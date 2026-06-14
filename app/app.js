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

    applyTableData(tableData);
}

function applyTableData(tableData) {
    // tableDataは<td>のidとそれに対する値が格納されている(辞書型)
    for (const [id, value] of Object.entries(tableData)) {

        const cell = document.getElementById(id);

        if (!cell) {
            console.error(`セルが見つかりません: ${id}`);
            continue;
        }

        cell.textContent = value;
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

function getInputData() {
    const data = {};

    document
        .querySelectorAll("input, select")
        .forEach((element) => {
            if (!element.id) {
                return;
            }

            data[element.id] = element.value;
        });
    
    return data;
}

function getTableData() {
    const data ={};

    document
        .querySelectorAll(".db-item")
        .forEach(elem => {
            data[elem.id] = elem.textContent.trim()
        });

    return data;
}

async function registerData() {
    const inputData = getInputData();
    const tableData = getTableData();
    // JSのスプレッド構文に注意
    const data = {
        ...inputData,
        ...tableData,
    };

    const result = await window.pywebview.api.register_data(data);
    if (result.ok) {
        alert(result.message);
    } else {
        alert("登録に失敗しました。\n" + result.message);
    }

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

    // データ登録ボタン
    const registerButton = document.getElementById("register_button");
    registerButton.addEventListener("click", () => {
        registerData()
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
    inputElement.value = result.staff_name;

    // 担当者に入力された場合は外観検査者にもコピー
    if (inputElement.id === "worker_name") {
        document.getElementById("appearance_checker").value = result.staff_name;
    }
}


