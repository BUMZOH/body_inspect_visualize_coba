function setInputValue(id, value) {
    const input = document.getElementById(id);

    if (input === null) {
        console.error(`inputが見つかりません: ${id}`);
        return;
    }

    input.value = value;
}

function applyDefaultValues(defaultValues) {
    setInputValue("inspection_machine_no", defaultValues.inspection_machine_no);
    console.log(defaultValues.record_date);
    setInputValue("record_date", defaultValues.record_date);
    setInputValue("shift_name", defaultValues.shift_name);
    setInputValue("inspection_start_time", defaultValues.inspection_start_time);
    setInputValue("inspection_end_time", defaultValues.inspection_end_time);

}

async function updateDefaultValues() {
    const defaultValues = await window.pywebview.api.get_default_values();
    applyDefaultValues(defaultValues);
}

window.addEventListener("pywebviewready", () => {
    const updateButton = document.getElementById("update_button");

    updateButton.addEventListener("click", async () => {
        await updateDefaultValues();
    });
});
