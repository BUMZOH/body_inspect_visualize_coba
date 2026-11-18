from pathlib import Path
from time import sleep
import webview

BASE_DIR = Path(__file__).resolve().parent
HTML_FILE = BASE_DIR / "web" / "index.html"


class AppApi:
    """JavaScriptから呼び出すPython API。"""

    def long_task(self)  -> str:
        """
        約30秒かかる長時間処理を実行する。

        実際のアプリでは、sleep()の部分を
        PLC通信、SQLite保存、集計処理などへ置き換える。
        """
        self._task1()
        self._task2()
        self._task3()
        self._task4()
        self._task5()

        return "すべての処理が完了しました"

    def _task1(self) -> None:
        """処理1を実行する"""
        sleep(1)
    
    def _task2(self) -> None:
        """処理1を実行する"""
        sleep(1)

    def _task3(self) -> None:
        """処理1を実行する"""
        sleep(1)

    def _task4(self) -> None:
        """処理1を実行する"""
        sleep(1)

    def _task5(self) -> None:
        """処理1を実行する"""
        sleep(1)

    def _task6(self) -> None:
        """処理1を実行する"""
        sleep(1)


def main() -> None:
    """pywebviewウィンドウを作成してアプリを起動する。"""
    api = AppApi()

    webview.create_window(
        title="固定メッセージ処理中ダイアログ",
        url=HTML_FILE.as_uri(),
        js_api=api,
        width=800,
        height=500,
    )

    webview.start(
        gui="edgechromium",
        debug=True
    )


if __name__ == "__main__":
    main()

