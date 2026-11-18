# VTのアラーム履歴をSDカードに出力させる
# KVのデバイスB0015を1秒間ONすると自動的に出力される
# 外部から使う関数はvt_output_csv

import time
import socket
from ftplib import FTP
from datetime import datetime

# --- CONSTANTS -------------------------------------------
PORT_NO = 8501


# --- FUNCTIONS -------------------------------------------
def com_with_plc(ip_add: str, cmd: str, timeout: float = 0.3) -> str:
    """KEYENCE KVシリーズ 上位リンク通信処理
    PLCへコマンドを送信し、CRLFまでレスポンスを受信する。

    Args:
        ip_add (str): PLCのIPアドレス
        cmd (str): PLCへ送信するコマンド
        timeout (float): 通信タイムアウト秒数

    Returns:
         response : str
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as skt:
        skt.settimeout(timeout)
        skt.connect((ip_add, PORT_NO))

        skt.sendall(cmd.encode("ascii"))

        data = b""
        while True:
            chunk = skt.recv(4096)

            if chunk == b"":
                # 「b""」が返ってきたときは相手が通信終了したとき
                raise ConnectionError("ソケット通信 途中終了")

            data += chunk

            if b"\r\n" in data:
                # 「b\r\n」はレスポンスの終端文字
                break

        response = data.decode("shift-jis").replace("\r\n", "")

        return response


def vt_output_csv(ip_add: str) -> bool:
    """ VTのアラーム履歴をSDカードへCSVファイルで出力
        (VT側の設定でB0015がOFF→ONで出力される)

    Args:
        ip_add (str): KV(PLC) IPアドレス

    Returns:
        bool: 通信成功/失敗
    """

    # 使用コマンド
    cmd_r = "RD B0015\r\n"      # 読み取りコマンド
    cmd_w1 = "WR B0015 1\r\n"   # 書き込みコマンド(ON)
    cmd_w0 = "WR B0015 0\r\n"   # 書き込みコマンド(OFF)

    print(f"--- {ip_add} : CSV output process start ---")

    # 1.初期値確認(B0015=OFFが前提)
    res = com_with_plc(ip_add, cmd_r)
    print(f"Step1 : response = {res}")


    # 2.強制リセット(B0015=ON時にOFFへ)
    if res=="1":
        res= com_with_plc(ip_add, cmd_w0)
        print(f"Step2 : response = {res}")

    # 3.B0015=ON (CSVファイルがSDカードに出力される)
    res = com_with_plc(ip_add, cmd_w1)
    print(f"Step3 : response = {res}")

    # 4.B0015=ON ドウェルタイム(これがないとVTが認識できない)
    time.sleep(1)

    # 5.終了処理(B0015=OFFに戻す)
    res = com_with_plc(ip_add, cmd_w0)
    print(f"Step5 : response = {res} <Process Conplete>")


def log(msg: str):
    """ログ出力用"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
    with open("log.txt", "a", encoding="utf-8") as f:  
	    f.write(f"{now} {msg}\n")


# テスト時コード
if __name__=='__main__':

    res = vt_output_csv("172.21.0.15")

