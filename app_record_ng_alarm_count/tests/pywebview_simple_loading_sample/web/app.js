function getElement(id) {
    const element = document.getElementById(id);

    if (element === null) {
        throw new Error(
            `HTML要素が見つかりません: ${id}`
        );
    }

    return element;
}

function showLoading() {
    const overlay = getElement("loading-overlay");
    overlay.classList.remove("hidden");
}

function hideLoading() {
    const overlay = getElement("loading-overlay");
    overlay.classList.add("hidden");
}

async function runLongTask() {
    const startButton = getElement("start-button");
    const resultMessage = getElement("result-message");

    startButton.disabled = true;
    resultMessage.textContent = "処理を実行しています";

    showLoading();

    try {

        const result = await window.pywebview.api.long_task();
        resultMessage.textContent = result;

    } catch (error) {

        console.error(error);

        resultMessage.textContent = `処理中にエラーが発生しました: ${error}`;
        alert(`処理中にエラーが発生しました。\n${error}`);

    } finally {

        hideLoading();
        startButton.disabled = false;

    }
}

function setupEventListeners() {
    const startButton = getElement("start-button");

    startButton.addEventListener("click", runLongTask);
}

window.addEventListener("pywebviewready", setupEventListeners)









