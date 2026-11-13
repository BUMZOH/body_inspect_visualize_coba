"""Windowsの名前付きMutexを使って、Pythonプログラムの二重起動を防ぐサンプル。

使い方:
    1. このファイルを実行する（1つ目は起動できる）。
    2. 別のコンソールから同じファイルを実行する。
    3. 2つ目には「すでに起動しています。」と表示され、終了する。
    4. 1つ目を Ctrl+C で停止すると、再び起動できる。

仕組み:
    Windowsが管理する「名前付きMutex」というオブジェクトを利用する。
    同じ名前のMutexがすでに存在すると、CreateMutexWは既存の
    オブジェクトのハンドルを返し、エラーコード183を設定する。

特徴:
    ・ロックファイルを作らないため、カレントディレクトリに依存しない。
    ・Pythonの標準ライブラリだけで動作する（Windows専用）。
    ・プロセスが終了すると、OSがハンドルを閉じる。
    ・Local\\ は同じWindowsログオンセッション内で名前を共有する。

注意:
    Mutexの名前はアプリごとに別のものにする。
    このサンプルは同じログオンセッション内での二重起動を防ぐ。
"""

import ctypes
import time
from ctypes import wintypes

# Windows APIで使用する定数
ERROR_ALREADY_EXISTS = 183  # 指定した名前のオブジェクトがすでに存在する
MUTEX_NAME = "Local\\MyPythonApp"

# Windowsのkernel32.dllに含まれる関数を利用する。
# use_last_error=True により、直後に ctypes.get_last_error() で
# Windows APIのエラーコードを読み取れる。
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

# CreateMutexWの引数と戻り値の型を指定する。
# 戻り値はHANDLE（ハンドル）。64bit Windowsでも正しく受け取るために重要。
kernel32.CreateMutexW.argtypes = (
    wintypes.LPVOID,  # セキュリティ属性。Noneなら既定値
    wintypes.BOOL,    # 最初からMutexを所有するか
    wintypes.LPCWSTR, # Mutexの名前（Unicode文字列）
)
kernel32.CreateMutexW.restype = wintypes.HANDLE

# 終了時にハンドルを閉じるための関数も設定する。
kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
kernel32.CloseHandle.restype = wintypes.BOOL

# 同じ名前のMutexがなければ新規作成し、あれば既存のものを開く。
# 第2引数 False は「Mutexの所有権を最初から取得しない」という意味。
# 二重起動の判定は所有権ではなく、同じ名前が存在するかで行う。
mutex = kernel32.CreateMutexW(None, False, MUTEX_NAME)

# 別のWindows API呼び出しで値が変わる前にエラーコードを取得する。
error_code = ctypes.get_last_error()

# ハンドルが取得できなかった場合は、本当のAPIエラーとして扱う。
if not mutex:
    raise ctypes.WinError(error_code)

try:
    # 183は「同じ名前のMutexがすでに存在する」という意味。
    if error_code == ERROR_ALREADY_EXISTS:
        print("すでに起動しています。")
    else:
        print("プログラムを起動しました。")

        # 動作確認のため3秒ごとにメッセージを表示し続ける。
        # Ctrl+Cで停止するとfinallyへ進み、ハンドルを閉じる。
        try:
            while True:
                print("実行中...")
                time.sleep(3)
        except KeyboardInterrupt:
            print("Ctrl+Cで終了します。")
finally:
    # 自分が取得したハンドルを必ず閉じる。
    # 最後のハンドルが閉じられると、名前付きMutexはOSにより破棄される。
    kernel32.CloseHandle(mutex)
