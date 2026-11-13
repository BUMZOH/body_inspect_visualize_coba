"""Windowsで同じPythonプログラムの二重起動を防止する最小サンプル。

仕組み:
    Pythonファイルと同じフォルダに app.lock を作成し、
    Windowsのファイルロック機能で先頭1バイトをロックする。
    別のプロセスが同じ場所をロックしようとすると失敗するため、
    すでに起動していることを検出できる。

確認方法:
    1. このプログラムを起動する。
    2. 別のターミナルから同じプログラムを起動する。
    3. 2つ目は「すでに起動しています。」と表示して終了する。
    4. 1つ目を Ctrl+C で停止すると、再び起動できる。

注意:
    app.lock が存在するだけでは二重起動とは判定しない。
    ロックはプログラム終了時にOSが解除するので、ファイルの削除は不要。
    このサンプルはWindows専用。同じロックファイルを使う実行同士が対象。
"""

import msvcrt  # Windowsのファイルロック機能を利用する標準ライブラリ
import time
from pathlib import Path


# カレントディレクトリに依存しないよう、Pythonファイル自身の場所を使う。
BASE_DIR = Path(__file__).resolve().parent
LOCK_FILE = BASE_DIR / "app.lock"

# a+b: 読み書き可能なバイナリモード。ファイルがなければ作成する。
# with文ではなく変数で保持し、プログラム実行中は開いたままにする。
with open(LOCK_FILE, "a+b") as lock_file:
    try:
        # a+bでは書き込み位置が末尾になるため、ロック対象を先頭に合わせる。
        lock_file.seek(0)

        # fileno(): OSがファイルを識別する番号（ファイル記述子）。
        # LK_NBLCK: ロック済みなら待たずにOSErrorを発生させる。
        # 1: 現在位置から1バイトをロックする。
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)

    except OSError as error:
        # Windowsのロック競合は通常 winerror=33（ロック違反）。
        # それ以外のエラーは隠さず、そのまま知らせる。
        if getattr(error, "winerror", None) != 33:
            raise
        print("すでに起動しています。")
        raise SystemExit(0)

    print("プログラムを起動しました。")

    try:
        # 動作確認用。実際のアプリではここに本来の処理を書く。
        while True:
            print("実行中...")
            time.sleep(3)
    except KeyboardInterrupt:
        print("Ctrl+Cで終了します。")

# with文を抜けるとファイルが閉じられ、ロックも解除される。
