import subprocess  # 外部コマンド実行（nbconvert）
import sys
import time
import webbrowser
from datetime import datetime
from pathlib import Path

import papermill as pm


# ================================================
#   Settings
# ================================================
BASE_DIR = Path(__file__).resolve().parent

NOTEBOOK_PATH = BASE_DIR / "body_insp_measurement_trend.ipynb"
OUTPUT_NOTEBOOK_PATH = BASE_DIR / "output_measurement_trend.ipynb"

UPDATE_INTERVAL_SECONDS = 1 * 60
BROWSER_REFRESH_SECONDS = 60

DESKTOP_PATH = Path.home() / "Desktop"
OUTPUT_HTML_PATH = DESKTOP_PATH / "body_insp_measurement_trend.html"


# ================================================
#   Functions
# ================================================
def normalize_datetime(value):
    """
    入力された基準日時を YYYY-MM-DD HH:MM:SS に統一する。

    入力例:
        2026-11-14 17:15:00
        2026-11-14 17:15
        11-14 17:15
    """
    date_part, time_part = value.strip().split()

    parts = date_part.split("-")

    if len(parts) == 2:
        year = datetime.now().year
        month, day = map(int, parts)
    elif len(parts) == 3:
        year, month, day = map(int, parts)

        if year < 100:
            year += 2000
    else:
        raise ValueError("日付形式が正しくありません")

    time_parts = time_part.split(":")

    if len(time_parts) == 2:
        hour, minute = map(int, time_parts)
        second = 0
    elif len(time_parts) == 3:
        hour, minute, second = map(int, time_parts)
    else:
        raise ValueError("時刻形式が正しくありません")

    dt = datetime(year, month, day, hour, minute, second)

    return dt.strftime("%Y-%m-%d %H:%M:%S")


def create_html_report(std_datetime):
    print()
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] レポート更新開始")
    print(f"基準日時: {std_datetime}")

    try:
        print("Notebookを実行しています...")

        pm.execute_notebook(
            NOTEBOOK_PATH,
            OUTPUT_NOTEBOOK_PATH,
            cwd=str(BASE_DIR),
            parameters={
                "STD_DATETIME": std_datetime,
            },
        )

        print("HTMLを作成しています...")

        subprocess.run(
            [
                sys.executable,
                "-m",
                "jupyter",
                "nbconvert",
                "--to",
                "html",
                "--no-input",
                "--no-prompt",
                "--output",
                str(OUTPUT_HTML_PATH),
                OUTPUT_NOTEBOOK_PATH,
            ],
            check=True,
        )

        add_auto_refresh(OUTPUT_HTML_PATH)

        print(f"HTMLを更新しました: {OUTPUT_HTML_PATH}")

    finally:
        temp_path = Path(OUTPUT_NOTEBOOK_PATH)

        if temp_path.exists():
            temp_path.unlink()
            print("一時Notebookを削除しました。")


def add_auto_refresh(html_path):
    html = html_path.read_text(encoding="utf-8")

    refresh_tag = (
        f'<meta http-equiv="refresh" '
        f'content="{BROWSER_REFRESH_SECONDS}">'
    )

    if "<head>" in html:
        html = html.replace("<head>", f"<head>\n{refresh_tag}", 1)
    else:
        raise RuntimeError("HTMLの<head>タグが見つかりません。")

    html_path.write_text(html, encoding="utf-8")


# ================================================
#   Main
# ================================================
def main():
    print(f"実行環境 = {sys.executable}")
    std_datetime = normalize_datetime(input("基準日時: "))

    print()
    print("リアルタイムHTMLレポートを開始します。")
    print(f"更新間隔: {UPDATE_INTERVAL_SECONDS}秒")
    print(f"ブラウザ再読み込み間隔: {BROWSER_REFRESH_SECONDS}秒")
    print("終了する場合は Ctrl+C を押してください。")

    browser_opened = False

    try:
        while True:
            try:
                create_html_report(std_datetime)

                if not browser_opened:
                    webbrowser.open(OUTPUT_HTML_PATH.resolve().as_uri())
                    browser_opened = True

            except Exception as error:
                print()
                print(f"レポート更新に失敗しました: {error}")
                print("次回の更新時に再試行します。")

            print()
            for elapsed in range(1, UPDATE_INTERVAL_SECONDS + 1):
                print(
                    f"\r次回更新まで {elapsed} / {UPDATE_INTERVAL_SECONDS} 秒",
                    end="",
                    flush=True,
                )
                time.sleep(1)

            print()

    except KeyboardInterrupt:
        print()
        print("リアルタイムHTMLレポートを終了しました。")


if __name__ == "__main__":
    main()
