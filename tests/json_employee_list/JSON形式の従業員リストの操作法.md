# jason形式の従業員リストの操作法
#Python #JSON #従業員マスタ #業務アプリ

## 概要

従業員番号と従業員氏名の対応表を外部ファイルとして管理する方法です。

今回はシンプルさを重視し、JSONファイルを利用します。

### employees.json

```json
{
    "011054": "山田太郎",
    "011055": "鈴木健司",
    "011056": "佐藤一郎"
}
```

ポイントは、従業員番号を文字列として管理することです。

```json
"011054"
```

先頭の0を保持できるためです。

---

## フォルダ構成

```text
project/
│
├─ main.py
└─ employees.json
```

---

## サンプルプログラム

### main.py

```python
import json
from pathlib import Path

EMPLOYEE_FILE = Path("employees.json")


def load_employees():
    with EMPLOYEE_FILE.open(
        mode="r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


employees = load_employees()

employee_no = "011054"

employee_name = employees.get(
    employee_no,
    "未登録"
)

print(employee_name)
```

実行結果

```text
山田太郎
```

---

## コード解説

### JSONファイルを開く

```python
with EMPLOYEE_FILE.open(
    mode="r",
    encoding="utf-8"
) as f:
```

employees.json をUTF-8で読み込みます。

UTF-8を指定しておけば日本語も安全に扱えます。

---

### JSONを辞書に変換

```python
json.load(f)
```

JSONファイルをPythonの辞書(dict)に変換します。

例えば

```json
{
    "011054": "山田太郎"
}
```

は

```python
{
    "011054": "山田太郎"
}
```

になります。

---

### get()で検索

```python
employees.get(
    employee_no,
    "未登録"
)
```

従業員番号をキーとして検索します。

存在する場合

```python
employees.get("011054")
```

結果

```text
山田太郎
```

存在しない場合

```python
employees.get(
    "999999",
    "未登録"
)
```

結果

```text
未登録
```

エラーにならないため安全です。

---

## 実務向けサンプル

```python
import json
from pathlib import Path

EMPLOYEE_FILE = Path("employees.json")

EMPLOYEES = {}


def load_employees():
    global EMPLOYEES

    with EMPLOYEE_FILE.open(
        mode="r",
        encoding="utf-8"
    ) as f:
        EMPLOYEES = json.load(f)


def get_employee_name(
    employee_no: str
) -> str:

    return EMPLOYEES.get(
        employee_no,
        "未登録"
    )


if __name__ == "__main__":

    load_employees()

    print(
        get_employee_name(
            "011054"
        )
    )
```

---

## 更新方法

従業員を追加する場合はJSONを編集します。

```json
{
    "011054": "山田太郎",
    "011055": "鈴木健司",
    "011056": "佐藤一郎",
    "011057": "高橋花子"
}
```

プログラム側の修正は不要です。

---

## JSON方式のメリット

### シンプル

SQLite不要。

INIファイルよりもPythonの辞書に近い。

---

### 高速

起動時に1回読み込むだけ。

数百人程度なら性能問題はほぼありません。

---

### 拡張可能

将来的に

```json
{
    "011054": {
        "name": "山田太郎",
        "department": "製造1課"
    }
}
```

のような構造へ発展できます。

---

## 今回の結論

従業員番号から氏名を取得するだけなら、

```json
{
    "011054": "山田太郎",
    "011055": "鈴木健司"
}
```

というJSON形式が最もシンプルです。

Pythonでは辞書として扱えるため、

```python
employee_name = employees.get(
    employee_no,
    "未登録"
)
```

だけで検索できます。

小規模～中規模の業務アプリでは十分実用的な方法です。
