# Python `all()` と `any()` の基礎解説書

## 1. 何をする関数？

`all()` と `any()` は、複数の値をまとめて真偽判定する **Pythonの組み込み関数** です。`import` は不要です。

| 関数 | `True` になる条件 | 覚え方 |
|---|---|---|
| `all()` | すべての要素が真 | 全部OK？ |
| `any()` | 1つでも真の要素がある | どれかOK？ |
| `not all()` | 1つでも偽の要素がある | 全部OKではない？ |
| `not any()` | 真の要素が1つもない | どれもOKではない？ |

## 2. 最小サンプル

次のコードはそのまま実行できます。

```python
print(all([True, True, True]))   # True
print(all([True, False, True]))  # False

print(any([False, False, True]))  # True
print(any([False, False, False])) # False
```

### `not` と組み合わせる

```python
checks = [True, False, True]

print(all(checks))      # False
print(not all(checks))  # True
print(any(checks))      # True
print(not any(checks))  # False
```

`not` は `True` と `False` を反転します。

## 3. `if` 文で使う

### `all()`：全項目が合格なら実行

```python
scores = [80, 90, 70]

if all(score >= 60 for score in scores):
    print("全員合格")
```

### `any()`：1項目でも異常なら実行

```python
scores = [80, 40, 70]

if any(score < 60 for score in scores):
    print("不合格者がいます")
```

ここでの `score >= 60 for score in scores` は **ジェネレータ式** です。リストの各要素に対して条件を順番に判定します。

## 4. PLC通信プログラムの実例

元のコード：

```python
if not all(
    len(values) == DATA_COUNT
    for values in (date_values, operating_values, production_values)
):
    raise ValueError("受信件数が500件ではありません")
```

`DATA_COUNT = 500` の場合、3種類の受信データが **すべて500件** か確認しています。1つでも500件でなければ `ValueError` です。

### `any()` で書き換える

```python
if any(
    len(values) != DATA_COUNT
    for values in (date_values, operating_values, production_values)
):
    raise ValueError("受信件数が500件ではありません")
```

**`not all(条件が正しい)` と `any(条件が間違っている)` は、この例では同じ判定です。**

### `or` で書く方法

```python
if (
    len(date_values) != DATA_COUNT
    or len(operating_values) != DATA_COUNT
    or len(production_values) != DATA_COUNT
):
    raise ValueError("受信件数が500件ではありません")
```

確認対象が3つだけなら、こちらも読みやすい書き方です。

## 5. `all()` と `any()` の重要な性質

### 5-1. `True` / `False` 以外も判定できる

Pythonでは `0`、`""`、`None`、空のリストなどは偽として扱われます。

```python
print(all([1, 2, 3]))  # True
print(all([1, 0, 3]))  # False
print(any([0, 0, 5]))  # True
print(any([0, 0, 0]))  # False
```

### 5-2. 空のデータには注意

```python
print(all([]))  # True
print(any([]))  # False
```

`all([])` が `True` なのは「条件に違反する要素が1つもない」ためです。空のデータをエラーにしたい場合は、別途確認します。

```python
values = []

if not values or not all(values):
    print("空、または偽の要素があります")
```

### 5-3. 判定は必要なところで止まる

- `all()` は最初の偽の要素を見つけたら、それ以降を調べません。
- `any()` は最初の真の要素を見つけたら、それ以降を調べません。

この性質を **短絡評価** と呼びます。

## 6. ジェネレータ式とリスト内包表記

どちらも使えます。

```python
numbers = [2, 4, 6]

print(all(n % 2 == 0 for n in numbers))    # ジェネレータ式
print(all([n % 2 == 0 for n in numbers]))  # リスト内包表記
```

`all()` / `any()` に渡すだけなら、通常は **余分なリストを作らないジェネレータ式** が簡潔です。

## 7. よくある間違い

### `all(a, b, c)` と書かない

`all()` に渡す引数は、リストやタプルなどの **反復可能なオブジェクト1つ** です。

```python
# NG: all(True, False, True)

# OK
print(all([True, False, True]))
print(all((True, False, True)))
```

### `all()` は要素同士の比較を自動で行わない

```python
numbers = [500, 500, 499]

print(all(numbers))                 # True（すべて0以外）
print(all(n == 500 for n in numbers))  # False
```

件数が500かどうかを調べるなら、`n == 500` という条件が必要です。

## 8. 復習問題

次の結果を予想してから実行してください。

```python
print(all([True, True, False]))
print(any([False, False, False]))
print(not all([True, True, True]))
print(not any([False, False]))
print(all([]))
```

**答え（上から順に）**：`False`、`False`、`False`、`True`、`True`

## 9. まとめ

- **`all()`**：すべて満たすかを確認する。
- **`any()`**：1つでも満たすかを確認する。
- **`not all()`**：1つでも満たさないものがあるかを確認する。
- **`not any()`**：1つも満たすものがないかを確認する。
- PLCの受信件数チェックには `not all(...)` も `any(...)` も使える。
- KISS重視なら、短い `or` 条件の方が読みやすい場合もある。
