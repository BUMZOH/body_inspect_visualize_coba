# SQLiteでNG詳細テーブルを保存する方法

## 概要

NG詳細テーブルをSQLiteへ保存する際、

- JSONで1カラム保存する方法
- カラムを個別に持つ方法

を比較し、後者を採用した理由をまとめます。

---

## 対象テーブル

| 検査内容 | 全長 | 外径 | 内径 | 穴径 | その他 |
|----------|------|------|------|------|--------|
| 初回検査 | 6 | 2 | 3 | 0 | 0 |
| 再検査 | 1 | 1 | 0 | 0 | 0 |

---

## SQLiteテーブル

```sql
CREATE TABLE IF NOT EXISTS inspection_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    full_length_1st INTEGER,
    outer_diameter_1st INTEGER,
    inner_diameter_1st INTEGER,
    hole_diameter_1st INTEGER,
    other_1st INTEGER,

    full_length_2nd INTEGER,
    outer_diameter_2nd INTEGER,
    inner_diameter_2nd INTEGER,
    hole_diameter_2nd INTEGER,
    other_2nd INTEGER
);
```

---

## JavaScript

```javascript
function getNgCountDetail() {

    const table = document.getElementById("ng_count_detail");

    const first = table.rows[1].cells;
    const second = table.rows[2].cells;

    return {
        full_length_1st: Number(first[1].textContent),
        outer_diameter_1st: Number(first[2].textContent),
        inner_diameter_1st: Number(first[3].textContent),
        hole_diameter_1st: Number(first[4].textContent),
        other_1st: Number(first[5].textContent),

        full_length_2nd: Number(second[1].textContent),
        outer_diameter_2nd: Number(second[2].textContent),
        inner_diameter_2nd: Number(second[3].textContent),
        hole_diameter_2nd: Number(second[4].textContent),
        other_2nd: Number(second[5].textContent),
    };
}
```

登録処理

```javascript
async function saveData() {

    const ngCountDetail = getNgCountDetail();

    await window.pywebview.api.insert_inspection_data(
        ngCountDetail
    );
}
```

---

## AppAPI

```python
class AppAPI:

    def insert_inspection_data(
        self,
        ng_count_detail
    ):

        insert_inspection_data(
            ng_count_detail
        )

        return {"ok": True}
```

---

## Python(SQLite登録)

```python
import sqlite3

DB_FILE = "inspection.db"


def insert_inspection_data(data):

    with sqlite3.connect(DB_FILE) as conn:

        conn.execute(
            '''
            INSERT INTO inspection_record (

                full_length_1st,
                outer_diameter_1st,
                inner_diameter_1st,
                hole_diameter_1st,
                other_1st,

                full_length_2nd,
                outer_diameter_2nd,
                inner_diameter_2nd,
                hole_diameter_2nd,
                other_2nd

            ) VALUES (

                ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?

            )
            ''',
            (

                data["full_length_1st"],
                data["outer_diameter_1st"],
                data["inner_diameter_1st"],
                data["hole_diameter_1st"],
                data["other_1st"],

                data["full_length_2nd"],
                data["outer_diameter_2nd"],
                data["inner_diameter_2nd"],
                data["hole_diameter_2nd"],
                data["other_2nd"],

            )
        )
```

---

## SQL集計例

```sql
SELECT
    SUM(full_length_1st)
FROM inspection_record;
```

```sql
SELECT
    SUM(outer_diameter_1st)
FROM inspection_record;
```

```sql
SELECT
    SUM(full_length_1st),
    SUM(full_length_2nd)
FROM inspection_record;
```

---

## 正規化しすぎる問題

理論上はさらに正規化できます。

しかし、

- JOINが増える
- SQLが複雑になる
- 保守しづらい

という問題があります。

いわゆる「リレーション地獄」です。

---

## 今回の結論

今回の設計は冗長です。

```text
full_length_1st
outer_diameter_1st
...
full_length_2nd
outer_diameter_2nd
...
```

しかし、

- SQL集計しやすい
- グラフ化しやすい
- 分析しやすい
- PythonでJSON解析不要

という大きなメリットがあります。

工場の品質管理システムでは非常に実用的な設計です。
