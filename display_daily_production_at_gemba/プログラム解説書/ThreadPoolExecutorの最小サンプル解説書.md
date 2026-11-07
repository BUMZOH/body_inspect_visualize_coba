# ThreadPoolExecutorの最小サンプル解説書

## 1. この資料の目的

Pythonの `ThreadPoolExecutor` と `as_completed` を、3つの待機処理を並列実行する最小サンプルで復習します。特に、**スレッド・Future・submit・as_completed・result・辞書内包表記**の関係を理解することが目標です。

## 2. 実行できるサンプル（元コード）

```python
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def worker(number, wait_sec):
    """指定秒数待って、結果を返す。"""
    print(f"仕事{number}: 開始")
    time.sleep(wait_sec)
    print(f"仕事{number}: 終了")

    return number * 10


def main():
    jobs = {
        1: 3,
        2: 1,
        3: 2,
    }

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(worker, number, wait_sec): number
            for number, wait_sec in jobs.items()
        }

        for future in as_completed(futures):
            number = futures[future]
            result = future.result()
            print(f"仕事{number}: 結果={result}")


if __name__ == "__main__":
    main()
```

## 3. 実行結果と所要時間

実行結果の一例：

```text
仕事1: 開始
仕事2: 開始
仕事3: 開始
仕事2: 終了
仕事2: 結果=20
仕事3: 終了
仕事3: 結果=30
仕事1: 終了
仕事1: 結果=10
```

3つの仕事は、それぞれ3秒・1秒・2秒待機します。逐次実行なら待機時間は合計6秒ですが、3スレッドで同時に待機すれば全体はおよそ3秒です（起動・表示などの時間は別）。**開始表示の順番は保証されません。** 完了順は、このサンプルの待機時間が十分に異なるため通常は仕事2→3→1ですが、一般にはスレッドのスケジューリング次第です。

```text
時刻（秒）    0       1       2       3
仕事1        [----------3秒----------]
仕事2        [--1秒--]
仕事3        [------2秒------]
```

## 4. まず知っておきたい基礎用語

| 用語 | 意味 | このサンプルでの役割 |
|---|---|---|
| スレッド | 同じプロセス内で実行される処理の流れ | 仕事を並行して進める |
| スレッドプール | 再利用できるスレッドの集まり | 仕事を割り当てる |
| `ThreadPoolExecutor` | スレッドプールを管理するクラス | 最大3スレッドを管理 |
| `executor` | 作成したExecutorのインスタンス | 仕事を投入する窓口 |
| `submit()` | 関数の実行をプールへ依頼する | `worker` を3回登録 |
| `Future` | 非同期に実行される仕事の状態・結果を保持するオブジェクト | 仕事の識別と結果の取得 |
| `as_completed()` | 完了したFutureから順に取り出す | 終了順に処理する |
| `future.result()` | 関数の戻り値を受け取る | 10、20、30を取得 |

**並列実行と同時実行の違い：** この例の `time.sleep()` は待機処理なので、スレッドを使う効果が分かりやすく現れます。一方、通常のCPythonではGILの影響により、純粋なPythonのCPU計算がスレッド数に比例して速くなるとは限りません。ネットワーク通信やファイルI/Oなど、待ち時間が多い処理に向いています。

## 5. コードを上から順番に読む

### 5.1 import

```python
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
```

- `time.sleep()` は指定秒数だけ現在のスレッドを待機させます。
- `ThreadPoolExecutor` はスレッドプールを作ります。
- `as_completed` は完了したFutureを順次取得するための関数です。

### 5.2 worker関数

```python
def worker(number, wait_sec):
    print(f"仕事{number}: 開始")
    time.sleep(wait_sec)
    print(f"仕事{number}: 終了")
    return number * 10
```

引数 `number` は仕事番号、`wait_sec` は待機秒数です。`return` した値は、呼び出し元で `future.result()` により受け取ります。例えば `worker(2, 1)` の結果は `20` です。

### 5.3 jobs辞書

```python
jobs = {1: 3, 2: 1, 3: 2}
```

辞書の **キー** が仕事番号、**値** が待機秒数です。`jobs.items()` は `(1, 3)`、`(2, 1)`、`(3, 2)` というキーと値の組を順番に取り出せます。

### 5.4 ThreadPoolExecutorとwith

```python
with ThreadPoolExecutor(max_workers=3) as executor:
```

`max_workers=3` は同時に実行できるワーカースレッドの最大数です。仕事が3件なので、3件とも投入後に進行できます。仕事が5件なら最大3件を並行実行し、空いたスレッドで残りを処理します。

`with` を抜けるとExecutorは終了処理を行い、登録済みの仕事の完了を待ちます。SQLiteの `with sqlite3.connect(...)` とは異なり、こちらの `with` はExecutorの後片付けを行います。

### 5.5 executor.submit

```python
future = executor.submit(worker, number, wait_sec)
```

これは「`worker(number, wait_sec)` をスレッドプールで実行してください」という依頼です。`submit` は**関数そのもの**と引数を別々に渡します。

```python
executor.submit(worker, 1, 3)    # 正しい：workerの実行を依頼
executor.submit(worker(1, 3))    # 誤り：先にworkerを実行してしまう
```

`submit` は通常、仕事の完了を待たずに `Future` を返します。`Future` は結果そのものではありません。

### 5.6 futures辞書の意味

```python
futures = {
    executor.submit(worker, number, wait_sec): number
    for number, wait_sec in jobs.items()
}
```

これは**辞書内包表記**です。キーが `Future`、値が仕事番号となる辞書を作ります。イメージ：

```text
Future(仕事1) → 1
Future(仕事2) → 2
Future(仕事3) → 3
```

`Future(仕事1)` は説明用表記であり、実際のPython構文ではありません。Futureから仕事番号を逆引きするための辞書です。

**同じ処理を通常のfor文で書くと：**

```python
futures = {}

for number, wait_sec in jobs.items():
    future = executor.submit(worker, number, wait_sec)
    futures[future] = number
```

初めて読むときはこちらのほうが理解しやすいでしょう。処理内容は同じです。

### 5.7 as_completed

```python
for future in as_completed(futures):
```

`futures` は辞書ですが、辞書を反復するとキーを取り出すので、ここでは `Future` が渡されます。`as_completed` は**完了したFutureから順に返す**イテレータです。まだ完了していない場合は次の完了まで待ちます。

ここで `for future in futures:` とすると、辞書に登録された順番でFutureを扱うため、先頭の仕事1がまだ終わっていないと `result()` で待たされ、仕事2が先に終わっていても結果表示が遅れます。

### 5.8 futures[future] と future.result()

```python
number = futures[future]
result = future.result()
print(f"仕事{number}: 結果={result}")
```

- `futures[future]` は、**どの仕事か（番号）**を辞書から取り出します。
- `future.result()` は、**仕事が返した結果**を取り出します。

例えば仕事2が終了したとき、`number` は `2`、`result` は `20` です。`as_completed` で受け取ったFutureは完了済みなので、通常 `result()` はすぐ戻ります。ただし、仕事中に例外が起きていた場合は、ここで例外が再送出されます。

### 5.9 if __name__ == "__main__"

```python
if __name__ == "__main__":
    main()
```

このファイルを直接実行した場合に `main()` を呼び出します。別のPythonファイルから `import` された場合は、ここでは `main()` を実行しません。

## 6. 処理の流れを整理

```text
main()
  │
  ├─ jobsを用意
  │
  ├─ ThreadPoolExecutorを作成
  │    ├─ submit(worker, 1, 3) → Future A
  │    ├─ submit(worker, 2, 1) → Future B
  │    └─ submit(worker, 3, 2) → Future C
  │
  ├─ as_completed(futures)
  │    ├─ Future B完了 → 仕事2、結果20
  │    ├─ Future C完了 → 仕事3、結果30
  │    └─ Future A完了 → 仕事1、結果10
  │
  └─ with終了：Executorの後片付け
```

## 7. 例外処理の基本

スレッド内で例外が発生しても、`submit` の時点で直ちにメインスレッドへ例外が飛ぶわけではありません。`future.result()` で例外が再送出されます。PLC通信のように仕事ごとの失敗を記録したいときは次のようにします。

```python
for future in as_completed(futures):
    number = futures[future]
    try:
        result = future.result()
        print(f"仕事{number}: 成功、結果={result}")
    except Exception as error:
        print(f"仕事{number}: 失敗、理由={error}")
```

こうすれば1件が失敗しても、ほかのFutureの結果を続けて処理できます。

## 8. PLC通信プログラムとの対応

| 学習サンプル | PLC受信プログラム |
|---|---|
| `worker(number, wait_sec)` | `receive_machine_data(machine_no, machine_config)` |
| `jobs` | `machines` |
| `max_workers=3` | `max_workers=len(machines)` |
| `submit(worker, ...)` | `submit(receive_machine_data, ...)` |
| `futures[future]` | 対応する設備番号を取得 |
| `future.result()` | `(machine_no, rows, skipped)` を取得 |
| `as_completed(futures)` | 通信が終わった設備から結果を処理 |

実際のPLCプログラムでは、**PLCからの受信だけを並列化し、SQLiteへの登録は受信完了後に順番に実行**しています。この分離により、DBへの書き込み処理が複数の受信スレッドから同時に行われるのを避けられます。

## 9. よくある疑問・注意点

**Q. `max_workers=3` なら必ず3つ同時に実行される？**  
A. 最大3つです。スケジューリングや仕事の数によって、実際の動作は変わります。

**Q. `submit()` の戻り値は `worker()` の戻り値？**  
A. 違います。`Future` です。実際の戻り値は `future.result()` で取得します。

**Q. `as_completed()` は仕事を開始する？**  
A. いいえ。仕事の登録・実行開始は `submit()` が担当します。`as_completed()` は完了通知を受け取る側です。

**Q. `future.result()` は待機する？**  
A. 未完了のFutureなら完了まで待機します。`as_completed()` から取得したFutureはすでに完了しているため、通常は待ちません。

**Q. 結果は投入順に並ぶ？**  
A. いいえ。`as_completed()` は完了順です。元の順番が必要なら仕事番号を使って整理します。

**Q. `print()` の順序は常に同じ？**  
A. いいえ。複数スレッドの実行順序は保証されません。

**Q. `with` を抜けたらどうなる？**  
A. Executorが終了処理を行い、登録済みの処理の完了を待ちます。

## 10. 復習用の小さな実験

1. `max_workers=1` に変更し、所要時間が約6秒になることを確認する。
2. `max_workers=2` に変更し、最大2つずつ進む様子を確認する。
3. `jobs` の待機秒数を変更し、結果の表示順が変わることを確認する。
4. 辞書内包表記を通常の `for` 文に置き換えて、同じ結果になることを確認する。
5. `worker()` に `if number == 2: raise ValueError("テストエラー")` を入れ、7章の `try / except` を試す。

※所要時間を測りたい場合は、`main()` の前後で `time.perf_counter()` の差を表示すると便利です。

## 11. 最重要ポイント（復習チェック）

- `ThreadPoolExecutor`：スレッドプールを管理する。
- `max_workers`：同時に動くワーカーの**最大数**。
- `submit(関数, 引数...)`：関数を実行依頼し、`Future` を返す。
- `Future`：仕事の状態と結果を管理するオブジェクト。
- `futures[future]`：どの仕事のFutureなのかを調べる。
- `as_completed(futures)`：**完了した順番**にFutureを取り出す。
- `future.result()`：戻り値を取得する。例外があればここで再送出される。
- PLCのような**通信待ちがある処理**はスレッド並列化と相性がよい。

---

**一言でまとめると：** `submit()` で仕事を依頼し、`as_completed()` で終わった仕事から受け取り、`result()` で結果を取り出す。
