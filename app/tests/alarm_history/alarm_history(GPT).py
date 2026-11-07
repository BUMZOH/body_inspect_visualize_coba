"""
KEYENCE KV-5000からアラーム履歴を取得し、SQLiteへ保存する。

PLC側データ:
- アラーム発生日時: EM11000から500点（32bit D形式）
- アラームデバイス: EM12000から500点（32bit D形式）
- 配列の先頭が最新、末尾が最古

保存先:
- body_inspection_machine.db
- alarm_history テーブル
- alarm_comment テーブル
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import kv_com


DB_FILE = Path(__file__).resolve().parent / "body_inspection_machine.db"

ALARM_HISTORY_COUNT = 500
ALARM_DATETIME_START_DEVICE = "EM11000"
ALARM_DEVICE_START_DEVICE = "EM12000"


def initialize_database(db_path: str | Path = DB_FILE) -> None:
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
        1015 -> LR10.15
        2900 -> LR29.00
    """
    if not 1000 <= device_value <= 2915:
        raise ValueError(
            f"アラームデバイス値が対象範囲外です: {device_value}"
        )

    word_number = device_value // 100
    bit_number = device_value % 100

    if not 10 <= word_number <= 29:
        raise ValueError(
            f"LRワード番号が対象範囲外です: {word_number}"
        )

    if not 0 <= bit_number <= 15:
        raise ValueError(
            f"LRビット番号が対象範囲外です: {bit_number}"
        )

    return f"LR{word_number}.{bit_number:02d}"


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
        (machine_no, alarm_device),
    ).fetchone()

    if row is None:
        return ""

    return str(row[0])


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
        ALARM_HISTORY_COUNT,
    )

    device_values = kv_com.read_devices_d(
        ip_add,
        ALARM_DEVICE_START_DEVICE,
        ALARM_HISTORY_COUNT,
    )

    if len(datetime_values) != ALARM_HISTORY_COUNT:
        raise RuntimeError(
            "アラーム発生日時の読出し件数が不正です: "
            f"{len(datetime_values)}"
        )

    if len(device_values) != ALARM_HISTORY_COUNT:
        raise RuntimeError(
            "アラームデバイスの読出し件数が不正です: "
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
        db_path: str | Path = DB_FILE
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
                alarm_device,
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
                    alarm_comment,
                ),
            )

            inserted_count += cursor.rowcount

    return inserted_count


def collect_alarm_history(
        ip_add: str,
        machine_no: int,
        db_path: str | Path = DB_FILE
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
        db_path=db_path,
    )

    read_count = len(alarm_history)

    return {
        "read_count": read_count,
        "inserted_count": inserted_count,
        "duplicate_count": read_count - inserted_count,
    }


def update_alarm_comments(
        ip_add: str,
        machine_no: int,
        db_path: str | Path = DB_FILE
) -> int:
    """
    PLCからLR10.00～LR29.15のコメントを取得し、
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
            ],
        )

        # コメントマスタ更新後、既存履歴側のコメントも同期する。
        conn.execute(
            """
            UPDATE alarm_history
            SET alarm_comment = COALESCE(
                (
                    SELECT ac.alarm_comment
                    FROM alarm_comment AS ac
                    WHERE ac.machine_no = alarm_history.machine_no
                      AND ac.alarm_device = alarm_history.alarm_device
                ),
                ''
            )
            WHERE machine_no = ?
            """,
            (machine_no,),
        )

    return len(alarm_info)


def parse_arguments() -> argparse.Namespace:
    """コマンドライン引数を解析する。"""
    parser = argparse.ArgumentParser(
        description="PLCからアラーム履歴を取得してSQLiteへ保存します。"
    )

    parser.add_argument(
        "ip_address",
        help="PLCのIPアドレス",
    )

    parser.add_argument(
        "machine_no",
        type=int,
        help="設備番号",
    )

    parser.add_argument(
        "--db",
        default=str(DB_FILE),
        help=(
            "SQLiteファイルのパス "
            f"(既定値: {DB_FILE})"
        ),
    )

    parser.add_argument(
        "--update-comments",
        action="store_true",
        help="アラーム履歴取得前にPLCコメントを更新する",
    )

    return parser.parse_args()


def main() -> None:
    """コマンドライン実行時の処理。"""
    args = parse_arguments()

    if args.update_comments:
        comment_count = update_alarm_comments(
            ip_add=args.ip_address,
            machine_no=args.machine_no,
            db_path=args.db,
        )
        print(
            f"アラームコメントを{comment_count}件更新しました。"
        )

    result = collect_alarm_history(
        ip_add=args.ip_address,
        machine_no=args.machine_no,
        db_path=args.db,
    )

    print(
        "アラーム履歴収集完了: "
        f"有効履歴={result['read_count']}件, "
        f"新規登録={result['inserted_count']}件, "
        f"登録済み={result['duplicate_count']}件"
    )


if __name__ == "__main__":
    main()
