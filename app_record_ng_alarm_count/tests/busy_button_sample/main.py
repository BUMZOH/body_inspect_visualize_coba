from pathlib import Path
import time

import webview


HTML_FILE = Path(__file__).parent / "index.html"

class Api:
    def execute(seld):
        """
        ダミー処理（3秒）    
        """
        time.sleep(3)
        return True
    

if __name__ == "__main__":
    api = Api()

    webview.create_window(
        title="処理中サンプル",
        url=HTML_FILE.as_uri(),
        js_api=api,
        width=500,
        height=300,
        resizable=True,
    )

    webview.start()