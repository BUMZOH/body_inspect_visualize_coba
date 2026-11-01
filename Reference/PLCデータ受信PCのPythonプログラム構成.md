# PLCデータ受信PCのPythonプログラム構成

## 1. 概要

機械のPLCと通信するPCで、以下の2つの処理を行う構成を考える。

1. 約5分に1回、PLCからデータを受信してSQLiteデータベースへ保存する
2. 他のPCからHTTPリクエストを受けた場合、Flaskを使用してSQLiteのデータを返す

この場合は、**PLC受信プログラムとFlaskアプリを別々のPythonプログラムとして動作させる構成を推奨する。**

FlaskをPLC受信プログラムの別スレッドとして動作させることも可能だが、今回の用途ではプログラムを分離した方が構成が単純で、保守や障害対応もしやすい。

---

## 2. 推奨構成

```text
                    ┌──────────────┐
                    │     PLC      │
                    └──────┬───────┘
                           │
                           │ PLC通信
                           ▼
              ┌────────────────────────┐
              │ plc_data_receiver.py   │
              │                        │
              │ 約5分ごとにPLCから取得 │
              │          ↓             │
              │ SQLiteへINSERT         │
              └───────────┬────────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │   SQLite DB   │
                  │               │
                  │ production.db │
                  └───────┬───────┘
                          │
                          │ SELECT
                          ▼
                  ┌────────────────┐
                  │ flask_server.py│
                  │                │
                  │ HTTP API       │
                  └───────┬────────┘
                          │
                 HTTP GET │
                          ▼
                 ┌─────────────────┐
                 │ 他のPC          │
                 │ Dashboard等     │
                 └─────────────────┘
```

重要なポイントは、**PLC受信プログラムとFlaskアプリが直接通信しないこと**である。

SQLiteデータベースを両者の境界として使用する。

```text
PLC受信
    │
    ▼
 SQLite
    ▲
    │
Flask API
```

このようにすると、それぞれのプログラムの役割が明確になる。

---

## 3. PLC受信プログラムの役割

`plc_data_receiver.py` はPLCからのデータ収集だけを担当する。

```text
PLCと通信
    ↓
データを受信
    ↓
SQLiteへ保存
```

例えば、以下のような処理になる。

```python
while True:
    data = receive_plc_data()
    insert_data(data)

    time.sleep(300)
```

実際には通信失敗時の例外処理やログ出力なども追加する。

このプログラムはHTTP通信について考える必要がない。

---

## 4. Flaskアプリの役割

`flask_server.py` はHTTPによるデータ提供だけを担当する。

```text
HTTPリクエストを待つ
    ↓
SQLiteをSELECT
    ↓
JSON等で返す
```

例えば、

```text
GET /api/production
GET /api/status
GET /api/alarm
```

などのAPIを用意する。

Flask側はPLCと直接通信せず、SQLiteに保存済みのデータだけを参照する。

---

## 5. Flaskを別スレッドにする構成

1つのPythonプログラム内でFlaskを別スレッドとして動作させることもできる。

例えば以下のような構成である。

```python
import threading


def run_flask():
    app.run(host="0.0.0.0", port=5000)


thread = threading.Thread(target=run_flask, daemon=True)
thread.start()

while True:
    receive_plc_data()
```

この場合は、

```text
1つのPythonプロセス
├─ メインスレッド → PLC通信
└─ Flaskスレッド → HTTP通信
```

となる。

技術的には問題ないが、今回の用途では積極的に採用するメリットは少ない。

---

## 6. 別プログラムにするメリット

### 6.1 役割が明確になる

PLC受信側は、

```text
PLC → SQLite
```

だけを考えればよい。

Flask側は、

```text
SQLite → HTTP
```

だけを考えればよい。

それぞれのプログラムが小さくなり、理解しやすい。

---

### 6.2 障害を分離できる

例えばPLC受信プログラムが異常終了しても、

```text
plc_data_receiver.py
        ↓
      停止

flask_server.py
        ↓
     正常稼働
```

という状態にできる。

最新データは追加されないが、Flaskから過去のデータを取得することは可能である。

逆にFlask側で問題が発生しても、

```text
PLC
 ↓
plc_data_receiver.py
 ↓
SQLite
```

は動作し続ける。

そのため、**HTTPサーバー側のトラブルによってPLCのデータ収集まで停止することを防げる。**

工場設備のデータ収集では、この障害分離は大きなメリットになる。

---

### 6.3 個別に再起動できる

例えばFlaskアプリだけを修正した場合、

```text
flask_server.py
```

だけを再起動できる。

PLC受信プログラムを停止する必要はない。

逆にPLC通信処理を変更した場合も、Flask側を停止する必要はない。

---

### 6.4 ログを分離できる

例えば、

```text
logs/
├─ plc_receiver.log
└─ flask_server.log
```

とすることができる。

PLC通信の問題なのか、HTTP通信の問題なのかを判断しやすくなる。

---

## 7. SQLiteを共有して問題ないか

今回の用途では、

```text
PLC受信プログラム
    ↓
INSERT
    ↓
SQLite
    ↑
SELECT
    ↑
Flask
```

という使い方になる。

基本的には、

- PLC受信側：書き込み
- Flask側：読み取り

という役割になる。

さらにPLCからの書き込みは約5分に1回程度なので、SQLiteとしてはかなり軽い使用方法である。

そのため、今回の規模であればSQLiteを共有データベースとして使用する構成は適している。

---

## 8. SQLiteのWALモード

SQLiteでは、必要に応じてWAL（Write-Ahead Logging）モードを使用できる。

```python
conn = sqlite3.connect(DB_FILE)

conn.execute("PRAGMA journal_mode=WAL")
```

WALモードでは、読み取りと書き込みを並行して行いやすくなる。

今回のような、

```text
PLC → INSERT
         ↓
       SQLite
         ↑
Flask → SELECT
```

という構成と相性がよい。

ただし、約5分に1回のINSERT程度であれば負荷は非常に小さい。

最初から必要以上に複雑にせず、通常構成で運用して問題がある場合にWALモードを検討する方法でもよい。

---

## 9. 推奨ファイル構成

最初は以下のようなシンプルな構成で十分である。

```text
plc_data_server/
│
├─ plc_data_receiver.py
├─ flask_server.py
│
├─ database.py
├─ config.json
│
└─ data/
   └─ production.db
```

### plc_data_receiver.py

PLC通信を担当する。

```text
PLC
 ↓
plc_data_receiver.py
 ↓
database.py
 ↓
SQLite INSERT
```

### flask_server.py

HTTP APIを担当する。

```text
HTTP Request
 ↓
flask_server.py
 ↓
database.py
 ↓
SQLite SELECT
```

### database.py

SQLiteへのアクセス処理を共通化する。

例えば、

```python
def insert_data(data):
    ...


def select_data(start_datetime, end_datetime):
    ...
```

程度のシンプルな関数構成でよい。

今回の規模では、必要以上にクラス化や階層化を行わず、KISSを優先する。

---

## 10. PC起動時の構成

PC起動時には2つのプログラムをそれぞれ起動する。

```text
PC起動
  │
  ├─ plc_data_receiver.py
  │
  └─ flask_server.py
```

それぞれ独立したPythonプロセスとして動作させる。

将来的にはWindowsのタスクスケジューラなどを利用して自動起動させることもできる。

---

## 11. 将来の拡張

この構成にしておけば、将来的にAPIを追加する場合もPLC通信側への影響を小さくできる。

例えば、

```text
                  PLC
                   │
                   ▼
        ┌────────────────────┐
        │ plc_data_receiver  │
        └─────────┬──────────┘
                  │ INSERT
                  ▼
          ┌───────────────┐
          │    SQLite     │
          └───────┬───────┘
                  │ SELECT
                  ▼
        ┌────────────────────┐
        │    Flask Server    │
        │                    │
        │ /api/production    │
        │ /api/status        │
        │ /api/alarm         │
        └─────────┬──────────┘
                  │ HTTP
        ──────────┼────────────
                  │
          ┌───────┴───────┐
          ▼               ▼
       PC-A             PC-B
    Dashboard        Dashboard
```

PLCの種類や取得データが変更された場合は主にPLC受信側を修正し、HTTP APIの仕様を変更する場合は主にFlask側を修正する、という分担が可能になる。

---

## 12. 結論

今回の用途では、以下の構成を推奨する。

```text
PLC
 ↓
plc_data_receiver.py
 ↓
SQLite
 ↑
flask_server.py
 ↑
HTTP
 ↑
他のPC
```

### 方針

- PLC受信プログラムとFlaskアプリは別々のPythonプログラムにする
- 2つのプログラムはSQLiteを介してデータを共有する
- PLC受信側はINSERTを担当する
- Flask側はSELECTとHTTP応答を担当する
- DBアクセス処理だけ必要に応じて`database.py`へ共通化する
- FlaskをPLC受信プログラムの別スレッドとして組み込まない
- 必要以上に複雑な構造にせずKISSを優先する

この構成では、**PLCからのデータ収集**と**他PCへのデータ提供**を明確に分離できる。

片方に障害や修正が発生しても、もう片方への影響を小さくできるため、工場設備のデータ収集PCとして保守しやすく、安定した構成になる。
