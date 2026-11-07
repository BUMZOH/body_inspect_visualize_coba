# Python辞書（dict）の基礎解説書

## 1. 辞書とは

辞書（`dict`）は、**キー（key）と値（value）を対応付けて保存する**データ型です。

```python
machine = {
    "machine_no": 412,
    "plc_ip_address": "192.168.8.1",
    "enabled": True,
}
```

- キー：`"machine_no"`、`"plc_ip_address"`、`"enabled"`
- 値：`412`、`"192.168.8.1"`、`True`
- キーは重複できません。値は重複できます。
- キーには文字列・整数・タプルなど、ハッシュ可能なオブジェクトを使えます。リストや辞書はキーにできません。
- Python 3.7以降、辞書は**挿入順序を保持**します。ただし、番号順に自動整列されるわけではありません。

## 2. 辞書の作成と値の取得

```python
machine = {"no": 412, "ip": "192.168.8.1"}
print(machine["no"])  # 412
print(machine["ip"])  # 192.168.8.1
```

`machine["missing"]` のように存在しないキーを指定すると `KeyError` になります。

### `get()`：キーが存在しない場合も安全に取得

```python
print(machine.get("ip"))            # 192.168.8.1
print(machine.get("comment"))       # None
print(machine.get("comment", "未設定"))  # 未設定
```

`get()` はキーがないとき、既定では `None` を返します。第2引数で代わりの値を指定できます。

**注意：** `machine.get("ip")` が `None` でも、「キーがない」のか「値として `None` が保存されている」のかは区別できません。区別したいときは `"ip" in machine` を使います。

## 3. `keys()`、`values()`、`items()` の違い（重要）

```python
machines = {
    "412": {"plc_ip_address": "192.168.8.1"},
    "413": {"plc_ip_address": "192.168.8.11"},
}

print(machines.keys())
print(machines.values())
print(machines.items())
```

| メソッド | 内容 | `for` 文の例 |
|---|---|---|
| `keys()` | キーを取り出す | `for no in machines.keys():` |
| `values()` | 値を取り出す | `for config in machines.values():` |
| `items()` | キーと値の組を取り出す | `for no, config in machines.items():` |

```python
for no in machines.keys():
    print(no)

for config in machines.values():
    print(config)

for no, config in machines.items():
    print(no, config["plc_ip_address"])
```

`items()` が返す各要素は `(キー, 値)` の2要素の組です。`for no, config in ...` はその2要素を**アンパック（分解して代入）**しています。

### `for key in 辞書` は `keys()` と同じ

```python
for no in machines:
    print(no)
```

キーだけ必要なら、`.keys()` は省略できます。

### 戻り値は「リスト」ではなくビュー

`keys()`、`values()`、`items()` は辞書ビューを返します。辞書が更新されるとビューにも反映されます。

```python
keys_view = machines.keys()
machines["416"] = {"plc_ip_address": "192.168.8.21"}
print(list(keys_view))  # ['412', '413', '416']
```

固定した一覧が必要なら `list(machines.keys())` などに変換します。

## 4. 追加・更新・削除

```python
machine = {"no": 412, "ip": "192.168.8.1"}

machine["comment"] = "検査設備"     # 追加
machine["ip"] = "192.168.8.2"      # 更新
machine.update({"enabled": True})  # 複数項目の追加・更新

removed = machine.pop("comment")   # 削除して値を返す
print(removed)  # 検査設備

del machine["enabled"]              # 指定キーを削除
```

- `pop("missing")` はキーがなければ `KeyError`。`pop("missing", None)` なら例外を避けられます。
- `del machine["missing"]` も `KeyError`。
- `machine.clear()` は全要素を削除します。
- `machine.popitem()` は最後に挿入したキーと値の組を取り除いて返します（空なら `KeyError`）。

## 5. キーの存在確認と `len()`

```python
machine = {"no": 412, "ip": "192.168.8.1"}

print("ip" in machine)       # True
print("comment" not in machine)  # True
print(len(machine))         # 2
```

`in` は**値ではなくキー**を調べます。値の存在を調べる場合は `"192.168.8.1" in machine.values()` とします。

## 6. 実際のPLC通信プログラムを読む

今回のコード：

```python
for machine_no, machine_config in machines.items():
    int(machine_no)
    if not machine_config.get("plc_ip_address"):
        raise ValueError(f"設備{machine_no}: plc_ip_address が未設定です")
```

`machines` のイメージ：

```python
machines = {
    "412": {"plc_ip_address": "192.168.8.1"},
    "413": {"plc_ip_address": "192.168.8.11"},
}
```

1. `machines.items()` が設備番号と設定辞書の組を順番に返します。
2. `machine_no` には `"412"` などの文字列が入ります。
3. `machine_config` には `{"plc_ip_address": "192.168.8.1"}` などの辞書が入ります。
4. `int(machine_no)` は整数に変換できることを**検証**します。戻り値を代入していないため `machine_no` 自体は文字列のままです。変換できなければ `ValueError` になります。
5. `machine_config.get("plc_ip_address")` はIPアドレスを取得します。キーがない場合は `None` です。
6. `not ...` により、キーがない・`None`・空文字列などの「偽」と判定される値をエラーにします。

例えば `"   "`（空白だけの文字列）は真と判定されるため、このチェックを通ります。必要なら別途 `.strip()` を使います。

### `int(machine_no)` と代入の違い

```python
machine_no = "412"
int(machine_no)          # 変換結果を捨てる（検証のみ）
print(type(machine_no))  # <class 'str'>

machine_no = int(machine_no)  # 変換結果を代入
print(type(machine_no))      # <class 'int'>
```

JSONオブジェクトのキーは文字列なので、`config.json` から読み込んだ設備番号が `"412"` になるのは自然です。

## 7. ネストした辞書（辞書の中に辞書）

```python
machines = {
    "412": {
        "plc_ip_address": "192.168.8.1",
        "comment": "設備A",
    },
    "413": {
        "plc_ip_address": "192.168.8.11",
        "comment": "設備B",
    },
}

print(machines["412"]["plc_ip_address"])
# 192.168.8.1
```

1つ目の `[...]` で設備を選び、2つ目の `[...]` で設定項目を選びます。

## 8. 辞書内包表記

```python
numbers = [1, 2, 3]
squares = {number: number ** 2 for number in numbers}
print(squares)  # {1: 1, 2: 4, 3: 9}
```

通常の `for` 文なら：

```python
squares = {}
for number in numbers:
    squares[number] = number ** 2
```

PLC通信プログラムの `futures = {...}` も辞書内包表記です。**キーがFutureオブジェクト、値が設備番号**という対応関係を作っています。

## 9. `setdefault()` と `copy()`

### `setdefault()`

```python
machine = {"no": 412}
comment = machine.setdefault("comment", "未設定")
print(comment)  # 未設定
print(machine)  # {'no': 412, 'comment': '未設定'}
```

キーが存在すれば既存値を返し、存在しなければ指定値を登録して返します。単に読むだけなら `get()` の方が適切です。

### `copy()` は浅いコピー

```python
original = {"412": {"ip": "192.168.8.1"}}
copied = original.copy()
copied["412"]["ip"] = "192.168.8.2"
print(original["412"]["ip"])  # 192.168.8.2
```

外側の辞書は別でも、内側の辞書は共有されます。ネスト構造を独立させたいときは `copy.deepcopy()` を検討します。

## 10. ループ中の辞書変更に注意

辞書を反復している最中に要素を追加・削除すると `RuntimeError` になる場合があります。

```python
# 削除する場合はキーのスナップショットを作る
for key in list(machines.keys()):
    if key == "412":
        del machines[key]
```

既存キーの値を変更するだけなら、通常は問題ありません。

## 11. JSONとの関係

```python
import json
from pathlib import Path

config_file = Path("config.json")
with config_file.open(encoding="utf-8") as file:
    config = json.load(file)

machines = config["machines"]
```

JSONのオブジェクトはPythonでは通常 `dict` になります。JSONオブジェクトのキーは文字列です。

Pythonの辞書をJSONへ保存する場合は `json.dump()` を使います。

```python
with Path("output.json").open("w", encoding="utf-8") as file:
    json.dump(machines, file, ensure_ascii=False, indent=4)
```

## 12. よくある間違い

| 間違い | 理由・対策 |
|---|---|
| `machine["missing"]` | 存在しないキーは `KeyError`。`get()` または `in` で確認 |
| `for key, value in machine:` | 辞書を直接反復するとキーだけ。`.items()` を使う |
| `int(machine_no)` で変数が整数になると思う | 戻り値を代入しなければ変数は変わらない |
| `get()` はキーがないとき必ずエラーと思う | 通常 `None` を返す |
| `keys()` がリストと思う | 実際は辞書ビュー。必要なら `list()` |
| `dict.copy()` で内側の辞書も複製されると思う | 浅いコピーなので内側は共有 |
| `"412"` と `412` を同じキーと思う | 文字列と整数は別のキー |

## 13. 復習問題

### 問題1

```python
machine = {"no": 412, "ip": "192.168.8.1"}
```

`keys()`、`values()`、`items()` でそれぞれ何が得られるでしょうか。

### 問題2

```python
machines = {"412": {"ip": "A"}, "413": {"ip": "B"}}
```

設備413のIPを表示するコードを書いてください。

### 問題3

```python
no = "412"
int(no)
```

この後、`no` は文字列と整数のどちらでしょうか。

### 問題4

```python
machine = {"ip": ""}
print(bool(machine.get("ip")))
```

何が表示されるでしょうか。

### 解答

1. キーのビュー、値のビュー、キーと値の組のビュー。
2. `print(machines["413"]["ip"])`
3. 文字列のまま。`int(no)` の戻り値を代入していないため。
4. `False`。空文字列は偽と判定されるため。

## 14. まず覚える最重要ポイント

```python
machine["ip"]             # キーを指定して取得（なければKeyError）
machine.get("ip")         # 安全に取得（なければNone）
"ip" in machine           # キーの存在確認
len(machine)              # 要素数

for key in machine:       # キーだけ
    print(key)

for key, value in machine.items():  # キーと値
    print(key, value)
```

**PLC通信プログラムでは `items()` と `get()` をまず押さえる**と、設定の読み込みと検証処理が読みやすくなります。

---

作成目的：Pythonの辞書を久しぶりに使う際の基礎復習。例はKEYENCE PLC収集プログラムの設備設定を参考にした学習用サンプルです。
