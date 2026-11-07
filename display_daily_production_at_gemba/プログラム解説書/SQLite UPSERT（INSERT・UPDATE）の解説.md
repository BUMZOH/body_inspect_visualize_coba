# SQLite UPSERT（INSERT・UPDATE）の解説

## 1. 今回の目的

PLCから定期的に受信する生産実績を、SQLiteの `production_result` テーブルに登録します。

- 同じ **号機番号（`machine_no`）と日時（`date_hour`）** の組み合わせがなければ、新規登録（INSERT）する。
- 同じ組み合わせがすでにあれば、稼働秒数と生産数を上書き（UPDATE）する。
- 同じ日時のデータを繰り返し受信しても、重複行を作らない。

この「なければINSERT、あればUPDATE」を **UPSERT** と呼びます。

## 2. 使用するSQL

```python
UPSERT_SQL = """
INSERT INTO production_result (
    machine_no,
    date_hour,
    operating_time_sec,
    production_num_1hour
)
VALUES (?, ?, ?, ?)
ON CONFLICT(machine_no, date_hour) DO UPDATE SET
    operating_time_sec = excluded.operating_time_sec,
    production_num_1hour = excluded.production_num_1hour
"""
```

### 2.1 `INSERT INTO ... VALUES (?, ?, ?, ?)`

```sql
INSERT INTO production_result (
    machine_no,
    date_hour,
    operating_time_sec,
    production_num_1hour
)
VALUES (?, ?, ?, ?)
```

まず、4つの値を新しいレコードとして登録しようとします。`?` はPythonの `sqlite3` から渡す値を入れるプレースホルダーです。値を文字列連結でSQLに埋め込まず、安全に渡せます。

### 2.2 `ON CONFLICT(machine_no, date_hour)`

```sql
ON CONFLICT(machine_no, date_hour)
```

`production_result` の主キーは、次の **複合主キー** です。

```sql
PRIMARY KEY (machine_no, date_hour)
```

`machine_no` と `date_hour` の組み合わせがすでに存在し、INSERTすると一意制約に違反する場合、`ON CONFLICT` の後に書いた処理へ進みます。

| 既存のデータ | 新しいデータ | 判定 |
|---|---|---|
| 412号機、2026-09-01 12:00 | 412号機、2026-09-01 12:00 | 重複 → UPDATE |
| 412号機、2026-09-01 12:00 | 413号機、2026-09-01 12:00 | 別の号機 → INSERT |
| 412号機、2026-09-01 12:00 | 412号機、2026-09-01 13:00 | 別の日時 → INSERT |

**注意：** `ON CONFLICT` は、単に値が似ているかを比較するのではなく、主キーやUNIQUE制約への違反を検出します。

### 2.3 `DO UPDATE SET`

```sql
DO UPDATE SET
```

重複が発生したとき、既存レコードを更新する指定です。実際にどのカラムを更新するかは、続く `SET` で指定します。

### 2.4 `excluded` の意味

```sql
operating_time_sec = excluded.operating_time_sec,
production_num_1hour = excluded.production_num_1hour
```

`excluded` はSQLiteのUPSERT構文で使う特別な名前です。**今回INSERTしようとした新しいレコードの値**を参照します。自分で作るテーブルでも、Pythonの変数でもありません。

| SQLの部分 | 意味 |
|---|---|
| 左辺 `operating_time_sec` | 更新対象となる既存レコードの稼働秒数 |
| 右辺 `excluded.operating_time_sec` | 今回INSERTしようとした新しい稼働秒数 |
| 左辺 `production_num_1hour` | 更新対象となる既存レコードの生産数 |
| 右辺 `excluded.production_num_1hour` | 今回INSERTしようとした新しい生産数 |

つまり、右辺の新しい値を左辺の既存カラムへ代入します。`machine_no` と `date_hour` はレコードを特定するキーなので、このSQLでは更新しません。

## 3. 実際のデータで確認

PLC 412号機の `2026-09-01 12:00` について、最初に次のデータが登録されていたとします。

| machine_no | date_hour | operating_time_sec | production_num_1hour |
|---:|---|---:|---:|
| 412 | 2026-09-01 12:00 | 3400 | 1800 |

次の受信で、同じ号機・日時の生産数が **1900** になりました。

| machine_no | date_hour | operating_time_sec | production_num_1hour |
|---:|---|---:|---:|
| 412 | 2026-09-01 12:00 | 3400 | 1900 |

処理の流れは以下です。

1. `INSERT` を試みる。
2. `(412, '2026-09-01 12:00')` がすでに存在するので、複合主キーの重複を検出する。
3. `ON CONFLICT ... DO UPDATE SET` が実行される。
4. `production_num_1hour` を `excluded.production_num_1hour`、つまり **1900** に更新する。
5. 行数は増えず、既存レコードが更新される。

この動作は、実際のPLCダミーデータを使った **1800 → 1900** の更新テストでも確認できました。

Python風に表すと、概念的には次の処理です。

```python
if 同じ号機と日時のレコードが存在する:
    稼働秒数と生産数を更新する
else:
    新しいレコードを追加する
```

実際には、この判定と登録・更新をSQLiteが **1つのSQL文** で処理します。

## 4. `INSERT OR REPLACE` ではダメなのか？

SQLiteでは、次のようにもっと短く書けます。

```sql
INSERT OR REPLACE INTO production_result
    (machine_no, date_hour, operating_time_sec, production_num_1hour)
VALUES (?, ?, ?, ?)
```

ただし、**`REPLACE` は `UPDATE` ではありません。** 主キーやUNIQUE制約が衝突した場合、基本的には衝突する既存レコードを **DELETEしてからINSERT** します。

| 比較 | UPSERT (`DO UPDATE`) | `INSERT OR REPLACE` |
|---|---|---|
| 新しいキー | INSERT | INSERT |
| 既存キー | 既存行をUPDATE | 既存行を削除してINSERT |
| 既存行の同一性 | 維持しやすい | 作り直される |
| 外部キーへの影響 | 通常のUPDATEとして扱われる | DELETEに伴う動作が起き得る |
| トリガー | UPDATE側の処理 | DELETE/INSERT側の処理（条件による） |
| 省略したカラム | 既存の値を維持できる | 新規INSERT時の値・デフォルトに置き換わり得る |

### なぜ今回 `INSERT OR REPLACE` を使わないのか

現在の生産実績テーブルでは結果が同じに見える場合もありますが、将来テーブルに別のカラムや外部キー参照が増えると、削除して作り直す方式は予期しない影響を及ぼす可能性があります。

今回の目的は、**同じレコードの稼働秒数と生産数だけを更新すること**です。その意図を正確に表すのは `ON CONFLICT ... DO UPDATE` です。

> **覚え方：** `UPSERT` は「既存行を更新」、`INSERT OR REPLACE` は「既存行を置き換え（削除＋挿入）」。

## 5. SQLをコンパクトに書くなら

動作を変えずに、カラム名の並べ方だけ短くできます。

```python
UPSERT_SQL = """
INSERT INTO production_result
    (machine_no, date_hour, operating_time_sec, production_num_1hour)
VALUES (?, ?, ?, ?)
ON CONFLICT(machine_no, date_hour) DO UPDATE SET
    operating_time_sec = excluded.operating_time_sec,
    production_num_1hour = excluded.production_num_1hour
"""
```

元のSQLと動作はまったく同じです。好みの読みやすさで選んで構いません。

## 6. 他のDBでも使える？

UPSERTという考え方はSQLite専用ではありません。ただし構文はDB製品によって異なります。

- **SQLite（3.24.0以降）**：`ON CONFLICT ... DO UPDATE`
- **PostgreSQL**：`ON CONFLICT ... DO UPDATE`（ほぼ同じ構文）
- **MySQL**：`ON DUPLICATE KEY UPDATE`
- **SQL Server**：`MERGE`、またはUPDATEとINSERTを組み合わせた実装など

## 7. 今回の結論

**現在の `UPSERT_SQL` をそのまま採用するのがおすすめです。**

- 1つのSQL文で「なければINSERT、あればUPDATE」を実現できる。
- 複合主キー `(machine_no, date_hour)` によって、同じ日時の重複登録を防げる。
- `excluded` で、今回PLCから受信した新しい値を参照できる。
- `INSERT OR REPLACE` のように既存レコードを削除しない。
- 実機テストで新規登録、重複防止、値の更新が確認できている。

**SQLが少し長くても、Python側で存在確認・INSERT・UPDATEを別々に書くより、処理全体はシンプルです。**

---

*対象：`insert_prod_data_from_plc.py` の `UPSERT_SQL`／SQLite `production_result` テーブル*
