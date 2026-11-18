window.addEventListener("pywebviewready", () => {
    setupExecuteButton();
});

function setupExecuteButton() {
    const button = document.getElementById("execute-button");

    button.addEventListener("click", async () => {
        //処理中表示
        button.disabled = true;
        button.textContent = "処理中...";

        //Python処理
        await window.pywebview.api.execute();

        //元へ戻す
        button.disabled =false;
        button.textContent = "実行";

        //完了メッセージ
        alert("処理が完了しました");
    });
}






