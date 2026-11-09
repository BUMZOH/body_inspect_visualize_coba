# Python型エイリアスの基礎解説書

## 1. 型エイリアスとは

**型エイリアス（type alias）**とは、長い型の表記に分かりやすい名前を付ける仕組みです。新しい型を作るわけではなく、既存の型に別名を付けます。

```python
ProductionRow = tuple[int, str, int, int]
```

これで `ProductionRow` は「整数、文字列、整数、整数の4要素からなるタプル」という型の別名になります。

```python
def save_row(row: ProductionRow) -> None:
    print(row)
```

次のように書くのと型の意味は同じです。

```python
def save_row(row: tuple[int, str, int, int]) -> None:
    print(row)
```

**重要：型ヒントは原則として実行時の値を自動検査しません。** 型の不一致は、Pylanceやmypyなどの静的解析ツールで検出するのが基本です。

## 2. 型ヒントの基本を復習

```python
def add(a: int, b: int) -> int:
    return a + b
```

- `a: int`：引数 `a` は整数を想定
- `b: int`：引数 `b` は整数を想定
- `-> int`：戻り値は整数を想定
- `-> None`：戻り値として値を返さない関数

代表的な型の表記：

| 表記 | 意味 | 例 |
|---|---|---|
| `int` | 整数 | `10` |
| `str` | 文字列 | `"412"` |
| `bool` | 真偽値 | `True` |
| `list[int]` | 整数のリスト | `[1, 2, 3]` |
| `dict[str, str]` | キー・値が文字列の辞書 | `{"ip": "192.168.8.1"}` |
| `tuple[int, str]` | 整数と文字列の2要素タプル | `(412, "OK")` |
| `str | None` | 文字列または `None` | `None` |

`list[int]` や `dict[str, str]` はPython 3.9以降、`str | None` はPython 3.10以降の表記です。

## 3. 今回のPLC通信プログラムの実例

### 3.1 1行分の生産実績

```python
ProductionRow = tuple[int, str, int, int]
```

1行の具体例：

```python
row = (412, "2026-11-08 08:00", 3500, 120)
```

| 要素 | 型 | 意味 |
|---|---|---|
| `412` | `int` | 設備番号 |
| `"2026-11-08 08:00"` | `str` | 時刻 |
| `3500` | `int` | 稼働秒数 |
| `120` | `int` | 1時間の生産数 |

### 3.2 設備の通信設定

```python
MachineConfig = dict[str, str]
Machines = dict[str, MachineConfig]
```

たとえば：

```python
machines = {
    "412": {"plc_ip_address": "192.168.8.1"},
    "413": {"plc_ip_address": "192.168.8.11"},
}
```

外側の辞書のキーは文字列の設備番号、値は各設備の設定辞書です。`Machines` を定義する際に `MachineConfig` を再利用することで、構造が分かりやすくなります。

### 3.3 複雑な戻り値を短くする

```python
def receive_machine_data(
    machine_no: str,
    machine_config: MachineConfig,
) -> tuple[str, list[ProductionRow], int]:
    ...
```

戻り値は次の3つです。

1. `str`：設備番号
2. `list[ProductionRow]`：登録する生産実績の行一覧
3. `int`：日時が0で除外した件数

実際の戻り値のイメージ：

```python
return "412", [
    (412, "2026-11-08 08:00", 3500, 120),
    (412, "2026-11-08 09:00", 3400, 115),
], 498
```

型エイリアスを使わなければ、`list[tuple[int, str, int, int]]` と毎回書く必要があります。

## 4. 型エイリアスの宣言方法

### 方法A：シンプルな代入

```python
ProductionRow = tuple[int, str, int, int]
```

簡潔で、Python 3.9以降の型ヒントでも使いやすい方法です。ただし、通常の変数代入と見た目が似ています。

### 方法B：`TypeAlias` を使う（Python 3.10以降）

```python
from typing import TypeAlias

ProductionRow: TypeAlias = tuple[int, str, int, int]
```

`TypeAlias` は「これは通常の変数ではなく、型の別名です」と静的解析ツールに明示するための印です。今回のコードで採用した方式です。

`TypeAlias` は実行時の型チェックを追加するものではありません。

### 方法C：`type` 文（Python 3.12以降）

```python
type ProductionRow = tuple[int, str, int, int]
```

新しい構文です。Python 3.11以前では構文エラーになります。また、内部的には `TypeAliasType` を使うなど、旧方式と実行時の扱いが一部異なります。

**今回のプログラムはPython 3.10以降を想定しているため、`TypeAlias` 方式で十分です。**

## 5. `TypeAlias` と普通の変数の違い

```python
from typing import TypeAlias

ProductionRow: TypeAlias = tuple[int, str, int, int]
```

これはデータを1件作っているわけではありません。型の説明に名前を付けています。

一方、こちらは実際のデータです。

```python
row: ProductionRow = (412, "2026-11-08 08:00", 3500, 120)
```

- `ProductionRow`：型の別名
- `row`：実際のタプルデータ

型エイリアスは、クラス定義のように独立した新しい型を作る仕組みではありません。

## 6. リスト・タプル・辞書の型表記の読み方

```python
Rows = list[ProductionRow]
```

`ProductionRow` が複数入ったリスト。

```python
ReceivedMachine = tuple[str, Rows]
```

設備番号と、その設備から受信した行一覧の2要素タプル。

```python
ReceivedMachines = list[ReceivedMachine]
```

受信成功した設備の結果をまとめたリスト。

ただし、**何でも型エイリアスにする必要はありません。** 1回しか使わない簡単な型なら、その場に書いた方が読みやすいこともあります。

## 7. よくある勘違い

### Q1. 型エイリアスを定義すると値が変換される？

いいえ。型エイリアスは値を変換しません。`str` を `int` に変えるには、従来どおり `int(value)` が必要です。

### Q2. 間違った型を渡すと必ず例外になる？

いいえ。Pythonの型ヒントは基本的に実行時に強制されません。VS CodeのPylanceやmypyなどで事前に確認します。

### Q3. 型エイリアスは処理速度を速くする？

通常、その目的では使いません。主な利点は読みやすさと保守性です。

### Q4. タプルの型とリストの型は同じ？

違います。`tuple[int, str]` は原則2要素のタプル、`list[int]` は整数を0個以上格納するリストです。

### Q5. `machine_no` が文字列なのはなぜ？

JSONのオブジェクトのキーは文字列です。`config.json` から読み込んだ設備番号キーは、例えば `"412"` となります。DBへ登録するときに `int(machine_no)` で整数へ変換しています。

## 8. 型エイリアスを使う判断基準

使うとよいケース：

- 同じ複雑な型が複数の関数に登場する
- `tuple[...]` や `dict[...]` が長くなり、意味を読み取りにくい
- `ProductionRow` のように業務上の意味を名前で表現できる

無理に使わなくてよいケース：

- `str`、`int`、`list[str]` のような短い型
- 一度しか登場せず、別名の方がかえって分かりにくい型

今回のPLC通信プログラムなら、`MachineConfig`、`Machines`、`ProductionRow` のような業務データの型を定義するのは自然です。

## 9. 復習用ミニ演習

**問題1**：次の型エイリアスは何を表しますか？

```python
AlarmRow: TypeAlias = tuple[int, str, int]
```

**問題2**：`list[AlarmRow]` は何を表しますか？

**問題3**：次の関数は何を返す想定ですか？

```python
def get_machine_names() -> list[str]:
    ...
```

**問題4**：型エイリアスを宣言すると、間違った型の値をPythonが自動的に拒否しますか？

### 解答

1. 整数・文字列・整数の3要素タプル
2. `AlarmRow` を要素に持つリスト
3. 文字列のリスト
4. いいえ。静的解析による確認が基本です

## 10. まとめ

型エイリアスは、**長い型の表記に意味のある名前を付ける仕組み**です。

```python
from typing import TypeAlias

MachineConfig: TypeAlias = dict[str, str]
Machines: TypeAlias = dict[str, MachineConfig]
ProductionRow: TypeAlias = tuple[int, str, int, int]
```

型エイリアスによって関数定義が短くなり、引数・戻り値の意味が理解しやすくなります。ただし、型エイリアスを増やしすぎると逆に読みにくくなるため、**KISSを優先し、必要な型だけに名前を付ける**方針がおすすめです。
