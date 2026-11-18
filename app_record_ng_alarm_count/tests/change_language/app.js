// 現在の言語
let currentLanguage = "ja";

// 翻訳データ格納用
let labels = {};


// 翻訳JSON読み込み
async function loadLanguage(language) {

    const response =
        await fetch(`lang/${language}.json`);

    labels =
        await response.json();

    applyLanguage();
}


// 画面へ翻訳内容反映
function applyLanguage() {

    // ラベル切替
    document.getElementById(
        "label-name"
    ).textContent = labels.name;

    document.getElementById(
        "label-age"
    ).textContent = labels.age;

    document.getElementById(
        "label-birthplace"
    ).textContent = labels.birthplace;

    document.getElementById(
        "register-button"
    ).textContent = labels.register;


    // ドロップダウン切替
    const options =
        document.querySelectorAll(
            "#birthplace option"
        );

    options[0].textContent =
        labels.country_japan;

    options[1].textContent =
        labels.country_america;

    options[2].textContent =
        labels.country_china;

    options[3].textContent =
        labels.country_other;
}


// 日本語ボタン
document.getElementById(
    "btn-ja"
).addEventListener(

    "click",

    () => {

        currentLanguage = "ja";

        loadLanguage("ja");
    }
);


// 英語ボタン
document.getElementById(
    "btn-en"
).addEventListener(

    "click",

    () => {

        currentLanguage = "en";

        loadLanguage("en");
    }
);


// 登録ボタン
document.getElementById(
    "register-button"
).addEventListener(

    "click",

    () => {

        alert(labels.message);
    }
);


// 起動時読み込み
loadLanguage(currentLanguage);
