# VTのSDカード内CSVファイルからアラーム履歴を取得し、
# SQLiteへデータ登録
# その後CSVファイル削除


from ftplib import FTP
import pandas as pd
import io
import sqlite3
from pathlib import Path


# --- CONSTANTS -------------------------------------------
USER = "VT"
PASSWORD = ""
TARGET_FOLDER = "/VTALM/ID0/00000_00999"

# DB_PATH = "./machine_operation.db"    # テスト時
DB_PATH = r"\\192.168.2.1\共有ファイル\M-光和共有ファイル\P_ProductControl\operation_data\machine_operation.db"
DB_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS alarm_history (
    MachineNo INTEGER NOT NULL,
    DateTime  TEXT NOT NULL,
    AlarmNo   INTEGER NOT NULL,
    Message   TEXT,
    PRIMARY KEY (MachineNo, DateTime, AlarmNo)
    )
"""


# --- FUNCTIONS -------------------------------------------
def ftp_init_proc(ftp: FTP) -> None:
    """FTP通信の初期プロセス
       (設定→ログイン→フォルダ移動)

    Args:
        ftp (FTP): FTPインスタンス
    """
    ftp.encoding = "shift-jis"
    ftp.set_pasv(True)  # デフォルトでパッシブだが、念のため

    # ログイン
    msg = ftp.login(USER, PASSWORD)
    print(f"{ftp.host}: FTP login : {msg}")

    # 対象フォルダへ移動
    ftp.cwd(TARGET_FOLDER)


def get_csv_file_list(ftp: FTP) -> list[str]:
    """FTPサーバ上のCSVファイル一覧を取得する

    Args:
        ftp (FTP): TPインスタンス

    Returns:
        list[str]: CSVファイルリスト
    """
    file_list = ftp.nlst(".")
    # CSVファイルのみ抽出
    csv_files = [f for f in file_list if f.lower().endswith(".csv")]
    print(f"CSVファイル数：{len(csv_files)}")   # ForDebug

    return csv_files


def read_csv_as_dataframe(ftp: FTP, file_name: str) -> pd.DataFrame:
    """FTPサーバ上のCSVをローカル保存せずDataFrameとして読み込む

    Args:
        ftp (FTP): FTPインスタンス
        file_name (str): CSVファイル名(VT SDカード内)

    Returns:
        pd.DataFrame: pandas DataFrame
    """
    print(f"Reading file({file_name})")
    data = bytearray()

    ftp.retrbinary(f"RETR {file_name}", data.extend)

    df = pd.read_csv(
        io.BytesIO(data),
        encoding = "shift-jis",
        skiprows = 3
    )

    return df


def delete_csv(ftp: FTP, file_name):
    """FTPサーバ(VT)状のファイルを削除

    Args:
        ftp (FTP): FTPインスタンス
        file_name (_type_): _description_
    """
    ftp.delete(file_name)
    print(f"file({file_name}) is deleted")


def import_df_into_sql(mc_no: int, df: pd.DataFrame):
    """DataFrameを成形し、SQLiteファイルに登録

    Args:
        mc_no (int): _description_
        df (pd.DataFrame): _description_
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(DB_CREATE_SQL)  # DB作成(すでにある場合はスキップ)

    df_ini = df.copy()  # 一応ローカルで受け取る
    # DateTimeカラム追加
    df_ini["DateTime"] = pd.to_datetime(
        df["DATE"] + " " + df["TIME"],
        format="%Y/%m/%d %H:%M:%S"
    )
    print(df_ini.head())    # ForDebug

    # DB登録用に整形(DateTime->文字列に注意)
    df_db = pd.DataFrame({
        "MachineNo": mc_no,
        "DateTime": df_ini["DateTime"].dt.strftime("%Y-%m-%d %H:%M:%S"),
        "AlarmNo": df_ini["ALARM No"],
        "Message": df_ini["MESSAGE"],
    })

    cur.executemany("""
    INSERT OR IGNORE INTO alarm_history (
        MachineNo,
        DateTime,
        AlarmNo,
        Message
    )
    VALUES (?, ?, ?, ?)
    """, df_db.values.tolist())
    conn.commit()

    # インポート結果
    inserted = cur.rowcount
    ignored = len(df_db) - inserted
    print(f"CSV行数: {len(df_db)}")
    print(f"新規登録: {inserted}")
    print(f"重複無視: {ignored}")


# --- MAIN PROCESS -----
def vt_csv_to_sql(mc_no: int, vt_ip: str):
    with FTP(vt_ip, timeout=1) as ftp:
        # 開始時処理(ログイン->フォルダ移動)
        ftp_init_proc(ftp)

        # VTからCSVファイルリスト取得
        csv_files = get_csv_file_list(ftp)
        if not csv_files:
            print("--- No CSV Files ---")
            return
        
        for file in csv_files:
            df = read_csv_as_dataframe(ftp, file)
            # print(df.head())

            # SQLite登録処理
            import_df_into_sql(mc_no, df)

            # CSVファイル削除(1->0で無効化)
            if 1:
                delete_csv(ftp, file)


if __name__=='__main__':
    mc_no = 55
    vt_ip = "172.21.0.16"
    vt_csv_to_sql(mc_no, vt_ip)