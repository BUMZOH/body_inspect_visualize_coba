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
    setInputValue("change_point_record", defaultValues.change_point_record);
}

async function updateDefaultValues() {
    const defaultValues = await window.pywebview.api.get_default_values();
    applyDefaultValues(defaultValues);
}

async function updateTables() {
    const tableData = await window.pywebview.api.get_table_data();

    updateCountSummary(tableData.count_summary);
    updateNgCountDetail(tableData.ng_count_detail);
    updateAlarmInfo(tableData.alarm_info);
}

function updateCountSummary(data) {
    const table = document.getElementById("count_summary");
    table.rows[1].cells[0].textContent = data.ok_count;
    table.rows[1].cells[1].textContent = data.ng_count;
}

function updateNgCountDetail(data) {
    const table = document.getElementById("ng_count_detail");
    const firstCheckValues = data.first_check;
    const reCheckValues = data.re_check;

    for (let i=0; i<firstCheckValues.length; i++) {
        table.rows[1].cells[i+1].textContent = firstCheckValues[i];
    }
    
    for (let i=0; i<reCheckValues.length; i++) {
        table.rows[2].cells[i+1].textContent = reCheckValues[i];
    }
}

function updateAlarmInfo(data) {
    const table = document.getElementById("alarm_info");

    for (let i=0; i<data.length; i++) {
        table.rows[1].cells[i].textContent = data[i];
    }
}

function resetAll() {
    document.querySelectorAll("input, select, textarea").forEach(el => {
        el.value = "";
    });

    document.querySelectorAll("table td").forEach(td => {
        td.textContent = "0";
    });
}


// ボタンへのイベントハンドラ登録
window.addEventListener("pywebviewready", () => {
    // データ更新ボタン
    const updateButton = document.getElementById("update_button");
    updateButton.addEventListener("click", async () => {
        await updateDefaultValues();
        await updateTables();
    });

    // データ初期化ボタン
    const initializeButton = document.getElementById("initialize_button");
    initializeButton.addEventListener("click", () => {
        resetAll();
    });
});

document.getElementById("appearance_check").addEventListener(
    "change",
    function () {
        if (this.value === "異常"){
            const result = confirm("製品異常の打ち上げは実施しましたか？");
            
            if (!result) {
                this.value = "";    // キャンセル時は未選択に戻す
            }
        }
    }
);

document.getElementById("setup_check").addEventListener(
    "change",
    function () {
        if (this.value === "あり") {
            const value = document.getElementById("worker_name").value
            document.getElementById("remaining_checker").value = value
            document.getElementById("camera_5st_checker").value = value
        }
    }
);


// バーコードによる作業者名入力
const STAFF_INPUT_IDS = [ 
    "worker_name", 
    "remaining_checker", 
    "appearance_checker",
    "camera_5st_checker", 
    "remaining_double_checker", 
];

for (const id of STAFF_INPUT_IDS){
    document.getElementById(id).addEventListener(
        "keydown",
        async (event) => {
            if (event.key === "Enter") {
                event.preventDefault();
                await convertBarcode(event.target);
            }
        }
    )
}

async function convertBarcode(inputElement) {
    const barcodeText = inputElement.value;

    const result = await window.pywebview.api.convert_barcode(barcodeText);
    console.log(result);
    inputElement.value = result.staff_name;
}


