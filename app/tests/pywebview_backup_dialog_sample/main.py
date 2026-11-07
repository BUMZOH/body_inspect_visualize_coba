from pathlib import Path
import webview

BASE_DIR = Path(__file__).resolve().parent
HTML_FILE = BASE_DIR / "index.html"

if __name__ == '__main__':
    webview.create_window(
        title="バックアップダイアログ サンプル",
        url=HTML_FILE.as_uri(),
        width=900,
        height=650,
        resizable=True,
    )

    webview.start(gui="edgechromium")




