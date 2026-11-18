# search_record_waiting_machineのマルチスレッド化

## 1. はじめに

現在の `search_record_waiting_machine()` は、`config.json` に登録されている設備を1台ずつ順番に確認し、PLCの `EM10011` がONになっている設備を探します。

現在の方式はシンプルで分かりやすい一方、電源OFFや通信異常の設備が増えると、PLC通信のタイムアウト待ちが設備台数分だけ積み重なる可能性があります。

例えば、1台あたりの通信タイムアウトが3秒で、電源OFFの設備が10台ある場合は、最悪で次のようになります。

```text
設備1のタイムアウト待ち：3秒
設備2のタイムアウト待ち：3秒
設備3のタイムアウト待ち：3秒
...
設備10のタイムアウト待ち：3秒

合計：約30秒
```

この待ち時間を短縮する方法として、複数の設備へ同時に通信する**マルチスレッド化**があります。

本書では、現在の直列処理を確認したうえで、`ThreadPoolExecutor` を使って `search_record_waiting_machine()` をマルチスレッド化する方法を、学習用として丁寧に解説します。

---

## 2. 現在の直列処理

現在の処理は、おおむね次のような構成です。

```python
def search_record_waiting_machine() -> dict[str, list[str]]:
    """記録待ち設備と通信できなかった設備の一覧を返す。"""
    record_waiting_machines = []
    communication_error_machines = []

    for machine_no, machine_config in config["machines"].items():
        plc_ip_address = machine_config["plc_ip_address"]

        try:
            record_waiting = int(
                kv_com.read_device_u(
                    plc_ip_address,
                    "EM10011",
                )
            )
        except Exception as error:
            print(
                f"設備番号{machine_no}のPLC通信に失敗しました。"
                f" IPアドレス: {plc_ip_address}"
            )
            print(error)
            communication_error_machines.append(machine_no)
            continue

        if record_waiting == 1:
            record_waiting_machines.append(machine_no)

    return {
        "record_waiting_machines": record_waiting_machines,
        "communication_error_machines": communication_error_machines,
    }
```

このコードでは、`for` 文によって設備を1台ずつ順番に確認しています。

```text
設備551へ通信
    ↓
結果を待つ
    ↓
設備552へ通信
    ↓
結果を待つ
    ↓
設備553へ通信
    ↓
結果を待つ
```

通信可能な設備だけであれば大きな問題になりません。しかし、電源OFFの設備では通信タイムアウトが発生するため、次の設備へ進むまで待ち時間が発生します。

---

## 3. マルチスレッド化の考え方

マルチスレッド化すると、複数の設備に対する通信をほぼ同時に開始できます。

```text
設備551へ通信 ─┐
設備552へ通信 ─┤
設備553へ通信 ─┤ 同時に実行
設備554へ通信 ─┤
設備555へ通信 ─┘
```

仮に10台すべてが電源OFFで、1台あたり3秒のタイムアウトが発生する場合でも、10台を同時に確認すれば、理論上はおおむね3秒前後で処理が終わります。

```text
直列処理：3秒 × 10台 ＝ 約30秒
並列処理：10台を同時に確認 ＝ 約3秒前後
```

実際にはスレッドの作成や処理の切り替えにわずかな時間がかかりますが、直列処理より大幅に短縮できる可能性があります。

---

## 4. なぜPLC通信とマルチスレッドの相性がよいのか

PLC通信では、プログラムの多くの時間が次のような「待ち時間」になります。

- PLCから応答が返るまで待つ
- ソケット通信の受信を待つ
- タイムアウトになるまで待つ
- ネットワーク通信が完了するまで待つ

このような処理を**I/O待ち処理**と呼びます。

あるスレッドがPLCの応答を待っている間に、別のスレッドが他の設備へ通信できるため、マルチスレッド化の効果が出やすくなります。

```text
スレッド1：設備551の応答待ち
スレッド2：設備552へ通信
スレッド3：設備553の結果を受信
```

CPUで重い計算を続ける処理ではなく、外部機器の応答を待つ処理だからこそ、マルチスレッド化が有効です。

---

## 5. 使用する標準ライブラリ

今回はPython標準ライブラリの `concurrent.futures` を使います。

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
```

### ThreadPoolExecutor

複数のスレッドを管理してくれる仕組みです。

- スレッドを作る
- 関数を別スレッドで実行する
- 実行結果を受け取る
- スレッドを安全に終了する

といった処理を簡潔に書けます。

### as_completed

登録した処理のうち、完了したものから順番に結果を受け取るために使います。

設備番号順に処理を開始しても、完了順は同じとは限りません。

```text
開始順：551 → 552 → 553
完了順：553 → 551 → 552
```

`as_completed()` を使うと、完了したものから結果を処理できます。

---

## 6. 1台分の処理を別関数へ分ける

マルチスレッド化する場合は、まず「設備1台を確認する処理」を独立した関数へ分けると分かりやすくなります。

```python
def check_record_waiting_machine(
        machine_no: str,
        machine_config: dict
) -> tuple[str, bool, bool]:
    """
    1台の設備について、記録待ち状態を確認する。

    Returns:
        tuple[str, bool, bool]:
            machine_no:
                設備番号

            is_record_waiting:
                EM10011がONならTrue

            has_communication_error:
                PLC通信に失敗した場合はTrue
    """
    plc_ip_address = machine_config["plc_ip_address"]

    try:
        record_waiting = int(
            kv_com.read_device_u(
                plc_ip_address,
                "EM10011",
            )
        )

        return machine_no, record_waiting == 1, False

    except Exception as error:
        print(
            f"設備番号{machine_no}のPLC通信に失敗しました。"
            f" IPアドレス: {plc_ip_address}"
        )
        print(error)

        return machine_no, False, True
```

この関数は、設備1台だけを担当します。

---

## 7. 戻り値の意味

この関数は3つの値をタプルで返します。

```python
return machine_no, is_record_waiting, has_communication_error
```

### 設備555が記録待ちの場合

```python
("555", True, False)
```

### 設備556と通信できなかった場合

```python
("556", False, True)
```

### 設備557が通信成功、記録待ちではない場合

```python
("557", False, False)
```

2つの真偽値により、次の3状態を表現できます。

| is_record_waiting | has_communication_error | 状態 |
|---|---|---|
| `True` | `False` | 記録待ち |
| `False` | `False` | 通信成功、記録待ちではない |
| `False` | `True` | 通信失敗 |

---

## 8. 全設備を並列で確認する関数

```python
def search_record_waiting_machine() -> dict[str, list[str]]:
    """
    全設備を並列で確認し、
    記録待ち設備と通信失敗設備を返す。
    """
    record_waiting_machines = []
    communication_error_machines = []

    machines = config["machines"]

    with ThreadPoolExecutor(
        max_workers=min(len(machines), 10)
    ) as executor:

        futures = [
            executor.submit(
                check_record_waiting_machine,
                machine_no,
                machine_config,
            )
            for machine_no, machine_config in machines.items()
        ]

        for future in as_completed(futures):
            machine_no, is_record_waiting, has_communication_error = (
                future.result()
            )

            if has_communication_error:
                communication_error_machines.append(machine_no)
                continue

            if is_record_waiting:
                record_waiting_machines.append(machine_no)

    return {
        "record_waiting_machines": sorted(record_waiting_machines),
        "communication_error_machines": sorted(
            communication_error_machines
        ),
    }
```

---

## 9. ThreadPoolExecutorの作成

```python
with ThreadPoolExecutor(
    max_workers=min(len(machines), 10)
) as executor:
```

`with` 文を使うことで、処理終了後にスレッドを安全に終了できます。

ファイル操作やSQLite接続と同じ考え方です。

```python
with open(...) as file:
    ...
```

```python
with sqlite3.connect(...) as conn:
    ...
```

---

## 10. max_workersとは

`max_workers` は、同時に動作できるスレッド数の上限です。

```python
max_workers=min(len(machines), 10)
```

- 設備が5台なら5スレッド
- 設備が10台なら10スレッド
- 設備が20台でも最大10スレッド

となります。

上限を設けることで、将来設備数が大幅に増えても、無制限にスレッドを作らないようにできます。

現在のように5～10台程度であれば、設備数と同じ数のスレッドを作っても大きな問題になりにくいと考えられます。

---

## 11. executor.submit()とは

```python
executor.submit(
    check_record_waiting_machine,
    machine_no,
    machine_config,
)
```

これは、次の関数呼び出しを別スレッドで実行するという意味です。

```python
check_record_waiting_machine(
    machine_no,
    machine_config,
)
```

ただし、`submit()` はその場で最終結果を返すのではなく、`Future` オブジェクトを返します。

---

## 12. Futureとは

`Future` は、「現在実行中、または今後完了する処理」を表すオブジェクトです。

```text
Future
├─ 実行待ち
├─ 実行中
├─ 完了
└─ 例外発生
```

処理完了後は、次のように結果を取得できます。

```python
result = future.result()
```

---

## 13. 全設備の処理を登録する

リスト内包表記を使う場合は次のようになります。

```python
futures = [
    executor.submit(
        check_record_waiting_machine,
        machine_no,
        machine_config,
    )
    for machine_no, machine_config in machines.items()
]
```

通常の `for` 文で書くと次のとおりです。

```python
futures = []

for machine_no, machine_config in machines.items():
    future = executor.submit(
        check_record_waiting_machine,
        machine_no,
        machine_config,
    )
    futures.append(future)
```

学習初期は、通常の `for` 文の方が処理を追いやすい場合があります。

---

## 14. as_completed()による結果取得

```python
for future in as_completed(futures):
```

登録順ではなく、完了順に結果を受け取ります。

```python
machine_no, is_record_waiting, has_communication_error = (
    future.result()
)
```

例えば戻り値が次の場合、

```python
("555", True, False)
```

各変数には次の値が入ります。

```python
machine_no = "555"
is_record_waiting = True
has_communication_error = False
```

---

## 15. 結果の分類

### 通信エラー設備

```python
if has_communication_error:
    communication_error_machines.append(machine_no)
    continue
```

`continue` によって、その設備に対する以降の処理を飛ばします。

### 記録待ち設備

```python
if is_record_waiting:
    record_waiting_machines.append(machine_no)
```

通信成功かつOFFの場合は、どちらのリストにも追加されません。

---

## 16. sorted()を使う理由

マルチスレッド処理では、結果が完了順に返ります。そのため、設備番号順になるとは限りません。

```text
開始順：551, 552, 553, 554, 555
完了順：553, 551, 555, 552, 554
```

そこで、戻り値を返す前に並べ替えます。

```python
sorted(record_waiting_machines)
```

```python
sorted(communication_error_machines)
```

これにより、JavaScript側で表示する設備番号の順番が安定します。

---

## 17. 完成コード

```python
from concurrent.futures import ThreadPoolExecutor, as_completed


def check_record_waiting_machine(
        machine_no: str,
        machine_config: dict
) -> tuple[str, bool, bool]:
    """
    1台の設備について、記録待ち状態を確認する。

    Returns:
        tuple[str, bool, bool]:
            machine_no:
                設備番号

            is_record_waiting:
                EM10011がONならTrue

            has_communication_error:
                PLC通信に失敗した場合はTrue
    """
    plc_ip_address = machine_config["plc_ip_address"]

    try:
        record_waiting = int(
            kv_com.read_device_u(
                plc_ip_address,
                "EM10011",
            )
        )

        return machine_no, record_waiting == 1, False

    except Exception as error:
        print(
            f"設備番号{machine_no}のPLC通信に失敗しました。"
            f" IPアドレス: {plc_ip_address}"
        )
        print(error)

        return machine_no, False, True


def search_record_waiting_machine() -> dict[str, list[str]]:
    """
    全設備を並列で確認し、
    記録待ち設備と通信失敗設備を返す。
    """
    record_waiting_machines = []
    communication_error_machines = []

    machines = config["machines"]

    with ThreadPoolExecutor(
        max_workers=min(len(machines), 10)
    ) as executor:

        futures = [
            executor.submit(
                check_record_waiting_machine,
                machine_no,
                machine_config,
            )
            for machine_no, machine_config in machines.items()
        ]

        for future in as_completed(futures):
            machine_no, is_record_waiting, has_communication_error = (
                future.result()
            )

            if has_communication_error:
                communication_error_machines.append(machine_no)
                continue

            if is_record_waiting:
                record_waiting_machines.append(machine_no)

    return {
        "record_waiting_machines": sorted(record_waiting_machines),
        "communication_error_machines": sorted(
            communication_error_machines
        ),
    }
```

---

## 18. JavaScript側は基本的に変更不要

Python側の戻り値を現在と同じ辞書構造にしているため、JavaScript側は基本的に変更する必要がありません。

```javascript
const result = await window.pywebview.api.get_record_waiting_machines();

const machineNos = result.record_waiting_machines;
const communicationErrorMachines = result.communication_error_machines;
```

Python内部の処理方法を直列から並列へ変えても、JavaScriptとのAPI仕様を変えずに済みます。

これは、内部実装を変更しても呼び出し側へ影響を与えない、よい設計です。

---

## 19. 実行時間の比較例

1台あたりのタイムアウトを3秒と仮定します。

| 電源OFF台数 | 直列処理 | 並列処理 |
|---:|---:|---:|
| 1台 | 約3秒 | 約3秒 |
| 2台 | 約6秒 | 約3秒前後 |
| 5台 | 約15秒 | 約3秒前後 |
| 10台 | 約30秒 | 約3秒前後 |

実際の処理時間は、次の条件によって変わります。

- PLC通信ライブラリのタイムアウト設定
- ネットワーク環境
- スレッド数
- Windows側のソケット処理
- PLC側の応答速度
- `kv_com.read_device_u()` の内部実装

---

## 20. kv_com側で確認すべき点

マルチスレッド化する前に、`kv_com.read_device_u()` が複数スレッドから同時に呼び出しても安全か確認する必要があります。

### 問題が起きにくい構造

関数を呼び出すたびに新しいソケットを作成している場合です。

```python
def read_device_u(ip_address, device):
    with socket.socket(...) as sock:
        sock.connect(...)
        sock.sendall(...)
        response = sock.recv(...)

    return response
```

この構造なら、それぞれのスレッドが独立したソケットを使うため、並列化しやすくなります。

### 注意が必要な構造

グローバルなソケットを複数処理で共有している場合です。

```python
global_socket.sendall(...)
response = global_socket.recv(...)
```

1つのソケットを複数スレッドで同時使用すると、送信と受信の対応関係が崩れる可能性があります。

現在の `kv_com` が関数ごとにソケットを作成する設計であれば、今回のマルチスレッド化を適用できる可能性が高いです。

---

## 21. 例外処理について

現在と同様に、次の形で通信失敗を捕まえています。

```python
except Exception as error:
```

この書き方なら、PLC通信内部で発生するさまざまな例外をまとめて捕まえられます。

例：

- `TimeoutError`
- `ConnectionError`
- `OSError`
- `socket.timeout`
- 通信応答の変換時に発生する例外

ただし、`Exception` は通信エラー以外のプログラムミスも捕まえます。

将来、`kv_com` が発生させる例外を明確にできた場合は、通信関連だけに限定する方法もあります。

```python
except (
    TimeoutError,
    ConnectionError,
    OSError,
) as error:
```

---

## 22. タイムアウト時間の短縮との組み合わせ

マルチスレッド化に加えて、PLC通信のタイムアウト時間を短くする方法もあります。

```python
sock.settimeout(2.0)
```

ただし、短くしすぎると次の問題が起きる可能性があります。

- 一時的なネットワーク遅延で通信エラーになる
- PLCが高負荷のときに応答を待てない
- 拠点間通信などで失敗が増える
- 稼働中の設備を電源OFF扱いしてしまう

おすすめの進め方は次のとおりです。

```text
1. 現在のタイムアウト値を確認する
2. マルチスレッド化だけで効果を測る
3. それでも遅い場合にタイムアウト値を調整する
```

---

## 23. Pingによる事前確認について

PLC通信前にPingを実行し、応答しない設備を除外する方法もあります。

しかし、次の注意点があります。

- PLCがPing応答を無効にしている場合がある
- Pingは通るがPLC通信ポートは使えない場合がある
- Pingにもタイムアウトがある
- PingとPLC通信の2回通信することになる
- Ping成功がPLC通信成功を保証しない

そのため、今回の用途では、Pingで事前確認するよりも、PLC通信そのものを並列化する方がシンプルです。

---

## 24. マルチスレッド化の注意点

### 24.1 結果の順番は保証されない

完了した設備から結果が返るため、設備番号順にはなりません。戻り値に `sorted()` を使って順番を安定させます。

### 24.2 共有データの書き換えに注意する

複数スレッドから同じリストや辞書を同時に書き換えると、複雑な問題が起きることがあります。

今回の構成では、各スレッドはタプルを返すだけです。リストへの追加は結果を受け取る側で行うため、比較的安全で分かりやすい構造です。

### 24.3 SQLite接続を共有しない

将来、各スレッド内でSQLiteへ保存する場合は、同じSQLite接続を複数スレッドで共有しない方が安全です。

### 24.4 GUIをスレッドから直接操作しない

Python側のスレッドからJavaScriptやpywebview画面を直接変更せず、各スレッドは結果だけ返します。すべての確認が終わってからAPIの戻り値としてJavaScriptへ渡します。

---

## 25. 導入時のテスト手順

### テスト1：全設備が通信可能

- エラーが発生しない
- 記録待ち設備が正しく1台返る
- JavaScript側の画面更新が正常に動く

### テスト2：1台だけ電源OFF

- アプリが異常終了しない
- 電源OFF設備が `communication_error_machines` に入る
- 記録待ち設備が1台なら処理を継続する

### テスト3：複数台を電源OFF

- 待ち時間が設備台数分だけ増えない
- 通信可能な設備の確認は正常に行われる
- 電源OFF設備がすべてエラー一覧に入る

### テスト4：全設備が電源OFF

- おおむね1回分のタイムアウト時間で処理が終わる
- `record_waiting_machines` が空になる
- JavaScript側で「記録待ち設備がありません」と表示される
- アプリ自体は終了しない

### テスト5：記録待ち設備が2台

- `record_waiting_machines` に2台入る
- JavaScript側で複数設備の警告が表示される
- 後続処理が中断される

---

## 26. 処理時間を測る方法

```python
from time import perf_counter

start_time = perf_counter()

result = search_record_waiting_machine()

elapsed_time = perf_counter() - start_time

print(f"検索時間: {elapsed_time:.2f}秒")
print(result)
```

直列版とマルチスレッド版で同じ条件を作り、処理時間を比較します。

```text
直列版検索時間: 15.24秒
並列版検索時間: 3.18秒
```

数値で比較すると、効果を客観的に確認できます。

---

## 27. 学習時のおすすめ順序

いきなり現在のアプリへ組み込まず、次の順序で学習すると理解しやすくなります。

### ステップ1：簡単な待ち処理を並列化する

```python
from concurrent.futures import ThreadPoolExecutor
from time import sleep


def task(name: str) -> str:
    print(f"{name} 開始")
    sleep(3)
    print(f"{name} 終了")
    return name


with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [
        executor.submit(task, "設備1"),
        executor.submit(task, "設備2"),
        executor.submit(task, "設備3"),
    ]

    for future in futures:
        print(future.result())
```

直列なら9秒かかる処理が、約3秒で終わることを確認します。

### ステップ2：as_completed()を使う

終了順に結果が返ることを確認します。

### ステップ3：1台確認関数を作る

実際のPLC通信を使わず、仮の関数で戻り値を確認します。

### ステップ4：PLC通信へ置き換える

最後に `kv_com.read_device_u()` を使用します。

この順序なら、問題が起きたときに、マルチスレッドの問題なのかPLC通信の問題なのかを切り分けやすくなります。

---

## 28. まとめ

現在の `search_record_waiting_machine()` は、設備を1台ずつ確認する直列処理です。

電源OFF設備が増えると、設備ごとの通信タイムアウトが順番に積み重なり、画面の応答が遅くなる可能性があります。

改善方法として、Python標準ライブラリの次の機能を使用できます。

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
```

マルチスレッド化のポイントは次のとおりです。

1. 設備1台分の処理を別関数へ分離する
2. `ThreadPoolExecutor` へ各設備の処理を登録する
3. `as_completed()` で完了した結果から受け取る
4. 通信失敗設備と記録待ち設備を分類する
5. 結果を `sorted()` して順番を安定させる
6. JavaScriptへ返す辞書構造は現在と同じにする

今回の処理はPLC通信の応答待ちが中心であるため、マルチスレッド化の効果が期待できます。

ただし、実装前には `kv_com.read_device_u()` が呼び出しごとに独立したソケットを使用しているか確認する必要があります。

現段階ですぐに改造せず、まず `ThreadPoolExecutor` の簡単なサンプルから学び、動作を理解してからアプリへ導入する進め方で問題ありません。
