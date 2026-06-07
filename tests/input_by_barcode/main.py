from __future__ import annotations

from pathlib import Path
import webview


BASE_DIR = Path(__file__).resolve().parent
INDEX_HTML = BASE_DIR / "index.html"

# 品番対応表
PART_MAP = {
    "299526-3310": "品番A",
    "299526-3330": "品番B",
    "299526-3340": "品番C",
}


class AppAPI:

    def convert_barcode(self, barcode_text: str) -> dict[str, str]:
        """バーコード文字列を品番名に変換する。"""
        barcode_text = barcode_text.strip()
        print(barcode_text)
        part_name = PART_MAP.get(
            barcode_text,
            "不明",
        )

        return {
            "barcode_text": barcode_text,
            "part_name": part_name,
        }


def main() -> None:
    api = AppAPI()

    webview.create_window(
        title="バーコード品番変換サンプル",
        url=INDEX_HTML.as_uri(),
        js_api=api,
        width=700,
        height=450,
    )

    webview.start(
        # gui="edgechromium",
        debug=False,
    )


if __name__ == "__main__":
    main()

