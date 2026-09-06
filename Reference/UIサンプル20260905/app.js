const dashboardData = {
    dayStaff: ["A", "B", "C", "D", "E", ""],
    nightStaff: ["F", "G", "H", "I", "J", ""],

    dayMinutes: 145,
    nightMinutes: 156,

    elapsedTime: "3:45",

    actualToday: 12535,
    targetToday: 13500,
    achievementToday: 83,

    actualTotal: 12535,
    targetTotal: 300000,
    achievementTotal: 5,

    machines: [
        { name: "MC557", count: 3457 },
        { name: "MC560", count: 3123 },
        { name: "MC577", count: 2544 },
        { name: "MC595", count: 957 },
        { name: "MC603", count: 2884 }
    ]
};


function formatNumber(value) {
    return Number(value).toLocaleString("ja-JP");
}


function renderStaff(targetId, staffList) {
    const root = document.getElementById(targetId);
    root.innerHTML = "";

    for (const staff of staffList) {
        const card = document.createElement("div");
        card.className = "staff-card";

        const photo = document.createElement("div");
        photo.className = "staff-photo";
        photo.textContent = staff || "—";

        const name = document.createElement("div");
        name.className = "staff-name";
        name.textContent = staff ? "NAME" : "";

        card.append(photo, name);
        root.appendChild(card);
    }
}


function renderMachines() {
    const root = document.getElementById("machineGrid");
    root.innerHTML = "";

    for (const machine of dashboardData.machines) {
        const card = document.createElement("div");
        card.className = "machine-card";

        const name = document.createElement("div");
        name.className = "machine-name";
        name.textContent = machine.name;

        const count = document.createElement("div");
        count.className = "machine-count";
        count.textContent = formatNumber(machine.count);

        card.append(name, count);
        root.appendChild(card);
    }
}


function animateShiftBoundary(dayPercent, nightPercent) {
    const shiftRatio = document.querySelector(".shift-ratio");
    const dayRatio = document.getElementById("dayRatio");
    const nightRatio = document.getElementById("nightRatio");

    // アニメーション中に境界が端へ寄りすぎないように制限
    const clamp = (value, min, max) =>
        Math.min(Math.max(value, min), max);

    // OS側で「アニメーションを減らす」が有効なら、すぐ最終値へ
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        dayRatio.style.width = `${dayPercent}%`;
        nightRatio.style.width = `${nightPercent}%`;
        return;
    }

    const duration = 3000;       // 約3秒揺らす
    const interval = 110;        // 境界変更間隔
    const maxSwing = 8;          // 最大 ±8%
    const startTime = performance.now();

    shiftRatio.classList.remove("is-settling");

    const timer = setInterval(() => {
        const elapsed = performance.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // 時間経過とともに揺れ幅を少しずつ小さくする
        const currentSwing = maxSwing * (1 - progress * 0.65);

        // ランダムな揺れ
        const randomOffset =
            (Math.random() * 2 - 1) * currentSwing;

        const animatedDayPercent =
            clamp(dayPercent + randomOffset, 15, 85);

        const animatedNightPercent =
            100 - animatedDayPercent;

        dayRatio.style.width = `${animatedDayPercent}%`;
        nightRatio.style.width = `${animatedNightPercent}%`;

        if (elapsed >= duration) {
            clearInterval(timer);

            // 最後だけ少しゆっくり滑らかに正しい位置へ固定
            shiftRatio.classList.add("is-settling");

            requestAnimationFrame(() => {
                dayRatio.style.width = `${dayPercent}%`;
                nightRatio.style.width = `${nightPercent}%`;
            });

            setTimeout(() => {
                shiftRatio.classList.remove("is-settling");
            }, 850);
        }
    }, interval);
}


function updateDashboard() {
    const totalShiftMinutes =
        dashboardData.dayMinutes +
        dashboardData.nightMinutes;

    const dayPercent =
        totalShiftMinutes === 0
            ? 50
            : dashboardData.dayMinutes / totalShiftMinutes * 100;

    const nightPercent = 100 - dayPercent;

    document.getElementById("dayMinutes").textContent =
        dashboardData.dayMinutes;

    document.getElementById("nightMinutes").textContent =
        dashboardData.nightMinutes;

    document.getElementById("dayPercent").textContent =
        Math.round(dayPercent);

    document.getElementById("nightPercent").textContent =
        Math.round(nightPercent);

    animateShiftBoundary(dayPercent, nightPercent);

    document.getElementById("elapsedTimeTop").textContent =
        dashboardData.elapsedTime;

    document.getElementById("elapsedTimeBottom").textContent =
        dashboardData.elapsedTime;

    document.getElementById("actualToday").textContent =
        formatNumber(dashboardData.actualToday);

    document.getElementById("targetToday").textContent =
        formatNumber(dashboardData.targetToday);

    document.getElementById("achievementToday").textContent =
        `${dashboardData.achievementToday}%`;

    document.getElementById("actualTotal").textContent =
        formatNumber(dashboardData.actualTotal);

    document.getElementById("targetTotal").textContent =
        formatNumber(dashboardData.targetTotal);

    document.getElementById("achievementTotal").textContent =
        `${dashboardData.achievementTotal}%`;

    // 125%をバー全体の100%幅として扱う
    const progressWidth =
        Math.min(dashboardData.achievementToday / 125 * 100, 100);

    document.getElementById("productionProgress").style.width =
        `${progressWidth}%`;

    const now = new Date();

    document.getElementById("lastUpdate").textContent =
        now.toLocaleString("ja-JP", {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit"
        });
}


function initialize() {
    renderStaff("dayStaff", dashboardData.dayStaff);
    renderStaff("nightStaff", dashboardData.nightStaff);
    renderMachines();
    updateDashboard();
}


document.addEventListener("DOMContentLoaded", initialize);
