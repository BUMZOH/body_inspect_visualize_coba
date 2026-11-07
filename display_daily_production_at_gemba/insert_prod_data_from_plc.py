"""5台のKEYENCE PLCから生産実績を収集し、既存SQLite DBへ登録する。

実行後、全PLCの収集・DB登録が終わるたびに180秒待機する。
停止は Ctrl+C。DBファイルおよびテーブルは自動作成しない。
"""

import json
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import TypeAlias

from common_lib_mw import kv_com


MachineConfig: TypeAlias = dict[str, str]
Machines: TypeAlias = dict[str, MachineConfig]
ProductionRow: TypeAlias = tuple[int, str, int, int]
ReceivedMachine: TypeAlias = tuple[str, list[ProductionRow]]

# ================================================
# Settings
# ================================================
BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"
DB_FILE = BASE_DIR.parent / "data" / "body_insp_production_data.db"
INTERVAL_SEC = 180
DATA_COUNT = 500

# 32ビット(D形式)を500個ずつ読み取る。各値は2ワードを使用する。
DEVICE_DATE_HOUR = "EM13000"
DEVICE_OPERATING_TIME = "EM14000"
DEVICE_PRODUCTION_NUM = "EM15000"

UPSERT_SQL = """
INSERT INTO production_result (
    machine_no,
    date_hour,
    operating_time_sec,
    production_num_1hour
)
VALUES (?, ?, ?, ?)
ON CONFLICT(machine_no, date_hour) DO UPDATE SET
    operating_time_sec = excluded.operating_time_sec,
    production_num_1hour = excluded.production_num_1hour
"""


# ================================================
# Common
# ================================================
def log(message: str) -> None:
    """日時を付けてコンソールへ出力する。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {message}", flush=True)


def load_config() -> Machines:
    """設定ファイルから通信対象の設備一覧を読み込む。"""
    with CONFIG_FILE.open(encoding="utf-8") as file:
        config = json.load(file)

    machines = config["machines"]
    if not machines:
        raise ValueError("config.json の machines が空です")

    for machine_no, machine_config in machines.items():
        int(machine_no)
        if not machine_config.get("plc_ip_address"):
            raise ValueError(f"設備{machine_no}: plc_ip_address が未設定です")

    return machines


# ================================================
# PLC communication
# ================================================
def receive_machine_data(
    machine_no: str, machine_config: MachineConfig
) -> tuple[str, list[ProductionRow], int]:
    """1台のPLCから500件×3項目を読み取り、DB登録用の行を返す。

    3領域のいずれかの読み取りに失敗した場合は例外を送出する。
    日時が0の行は登録対象から除外する。
    """
    ip_address = machine_config["plc_ip_address"]

    date_values = kv_com.read_devices_d(
        ip_address, DEVICE_DATE_HOUR, DATA_COUNT
    )
    operating_values = kv_com.read_devices_d(
        ip_address, DEVICE_OPERATING_TIME, DATA_COUNT
    )
    production_values = kv_com.read_devices_d(
        ip_address, DEVICE_PRODUCTION_NUM, DATA_COUNT
    )

    if not all(
        len(values) == DATA_COUNT
        for values in (date_values, operating_values, production_values)
    ):
        raise ValueError(f"設備{machine_no}: 受信件数が500件ではありません")

    rows = []           # DB登録用のデータ一覧
    skipped = 0         # 日時が0でスキップした件数
    seen_dates = set()  # 日時の重複チェック用

    for index, (seconds, operating_sec, production_num) in enumerate(
        zip(date_values, operating_values, production_values)
    ):
        if seconds == 0:
            skipped += 1
            continue

        # PLCのSEC命令: 2000-01-01 00:00:00からの経過秒数。
        date_text = kv_com.kv_seconds_to_datetime_str(seconds)
        date_time = datetime.strptime(date_text, "%Y-%m-%d %H:%M:%S")

        # DBのdate_hourは「YYYY-MM-DD HH:MM」。時間単位データを検証する。
        if date_time.minute != 0 or date_time.second != 0:
            raise ValueError(
                f"設備{machine_no} index={index}: "
                f"時間境界ではない日時 {date_text}"
            )
        date_hour = date_time.strftime("%Y-%m-%d %H:%M")

        if date_hour in seen_dates:
            raise ValueError(
                f"設備{machine_no}: 日時が重複しています: {date_hour}"
            )
        seen_dates.add(date_hour)

        # DBのCHECK制約に合わせ、書き込み前に異常を明示する。
        if not 0 <= operating_sec <= 3600:
            raise ValueError(
                f"設備{machine_no} {date_hour}: "
                f"稼働秒数が不正です: {operating_sec}"
            )
        if production_num < 0:
            raise ValueError(
                f"設備{machine_no} {date_hour}: "
                f"生産数が不正です: {production_num}"
            )

        rows.append(
            (int(machine_no), date_hour, operating_sec, production_num)
        )

    return machine_no, rows, skipped


def receive_all_machines(
    machines: Machines,
) -> tuple[list[ReceivedMachine], list[str]]:
    """PLC受信だけを並列実行する。失敗した設備は個別に記録する。"""
    received = []
    failed = []

    with ThreadPoolExecutor(max_workers=len(machines)) as executor:
        futures = {
            executor.submit(receive_machine_data, no, config): no
            for no, config in machines.items()
        }

        for future in as_completed(futures):
            machine_no = futures[future]
            try:
                _, rows, skipped = future.result()
                received.append((machine_no, rows))
                log(
                    f"PLC {machine_no}: 受信成功 "
                    f"登録対象={len(rows)}件 / 日時0で除外={skipped}件"
                )
            except Exception as error:
                failed.append(machine_no)
                log(f"PLC {machine_no}: 受信失敗: {error}")

    return received, failed


# ================================================
# Database
# ================================================
def insert_production_data(
    connection: sqlite3.Connection, machine_no: str, rows: list[ProductionRow]
) -> int:
    """1台分を1トランザクションでUPSERTする。"""
    if not rows:
        return 0

    # with connection は正常終了時commit、例外時rollback。
    with connection:
        connection.executemany(UPSERT_SQL, rows)

    return len(rows)


# ================================================
# Main
# ================================================
def run_once(machines: Machines) -> None:
    """1回の収集サイクル。受信は並列、DB登録は逐次実行する。"""
    log("収集開始")
    received, failed = receive_all_machines(machines)
    total_rows = 0

    # PLC受信完了後にDBへ接続
    conn = sqlite3.connect(DB_FILE)

    try:
        for machine_no, rows in received:
            try:
                count = insert_production_data(conn, machine_no, rows)
                total_rows += count
                log(f"PLC {machine_no}: DB登録成功 {count}件")
            except sqlite3.Error as error:
                failed.append(machine_no)
                log(f"PLC {machine_no}: DB登録失敗: {error}")
    finally:
        conn.close()

    log(
        f"収集終了: DB登録={total_rows}件 / "
        f"成功={len(machines) - len(failed)}台 / 失敗={len(failed)}台"
    )


def main() -> None:
    """起動時に設定・DBを確認し、停止されるまで定期収集する。"""
    machines = load_config()

    # DBファイルの存在確認
    if not DB_FILE.is_file():
        raise FileNotFoundError(f"DBファイルが存在しません: {DB_FILE}")

    # production_resultテーブルの存在確認
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.execute("SELECT 1 FROM production_result LIMIT 1")
    finally:
        conn.close()

    log(f"起動: PLC={len(machines)}台 / DB={DB_FILE}")

    while True:
        try:
            run_once(machines)
        except sqlite3.Error:
            # DB自体の致命的な障害はログに埋もれさせず停止する。
            raise
        except Exception as error:
            log(f"収集サイクルで予期しないエラー: {error}")

        log(f"次回収集まで{INTERVAL_SEC}秒待機")

        for _ in range(INTERVAL_SEC):
            print(".", end="", flush=True)
            time.sleep(1)

        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("Ctrl+C により終了しました")
    except Exception as error:
        log(f"プログラムを終了します: {error}")
        raise
