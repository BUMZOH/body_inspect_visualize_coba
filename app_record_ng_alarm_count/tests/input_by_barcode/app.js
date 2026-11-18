function getElement(id) {
    const element = document.getElementById(id);

    if (element === null) {
        throw new Error(`要素が見つかりません: ${id}`);
    }

    return element;
}

async function convertBarcode() {

    const barcodeInput = getElement("barcode_input");

    const barcodeText = barcodeInput.value;

    const result =
        await window.pywebview.api.convert_barcode(
            barcodeText
        );

    barcodeInput.value = result.part_name;

    // 次の読取に備えて全選択
    barcodeInput.select();
}

window.addEventListener("pywebviewready", () => {
    const barcodeInput = getElement("barcode_input");

    barcodeInput.focus();

    barcodeInput.addEventListener("keydown", async (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            await convertBarcode();
        }
    });
});
