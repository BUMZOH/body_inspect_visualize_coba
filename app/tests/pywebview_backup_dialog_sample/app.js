const BACKUP_WAIT_TIME_MS = 3000;
const DIALOG_CLOSE_DELAY_MS = 1000;

const openBackupDialogButton = document.getElementById("open-backup-dialog-button");
const backupDialogOverlay = document.getElementById("backup-dialog-overlay");
const backupDriveSelect = document.getElementById("backup-drive-select");
const executeBackupButton = document.getElementById("execute-backup-button");
const cancelBackupButton = document.getElementById("cancel-backup-button");
const backupMessage = document.getElementById("backup-message");

let isBackupRunning = false;

function openBackupDialog() {
    resetBackupDialog();
    backupDialogOverlay.classList.remove("hidden");
    backupDriveSelect.focus();
}

function closeBackupDialog() {
    if (isBackupRunning) {
        return;
    }
    backupDialogOverlay.classList.add("hidden");
}

function resetBackupDialog() {
    isBackupRunning = false;
    backupDriveSelect.disabled = false;
    executeBackupButton.disabled = false;
    cancelBackupButton.disabled = false;
    backupMessage.textContent = "";
}

function wait(milliseconds) {
    return new Promise((resolve) => {
        setTimeout(resolve, milliseconds)
    });
}

async function executeBackup() {
    if (isBackupRunning) {
        return;
    }

    isBackupRunning = true;
    backupDriveSelect.disabled = true;
    executeBackupButton.disabled = true;
    cancelBackupButton.disabled = true;
    backupMessage.textContent = "バックアップ中です....";

    await wait(BACKUP_WAIT_TIME_MS);

    backupMessage.textContent = "バックアップ完了";

    await wait(DIALOG_CLOSE_DELAY_MS);

    isBackupRunning = false;
    backupDialogOverlay.classList.add("hidden");
}


openBackupDialogButton.addEventListener("click", openBackupDialog);
executeBackupButton.addEventListener("click", executeBackup);
cancelBackupButton.addEventListener("click", closeBackupDialog);

backupDialogOverlay.addEventListener("click", (event) => {
    if (event.target === backupDialogOverlay) {
        closeBackupDialog();
    }
});

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        closeBackupDialog();
    }
});






