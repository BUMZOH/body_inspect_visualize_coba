from __future__ import annotations
from pathlib import Path
import webview
#　独自モジュール
from db import init_db
from app_api import AppAPI, load_staff_info


# CONSTANTS -----------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
INDEX_HTML = BASE_DIR / "index.html"


def main() -> None:
    load_staff_info()    # 従業員番号-氏名 対応表読み込み
    
    init_db()

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




