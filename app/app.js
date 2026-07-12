async function getRecordWaitingMachines() {
    const result = await window.pywebview.api.get_record_waiting_machines();
    const machineNos = result.record_waiting_machines;
    const communicationErrorMachines = result.communication_error_machines;

    if (communicationErrorMachines.length >= 1) {
        console.warn("PLC通信に失敗した設備:", communicationErrorMachines);
    }


    if (machineNos.length === 0) {
        alert("記録待ち設備がありません。");
        return null;
    }

    if (machineNos.length >= 2) {
        alert(`記録待ち設備が複数あります。\n設備番号: ${machineNos.join(", ")}`);
        return null;
    }

    return machineNos[0];
}

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

async function updateDefaultValues(machineNo) {
    const defaultValues = await window.pywebview.api.get_default_values(machineNo);
    applyDefaultValues(defaultValues);
}

async function updateMonthlySerialNo() {
    // updateDefaultValues()でフォームへ値を設定した後に取得する。
    const inspectionMachineNo = document.getElementById("inspection_machine_no").value;
    const recordDate = document.getElementById("record_date").value;

    const monthlySerialNo = await window.pywebview.api.get_monthly_serial_no(
        inspectionMachineNo,
        recordDate
    );

    setInputValue("monthly_serial_no", monthlySerialNo);
}

async function updateTables() {
    const inspectionMachineNo = document.getElementById("inspection_machine_no").value;
    const inspectionStartTime = document.getElementById("inspection_start_time").value;
    const inspectionEndTime = document.getElementById("inspection_end_time").value;

    const tableData = await window.pywebview.api.get_table_data(
        inspectionMachineNo,
        inspectionStartTime,
        inspectionEndTime
    );

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
    const data = {};

    document
        .querySelectorAll(".db-item")
        .forEach(elem => {
            data[elem.id] = elem.textContent.trim();
        });

    return data;
}

async function registerData() {
    const inputData = getInputData();
    const tableData = getTableData();
    // 以下のスプレッド構文に注意(Pythonの辞書の結合に相当)
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
        try {
            // 記録待ち設備を検索する。
            const machineNo = await getRecordWaitingMachines();

            // 0台または複数台の場合は処理を中断する。
            if (machineNo === null) {
                return;
            }

            // 検索で確定した設備番号を使ってデフォルト値を取得する。
            await updateDefaultValues(machineNo);

            // フォームに入力された設備番号・記録日を使って採番する。
            await updateMonthlySerialNo();

            await updateTables();
        } catch (error) {
            console.error(error);
            alert(`データ更新に失敗しました。\n${error}`);
        }
    });

    // データ初期化ボタン
    const initializeButton = document.getElementById("initialize_button");
    initializeButton.addEventListener("click", () => {
        resetAll();
    });

    // データ登録ボタン
    const registerButton = document.getElementById("register_button");
    registerButton.addEventListener("click", () => {
        registerData();
    });

    // バックアップボタン
    const backupButton = document.getElementById("backup_button");
    backupButton.addEventListener("click", () => {
        alert("現在作成中です。");
    });

    // アラームコメント吸出しボタン
    const exportAlarmCommentButton = document.getElementById("export_alarm_comment_button");
    exportAlarmCommentButton.addEventListener("click", () => {
        alert("現在作成中です。");
    });

});

document.getElementById("appearance_check").addEventListener(
    "change",
    function () {
        if (this.value === "異常") {
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
            const value = document.getElementById("worker_name").value;
            document.getElementById("remaining_checker").value = value;
            document.getElementById("camera_5st_checker").value = value;
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

for (const id of STAFF_INPUT_IDS) {
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


