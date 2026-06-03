from __future__ import annotations

from datetime import datetime
from pathlib import Path
import webview

BASE_DIR = Path(__file__).resolve().parent
INDEX_HTML = BASE_DIR / "index.html"


class AppAPI:
    def __init__(self) -> None:
        # 本来は設定ファイル、PLC、CSV、DBなどから取得する想定です。
        # まずはPythonから取得できていることを確認するため固定値にしています。
        self.inspection_machine_no = "BODY-INSPECT-01"

        # 検査開始時間もPythonから取得する指定なので、
        # アプリ起動時点の時刻を保持します。
        self.inspection_start_time = datetime.now()

    def get_default_values(self) -> dict[str, str]:
        """画面のデフォルト値を返す。"""
        now = datetime.now()

        if now.hour < 20:
            shift_name = "昼勤"
        else:
            shift_name = "夜勤"

        return {
            "inspection_machine_no": self.inspection_machine_no,
            "record_date": now.strftime("%Y-%m-%d"),
            "shift_name": shift_name,
            "inspection_start_time": self.inspection_start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "inspection_end_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        }


def main() -> None:
    api = AppAPI()

    webview.create_window(
        title="ボディ検査装置 稼働データ入力画面",
        url=str(INDEX_HTML),
        js_api=api,
        width=1600,
        height=900,
    )

    webview.start(
        gui="edgechromium",
        debug=True,
    )


if __name__ == "__main__":
    main()




