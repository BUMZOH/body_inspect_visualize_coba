"""
KEYENCE KV-5000からアラーム履歴を取得し、SQLiteへ保存する。

PLC側データ:
- アラーム発生日時: EM11000から500点（32bit D形式）
- アラームデバイス: EM12000から500点（32bit D形式）
- 配列の先頭が最新、末尾が最古

保存先:
- 呼び出し元から指定されたSQLiteファイル
- alarm_history テーブル
- alarm_comment テーブル
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

# original module(同一パッケージ内)
from . import kv_com


ALARM_HISTORY_COUNT = 500
ALARM_DATETIME_START_DEVICE = "EM11000"
ALARM_DEVICE_START_DEVICE = "EM12000"


def initialize_database(db_path: str | Path) -> None:
    """アラーム履歴用テーブルを作成する。既に存在する場合は何もしない。"""
    db_path = Path(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alarm_comment (
                machine_no INTEGER NOT NULL,
                alarm_device TEXT NOT NULL,
                alarm_comment TEXT NOT NULL DEFAULT '',
                UNIQUE(machine_no, alarm_device)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alarm_history (
                machine_no INTEGER NOT NULL,
                datetime TEXT NOT NULL,
                alarm_device TEXT NOT NULL,
                alarm_comment TEXT NOT NULL DEFAULT '',
                UNIQUE(machine_no, datetime, alarm_device)
            )
            """
        )


def alarm_device_value_to_name(device_value: int) -> str:
    """
    PLCに4桁整数で保存されたアラームデバイスをLR表記へ変換する。

    例:
        1015 -> LR1015
        2900 -> LR2900
    """
    if not 1000 <= device_value <= 2915:
        raise ValueError(f"アラームデバイス値が対象範囲外です: {device_value}")
    
    word_number = device_value // 100
    bit_number = device_value % 100

    if not 10 <= word_number <= 29:
        raise ValueError(f"LRワード番号が対象範囲外です: {word_number}")
    
    if not 0 <= bit_number <= 15:
        raise ValueError(f"LRビット番号が対象範囲外です: {bit_number}")

    return f"LR{word_number}{bit_number:02d}"


def get_alarm_comment(
    conn: sqlite3.Connection,
    machine_no: int,
    alarm_device: str
) -> str:
    """alarm_commentテーブルから設備別のアラームコメントを取得する。"""
    row = conn.execute(
        """
        SELECT alarm_comment
        FROM alarm_comment
        WHERE machine_no = ?
          AND alarm_device = ?
        """,
        (machine_no, alarm_device)
    ).fetchone()

    if row is None:
        return ""
    
    return row[0]


def read_alarm_history_from_plc(
        ip_add: str
) -> list[tuple[str, str]]:
    """
    PLCからアラーム履歴500件を読み出し、日時とデバイス名の組で返す。

    未使用領域と判断したデータは除外する。
    - 発生秒数が0
    - アラームデバイス値が0
    """
    datetime_values = kv_com.read_devices_d(
        ip_add,
        ALARM_DATETIME_START_DEVICE,
        ALARM_HISTORY_COUNT
    )

    device_values = kv_com.read_devices_d(
        ip_add,
        ALARM_DEVICE_START_DEVICE,
        ALARM_HISTORY_COUNT
    )

    if len(datetime_values) != ALARM_HISTORY_COUNT:
        raise RuntimeError(
            f"アラーム発生日時の読み出し件数が不正です: "
            f"{len(datetime_values)}"
        )
    
    if len(device_values) != ALARM_HISTORY_COUNT:
        raise RuntimeError(
            f"アラームデバイスの読み出し件数が不正です: "
            f"{len(device_values)}"
        )
    
    alarm_history: list[tuple[str, str]] = []

    for seconds, device_value in zip(datetime_values, device_values):
        if seconds == 0 or device_value == 0:
            continue

        alarm_datetime = kv_com.kv_seconds_to_datetime_str(seconds)
        alarm_device = alarm_device_value_to_name(device_value)

        alarm_history.append(
            (alarm_datetime, alarm_device)
        )

    return alarm_history
    

def save_alarm_history(
    machine_no: int,
    alarm_history: list[tuple[str, str]],
    db_path: str | Path
) -> int:
    """
    アラーム履歴をSQLiteへ保存する。

    同じ設備番号・発生日時・アラームデバイスの組合せは重複登録しない。

    Returns:
        int: 今回新しく追加した件数
    """
    db_path = Path(db_path)
    inserted_count = 0

    with sqlite3.connect(db_path) as conn:
        for alarm_datetime, alarm_device in alarm_history:
            alarm_comment = get_alarm_comment(
                conn,
                machine_no,
                alarm_device
            )

            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO alarm_history (
                    machine_no,
                    datetime,
                    alarm_device,
                    alarm_comment
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    machine_no,
                    alarm_datetime,
                    alarm_device,
                    alarm_comment 
                )
            )

            inserted_count += cursor.rowcount   # INSERT時=1 / IGNORE時=0

    return inserted_count


def collect_alarm_history(
        ip_add: str,
        machine_no: int,
        db_path: str | Path
) -> dict[str, int]:
    """
    PLCからアラーム履歴を取得し、SQLiteへ保存する。

    Returns:
        dict[str, int]:
            read_count: PLCから取得した有効履歴数
            inserted_count: DBへ新規追加した件数
            duplicate_count: 既に登録済みだった件数
    """
    if machine_no <= 0:
        raise ValueError(
            f"設備番号が不正です: {machine_no}"
        )

    initialize_database(db_path)

    alarm_history = read_alarm_history_from_plc(ip_add)

    inserted_count = save_alarm_history(
        machine_no=machine_no,
        alarm_history=alarm_history,
        db_path=db_path
    )

    read_count = len(alarm_history)

    return {
        "read_count": read_count,
        "inserted_count": inserted_count,
        "duplicate_count": read_count - inserted_count
    }


def update_alarm_comments(
    ip_add: str,
    machine_no: int,
    db_path: str | Path
) -> int:
    """
    PLCからLR1000～LR2915のコメントを取得し、
    alarm_commentテーブルへ登録または更新する。

    Returns:
        int: 登録・更新対象件数
    """
    if machine_no <= 0:
        raise ValueError(
            f"設備番号が不正です: {machine_no}"
        )

    initialize_database(db_path)

    alarm_info = kv_com.dl_alarm_comment(ip_add)

    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO alarm_comment (
                machine_no,
                alarm_device,
                alarm_comment
            )
            VALUES (?, ?, ?)
            ON CONFLICT(machine_no, alarm_device)
            DO UPDATE SET
                alarm_comment = excluded.alarm_comment
            """,
            [
                (machine_no, alarm_device, alarm_comment)
                for alarm_device, alarm_comment in alarm_info
            ]
        )

    return len(alarm_info)


def get_alarm_history(
    machine_no: int,
    start_datetime: str,
    end_datetime: str,
    db_path: str | Path
) -> list[tuple[str, str, str]]:
    """
    指定設備・指定期間のアラーム履歴を取得する。

    日時の新しい順に並べて返す。
    開始日時と終了日時は取得範囲に含む。

    Args:
        machine_no: 設備番号
        start_datetime: 取得開始日時（YYYY-MM-DD HH:MM:SS）
        end_datetime: 取得終了日時（YYYY-MM-DD HH:MM:SS）
        db_path: SQLiteファイルのパス

    Returns:
        list[tuple[str, str, str]]:
            [(datetime, alarm_device, alarm_comment), ...]
    """
    if machine_no <= 0:
        raise ValueError(
            f"設備番号が不正です: {machine_no}"
        )
    
    if start_datetime > end_datetime:
        raise ValueError(
            "取得開始日時が取得終了日時より後になっています: "
            f"{start_datetime} > {end_datetime}"
        )
    
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(
            f"データベースファイルが存在しません: {db_path}"
        )

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT
                datetime,
                alarm_device,
                alarm_comment
            FROM alarm_history
            WHERE machine_no = ?
              AND datetime BETWEEN ? AND ?
            ORDER BY datetime DESC
            """,
            (
                machine_no,
                start_datetime,
                end_datetime
            )
        ).fetchall()

    return rows


def count_alarm_keyword(
    alarm_history: list[tuple[str, str, str]],
    keyword: str
) -> int:
    """
    アラーム履歴のalarm_commentに指定キーワードが含まれる件数を返す。

    Args:
        alarm_history:
            get_alarm_history()で取得したアラーム履歴
        keyword:
            検索する文字列

    Returns:
        int: キーワードを含むアラームコメントの件数
    """
    if not keyword:
        raise ValueError("検索キーワードが空です")
    
    # 以下ジェネレータ式に注意
    return sum(
        keyword in alarm_comment
        for _, _, alarm_comment in alarm_history
    )


def count_alarm_keywords(
        alarm_history: list[tuple[str, str, str]],
        keywords: list[str]
) -> dict[str, int]:
    """
    アラーム履歴のalarm_commentに各キーワードが含まれる件数を返す。

    Args:
        alarm_history:
            get_alarm_history()で取得したアラーム履歴
        keywords:
            検索するキーワードのリスト

    Returns:
        dict[str, int]:
            キーワードをキー、該当件数を値とする辞書
            例: {"1ST": 10, "2ST": 5}
    """
    if not keywords:
        raise ValueError("検索キーワードのリストが空です")
    
    if any(not keyword for keyword in keywords):
        raise ValueError("検索キーワードに空文字が含まれています")

    # 注意: 辞書内包表記 + ジェネレータ式 + sum()による集計
    return {
        keyword: sum(
            keyword in alarm_comment
            for _, _, alarm_comment in alarm_history
        )
        for keyword in keywords
    }


if __name__ == "__main__":
    # 単体テスト用コード
    # モジュール実行すること(コマンド例: python -m app.common_lib_mw.kv_alarm_history)

    UPDATE_COMMENTS = True
    COLLECT_HISTORY = True
    CHECK_HISTORY = True

    # 以下環境に合わせて変更すること
    ip_add = "192.168.8.1"
    machine_no = 555
    db_file = "data/body_inspection_machine.db"

    if UPDATE_COMMENTS:
        comment_count = update_alarm_comments(
            ip_add,
            machine_no,
            db_file
        )
        print(f"アラームコメント登録件数: {comment_count}")

    if COLLECT_HISTORY:
        collect_result = collect_alarm_history(
            ip_add,
            machine_no,
            db_file
        )
        print(collect_result)

    if CHECK_HISTORY:
        rows = get_alarm_history(
            machine_no=machine_no,
            start_datetime="2026-01-01 00:00:00",
            end_datetime="2026-12-31 23:59:59",
            db_path=db_file
        )

        alarm_1st_count = count_alarm_keyword(
            rows,
            "1ST"
        )
        print(f"1STアラーム件数: {alarm_1st_count}")

        keywords = ["1ST", "2ST", "3ST"]
        alarm_counts = count_alarm_keywords(
            rows,
            keywords
        )
        print(alarm_counts)


"""
---- 更新履歴 ------

2026/7/11
初回リリース

"""