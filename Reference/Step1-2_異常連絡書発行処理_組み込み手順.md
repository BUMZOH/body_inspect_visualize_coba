# Step1-2 異常連絡書発行処理：既存アプリへの組み込み手順

## 1. 概要

「データ登録」ボタンの既存処理が終了した後、再検査不良数（`_ngcount2`）が100個以上の項目があれば「異常連絡書に転記しますか？」と確認する。「はい」の場合に限り、既存の `issue_abnormality_report.py` でExcel帳票を作成する。

本資料は2026-11-18時点の添付ソースに基づく。行番号は目安とし、関数名・前後のコードを目印に編集する。今回は実機確認前の変更手順の整理である。

| ファイル | 変更 | 位置 |
|---|---|---|
| `app_api.py` | importを1行追加 | 冒頭のimport群（1～11行付近） |
| `app_api.py` | APIメソッドを追加 | `AppAPI` クラスの `register_data()` の直後（715行付近） |
| `app.js` | 判定関数を追加 | `registerData()` の直前（142行付近） |
| `app.js` | 確認・発行処理を追加 | `registerData()` の末尾（179～182行付近） |

`main.py`、`db.py`、`index.html`、`issue_abnormality_report.py` のコード変更は原則不要。

## 2. `app_api.py` の修正

### 2-1. importを追加

ファイル冒頭、他の独自モジュールのimport付近に追加する。

```python
from issue_abnormality_report import issue_abnormality_report
```

### 2-2. `AppAPI` クラス内にメソッドを追加

`def register_data(self, data: dict):` の処理が終了した後、`def get_record_waiting_machines(...)` の前に以下を追加する。**クラス内のメソッドなので、先頭は4スペースのインデント**にする。

```python
    def create_abnormality_report(self, data: dict) -> dict:
        """異常連絡書をExcelで作成する。"""
        try:
            output_file = issue_abnormality_report(data)

            return {
                "ok": True,
                "message": f"異常連絡書を作成しました。\n{output_file}",
            }

        except Exception as e:
            return {
                "ok": False,
                "message": str(e),
            }
```

既存の `register_data()` は変更しない。JavaScriptからは `window.pywebview.api.create_abnormality_report(data)` で呼び出せる。

## 3. `app.js` の修正

### 3-1. 判定関数を追加

`function getTableData()` の閉じ括弧の後、`async function registerData()` の直前に追加する。

```javascript
function needsAbnormalityReport(data) {
    return Object.entries(data).some(([key, value]) => {
        return key.endsWith("_ngcount2") && Number(value) >= 100;
    });
}
```

`_ngcount2` で終わる項目のうち、100以上が1件でもあれば `true`。12項目を個別に列挙する必要はない。

### 3-2. `registerData()` の末尾を置換

現在の末尾：

```javascript
    alert("データ登録完了しました");

    resetAll();
}
```

これを以下に置き換える。

```javascript
    alert("データ登録完了しました");

    // 再検査NG数が100以上の場合、異常連絡書の発行を確認する。
    if (needsAbnormalityReport(data)) {
        const shouldIssue = confirm("異常連絡書に転記しますか？");

        if (shouldIssue) {
            const result = await window.pywebview.api.create_abnormality_report(data);

            if (!result.ok) {
                alert("異常連絡書の作成に失敗しました。\n" + result.message);
            }
        }
    }

    resetAll();
}
```

`resetAll()` は最後に残す。確認ダイアログでキャンセルした場合はExcelを作成せず、画面初期化へ進む。

## 4. 処理の順序

1. データ登録ボタンを押す。
2. `app.js` が入力データと表データを結合して `data` を作る。
3. `app_api.py` の既存 `register_data(data)` で正規化・DB登録。失敗時は中断。
4. 既存のPLCリセット確認と処理を実施。
5. 「データ登録完了しました」を表示。
6. `_ngcount2` のいずれかが100以上なら異常連絡書発行を確認。
7. 「はい」の場合に `create_abnormality_report(data)` を経由してExcel作成。
8. Excelは保存後も開いたまま。画面を `resetAll()` で初期化。

## 5. ファイル配置と実行環境

```text
アプリフォルダ/
├── main.py
├── app_api.py
├── app.js
├── issue_abnormality_report.py
├── data_definition.json
├── 異常連絡書テンプレート.xlsx
└── excel_output/       # 実行時に自動作成
```

Microsoft Excelと `xlwings` が必要。`issue_abnormality_report.py` の `TEST_DATA` と `main()` は単独動作確認用として残せる。importだけでは単独テストは実行されない。

## 6. 正式運用前の注意点

- **PLCリセット失敗時：** 現行の `registerData()` は失敗時に `return` する。DB登録が成功していても、異常連絡書の確認に進まない。今回は既存処理を維持する。
- **帳票に渡す値：** DB登録時は `normalize_record(data)` で正規化するが、ExcelにはJavaScript側の元データを渡す。帳票とDBの値に差がないか確認する。
- **Excel発行失敗時：** DB登録は取り消されない。エラーメッセージを表示する。
- **追加検討（必須修正には含めない）：** データ登録ボタンの二重押し防止、JavaScriptとPythonの通信例外の捕捉、PLCリセット失敗時の発行可否。

## 7. 実機確認時のチェックリスト

- [ ] 全項目100未満：発行確認が出ない
- [ ] 1項目以上100以上：発行確認が出る
- [ ] キャンセル：Excelは作成されない
- [ ] 「はい」：Excelが作成され、開いたままになる
- [ ] 7項目以上100以上：不良数降順の上位6項目だけ転記される
- [ ] 新しいExcelセル位置がテンプレートと一致する
- [ ] DB登録失敗時：発行確認に進まない
- [ ] PLCリセット失敗時：現行仕様では発行確認に進まない
- [ ] Excel発行失敗時：DB登録済みデータが保持される

---

**必須変更は2ファイル・4か所。** 既存のDB登録処理・PLCリセット処理・Excel転記関数は再利用する。
