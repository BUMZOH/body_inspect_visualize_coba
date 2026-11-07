import webview


if __name__ == "__main__":

    # HTMLを表示
    webview.create_window(
        title="多言語対応サンプル",
        url="index.html",
        width=600,
        height=400,
    )

    webview.start()
