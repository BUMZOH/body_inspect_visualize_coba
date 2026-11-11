"""Download inspection CSV files from KEYENCE PLC and register them in SQLite."""

import csv
import io
import json
import re
import sqlite3
import time
from datetime import datetime
from ftplib import FTP
from pathlib import Path


# ================================================
# Settings
# ================================================
BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"
DB_FILE = BASE_DIR.parent / "data" / "body_insp_measurement_data.db"
FTP_USER = "KV"
FTP_PASSWORD = ""
REMOTE_DIR = "/MMC/INSPECTION_DATA"
TABLE_NAME = "measurement_result"

INTERVAL_SEC = 300  # 次の実行までの待機秒数

CSV_COLUMNS = [
    "measured_at", "part_no", "proc_machine_no", "process_date",
    "measured_value", "judgment", "upper_limit", "lower_limit",
]
FILE_PATTERN = re.compile(r"^([a-z][a-z0-9_]*)_(\d{8})_(\d{2})\.csv$", re.I)


# ================================================
# Configuration
# ================================================
def get_machines():
    """config.jsonから全号機の設定を取得する。"""
    with CONFIG_FILE.open("r", encoding="utf-8-sig") as f:
        config = json.load(f)
    return config["machines"]


# ================================================
# CSV files
# ================================================
def get_csv_files(ftp):
    """
    PLC内のCSVファイル一覧を取得し、処理対象ファイルを返す。

    ファイル名から検査項目と日時を取得する。
    検査項目ごとに最新時間帯のCSVを除外し、残りのファイルを日時順に並べて返す。
    PLCがCSVを書き込み中の可能性があるため、最新時間帯は除外する。

    Args:
        ftp: 接続済みのFTPオブジェクト

    Returns:
        list: 処理対象CSVの一覧
              各要素は(日時, 検査項目, ファイル名, FTP上の名前)のタプル
              対象ファイルがない場合は空リスト
    """
    ftp.cwd(REMOTE_DIR)
    files = []
    for remote_name in ftp.nlst():
        name = remote_name.rsplit("/", 1)[-1]
        match = FILE_PATTERN.fullmatch(name)
        if match:
            item, day, hour = match.groups()
            try:
                file_hour = datetime.strptime(f"{day}{hour}", "%Y%m%d%H")
            except ValueError:
                continue
            files.append((file_hour, item, name, remote_name))

    if not files:
        return []

    # 検査項目ごとの最新時間帯を取得
    latest_by_item = {}

    for file_hour, item, name, remote_name in files:
        if item not in latest_by_item or file_hour > latest_by_item[item]:
            latest_by_item[item] = file_hour

    # 最新時間帯を表示
    for item, latest_hour in sorted(latest_by_item.items()):
        print(f"最新時間帯（処理対象外）: {item} / {latest_hour:%Y-%m-%d %H}:00")

    # 各検査項目の最新時間帯を除外
    target_files = []

    for entry in files:
        file_hour, item, name, remote_name = entry

        if file_hour < latest_by_item[item]:
            target_files.append(entry)

    return sorted(target_files)


def download_csv(ftp, remote_name):
    buffer = io.BytesIO()
    ftp.retrbinary(f"RETR {remote_name}", buffer.write)
    return buffer.getvalue()


def parse_csv(data, inspection_item, file_hour, machine_no):
    """
    CSVデータを解析し、SQLite登録用のデータ一覧を返す。

    CP932形式のCSVを読み込み、ヘッダー、列数、日時、数値を検証する。
    測定日時がファイル名の時間帯と一致することも確認する。
    正常なデータはSQLite登録用のタプルに変換する。

    Args:
        data: FTPから受信したCSVのバイナリデータ
        inspection_item: 検査項目名（例: thickness）
        file_hour: ファイル名から取得した日時（datetime型）
        machine_no: 検査装置の号機番号（例: 412）

    Returns:
        list: SQLite登録用のデータ一覧
              各要素はDBのカラム順に並べたタプル

    Raises:
        ValueError: CSVの形式やデータが不正な場合
    """
    text_data = io.StringIO(data.decode("cp932"), newline="")
    reader = csv.DictReader(text_data)

    # CSVヘッダー確認（列の順番は問わない）
    if (
        len(reader.fieldnames) != len(CSV_COLUMNS)
        or set(reader.fieldnames) != set(CSV_COLUMNS)
    ):
        raise ValueError(f"CSVヘッダーが仕様と異なります: {reader.fieldnames}")

    rows = []
    for line_no, row in enumerate(reader, start=2):
        # 列が多すぎる場合と少なすぎる場合の両方をチェック
        if None in row or any(row[col] is None for col in CSV_COLUMNS):
            raise ValueError(f"CSVの列数が不正です（{line_no}行目）")

        try:
            measured_at = datetime.strptime(
                row["measured_at"], "%Y-%m-%d %H:%M:%S"
            )
            process_date = datetime.strptime(
                row["process_date"], "%Y-%m-%d"
            ).strftime("%Y-%m-%d")
            if measured_at.replace(minute=0, second=0) != file_hour:
                raise ValueError("測定日時がファイル名の時間帯と一致しません")
            values = (
                machine_no,
                inspection_item,
                measured_at.strftime("%Y-%m-%d %H:%M:%S"),
                row["part_no"],
                int(row["proc_machine_no"]),
                process_date,
                float(row["measured_value"]),
                row["judgment"],
                float(row["upper_limit"]),
                float(row["lower_limit"]),
            )
        except (ValueError, TypeError) as e:
            raise ValueError(f"CSVデータ不正（{line_no}行目）: {e}") from e
        rows.append(values)

    if not rows:
        raise ValueError("CSVにデータ行がありません")
    return rows


# ================================================
# Database
# ================================================
def insert_rows(conn, rows):
    before = conn.total_changes
    conn.executemany(
        """
        INSERT OR IGNORE INTO measurement_result (
            insp_machine_no, inspection_item, measured_at, part_no,
            proc_machine_no, process_date, measured_value, judgment,
            upper_limit, lower_limit
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    return conn.total_changes - before


def process_machine(conn, machine_no, plc_ip):
    """指定した号機のCSVを取得し、DBへ登録する。"""
    with FTP(plc_ip, timeout=3) as ftp:
        ftp.login(FTP_USER, FTP_PASSWORD)
        print("FTP接続成功")
        files = get_csv_files(ftp)
        print(f"処理対象CSV: {len(files)}件")

        for file_hour, item, name, remote_name in files:
            try:
                data = download_csv(ftp, remote_name)
                rows = parse_csv(data, item, file_hour, machine_no)
                with conn:
                    inserted = insert_rows(conn, rows)
                print(f"{name}: 登録={inserted} / 重複={len(rows) - inserted}")
            except (OSError, ValueError, sqlite3.Error) as e:
                print(f"{name}: エラー（削除しません）: {e}")
                continue

            # DBへの登録が確定した後にPLC側CSVを削除
            try:
                ftp.delete(remote_name)
                print(f"  PLC側CSV削除: {name}")
            except Exception as e:
                print(f"  PLC側CSV削除失敗（DB登録済み）: {e}")


# ================================================
# Main
# ================================================
def main():
    if not DB_FILE.is_file():
        raise FileNotFoundError(f"DBファイルがありません: {DB_FILE}")

    machines = get_machines()
    print(f"DB : {DB_FILE}")

    with sqlite3.connect(DB_FILE) as conn:
        # テーブルの存在確認
        conn.execute(f"SELECT 1 FROM {TABLE_NAME} LIMIT 1")

        # config.jsonに登録された全号機を順番に処理
        for machine_no_str, settings in machines.items():
            machine_no = int(machine_no_str)
            plc_ip = settings["plc_ip_address"]

            print(f"\nPLC: {machine_no} / {plc_ip}")

            try:
                process_machine(conn, machine_no, plc_ip)
            except (OSError, ValueError, EOFError) as e:
                print(f"PLC {machine_no}: 処理エラー: {e}")

    print("処理終了")


if __name__ == "__main__":
    try:
        while True:
            try:
                main()
            except Exception as e:
                print(f"処理エラー: {e}")

            # 次の実行までカウントダウン
            for sec in range(INTERVAL_SEC, 0, -1):
                print(f"\rNext execution in {sec:3d} sec", end="", flush=True)
                time.sleep(1)

            print()

    except KeyboardInterrupt:
        print("\nStopped by user.")