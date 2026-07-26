let currentLanguage = "japanese";


const BUTTON_LABELS = {
    backup: {
        japanese: "バックアップ",
        english: "Backup",
    },

    exportAlarmComment: {
        japanese: "ｱﾗｰﾑｺﾒﾝﾄ吸出し",
        english: "Export Alarm Comments",
    },

    exportData: {
        japanese: "データ出力",
        english: "Export Data",
    },

    initialize: {
        japanese: "データ初期化",
        english: "Initialize Data",
    },

    update: {
        japanese: "データ更新",
        english: "Update Data",
    },

    register: {
        japanese: "データ登録",
        english: "Register Data",
    },

    processing: {
        japanese: "処理中...",
        english: "Processing...",
    },
};

function getButtonLabel(buttonName) {
    const labels = BUTTON_LABELS[buttonName]

    if (!labels) {
        return buttonName;
    }

    return labels[currentLanguage] ?? labels.japanese
}

function applyButtonLabels() {
    const buttons = document.querySelectorAll("[data-button-name]");

    for (const button of buttons) {
        const buttonName = button.dataset.buttonName;

        button.textContent = getButtonLabel(buttonName);
    }
}

async function applyFormLabels() {
    const labels = await window.pywebview.api.get_form_labels(currentLanguage);

    const labelElements = document.querySelectorAll("label[data-column]");

    for (const labelElement of labelElements) {
        const column = labelElement.dataset.column;
        const labelText = labels[column];

        if (!labelText) {
            console.warn(`ラベル定義が見つかりません: ${column}`);
            continue;
        }

        labelElement.textContent = `${labelText}:`;
    }
}

async function changeLanguage(language) {
    if (language !== "japanese" && language !== "english") {
        console.error(`未対応の言語です: ${language}`);
        return;
    }

    currentLanguage = language;

    await applyFormLabels();
    applyButtonLabels();
}

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
    setInputValue("part_no", defaultValues.part_no);
    setInputValue("monthly_serial_no", defaultValues.monthly_serial_no);
    setInputValue("inspection_start_time", defaultValues.inspection_start_time);
    setInputValue("inspection_end_time", defaultValues.inspection_end_time);
    setInputValue("change_point_record", defaultValues.change_point_record);
}

async function updateDefaultValues(machineNo) {
    const defaultValues = await window.pywebview.api.get_default_values(machineNo);
    applyDefaultValues(defaultValues);
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

    const registerResult = await window.pywebview.api.register_data(data);
    if (!registerResult.ok) {
        alert(
            "登録に失敗しました。\n" + registerResult.message
        );
        return;
    }

    const shouldResetPlc = confirm(
        "PLCデバイスをリセットしますか？"
    );

    if (shouldResetPlc) {
        const resetResult = await window.pywebview.api.reset_plc_devices(
            data.inspection_machine_no
        );

        if (!resetResult.ok) {
            alert(
                "PLCデバイスのリセットに失敗しました。\n"
                + resetResult.message
            );
            return;
        }

        alert(resetResult.message);
    }

    resetAll();
}




// ボタンへのイベントハンドラ登録
window.addEventListener("pywebviewready", async () => {
    // 言語切り替えボタン
    const englishButton = document.getElementById("english_button");
    const japaneseButton = document.getElementById("japanese_button");
    englishButton.addEventListener("click", async () => {
        await changeLanguage("english");
    });
    japaneseButton.addEventListener("click", async () => {
        await changeLanguage("japanese");
    });

    // データ更新ボタン
    const updateButton = document.getElementById("update_button");
    updateButton.addEventListener("click", async () => {
        updateButton.disabled = true;
        updateButton.textContent = getButtonLabel("processing");

        try {
            // 記録待ち設備を検索する。
            const machineNo = await getRecordWaitingMachines();

            // 0台または複数台の場合は処理を中断する。
            if (machineNo === null) {
                return;
            }

            // 検索で確定した設備番号を使ってデフォルト値を取得する。
            await updateDefaultValues(machineNo);

            await updateTables();

        } catch (error) {
            console.error(error);
            alert(`データ更新に失敗しました。\n${error}`);

        } finally {
            updateButton.disabled = false;
            updateButton.textContent = getButtonLabel("update");
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
    backupButton.addEventListener("click", async () => {
        backupButton.disabled = true;
        backupButton.textContent = getButtonLabel("processing");

        try {
            const backupResult = await window.pywebview.api.backup_database();

            if (!backupResult.ok) {
                alert(
                    "バックアップに失敗しました。 \n"
                    + backupResult.message
                );
                return;
            }

            alert(backupResult.message);
        
        } catch (error) {
            console.error(error);
            alert(`バックアップに失敗しました。\n${error}`);

        } finally {
            backupButton.disabled = false;
            backupButton.textContent = getButtonLabel("backup");
        }
    });

    // アラームコメント吸出しボタン
    const exportAlarmCommentButton = document.getElementById("export_alarm_comment_button");
    exportAlarmCommentButton.addEventListener("click", async () => {
        exportAlarmCommentButton.disabled = true;
        exportAlarmCommentButton.textContent = getButtonLabel("processing");

        try {
            await window.pywebview.api.export_alarm_comments();
            alert("処理が完了しました。");
        
        } catch (error) {
            console.error(error);
            alert(`アラームコメントの吸出しに失敗しました。\n${error}`);

        } finally {
            exportAlarmCommentButton.disabled = false;
            exportAlarmCommentButton.textContent = getButtonLabel("exportAlarmComment");
        }
    });

    // データ出力ボタン
    const exportDataButton = document.getElementById("export_data_button");
    exportDataButton.addEventListener("click", async () => {
        const inputValue = prompt(
            "今日を含め、何日分のデータを出力しますか？",
            "1"
        );

        // キャンセルが押された場合
        if (inputValue === null) {
            return;
        }

        const daysText = inputValue.trim();

        // 入力値チェック
        // 正規表現に注意 (先頭から最後まで全部数字という意味)
        if (
            !/^\d+$/.test(daysText)
            || Number(daysText) < 1
        ) {
            alert("取得日数は1以上の整数で入力してください。");
            return;
        }

        exportDataButton.disabled = true;
        exportDataButton.textContent = getButtonLabel("processing");

        try {
            const exportResult = await window.pywebview.api.export_data(
                Number(daysText)
            );

            if (!exportResult.ok) {
                alert(
                    "CSV出力に失敗しました。\n"
                    + exportResult.message
                );
                return;
            }

            alert(exportResult.message);

        } catch (error) {
            console.error(error);

            alert(`CSV出力に失敗しました。\n${error}`);

        } finally {
            exportDataButton.disabled = false;
            exportDataButton.textContent = getButtonLabel("exportData");
        }
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


