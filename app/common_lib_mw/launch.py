"""
subprocessで外部プログラムを起動させるプログラム
"""
import subprocess
import sys
from pathlib import Path


def run_outer_app(app_path: Path):
    """外部プログラム(app_path)を subprocess で実行"""
    # フォルダまで含めたプログラム名(main.pyだけだとわからないため)
    pg_name = app_path.parent.name + "/" + app_path.name
    print(f"----- 外部プログラム({pg_name}) : 開始 -----")

    process = subprocess.Popen(
        [sys.executable, str(app_path)],
        cwd=app_path.parent,
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )

    # 外部プログラムの終了を待つ
    return_code = process.wait()

    if return_code == 0:
        print("外部プログラムは正常終了しました")
    else:
        print(f"外部プログラムは異常終了しました: {return_code}")




if __name__ == "__main__":

    base_dir = Path(__file__).resolve().parent
    app_path = base_dir / "main.py"

    run_outer_app(app_path)


"""
----- 更新履歴 ------------------------------------------------


2026.5.7
呼び出しプログラムを別コンソールで実施した。
コンソール種類による文字化け問題を解決するため。

2026.5.7
pg_name部分を追加 (ファイル名だけだとmain.pyとなり意味不明なため)

"""