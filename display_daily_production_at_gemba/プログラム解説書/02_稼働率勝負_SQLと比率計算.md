# 稼働率勝負 プログラム解説書 ② SQLite・勤務時間・比率計算

> 対象: `main(20261104-112801).py`。上段の**実データ処理**を重点解説。  
> DBスキーマ全体は添付されていないため、SQLから読み取れる列・条件のみ説明する。

## 1. データの流れ

```text
「結果表示」ボタン
   ↓ show_results()
基準日時を入力・検証
   ↓
先週の同じ日時 = 基準日時 - 7日
   ↓
get_operating_time() × 2 → 直近1時間の比率
   ↓
get_shift_start_datetime() × 2 → 勤務開始日時
   ↓
get_cumulative_operating_time() × 2 → 累積比率
   ↓
get_weekly_production() → 週間検査数
   ↓
ratio_specs / ratio_targets / result_photo_modes を更新
   ↓
アニメーション・写真・効果音
```

## 2. `date_hour` は「1時間の開始時刻」

ソースのSQLは `production_result.date_hour` と `operating_time_sec` を使う。例えば `2026-11-04 20:00` は、**20:00～20:59の1時間を表すレコード**として扱っている。したがって基準日時が20:00のとき、その勤務の累積対象も最初の1時間だけになる。

この前提は今回のアプリの集計仕様として重要。もしDBの時刻が「終了時刻」を表す設計なら集計範囲を見直す必要があるが、現在の説明は開始時刻としての運用に従う。

## 3. 日時入力の読み方

```python
now = datetime.now().replace(minute=0, second=0, microsecond=0)
date_str = simpledialog.askstring(...)
base_datetime = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
if base_datetime.minute != 0:
    raise ValueError
```

`datetime.now()` は現在日時、`replace()` は指定要素を置き換える。`strptime()` は文字列を日時へ変換。分が00でなければエラーにする。キャンセル時は `None` なので処理を終了する。

**補足:** `minute == 0` の検査はあるが、未来日時やDBの存在期間についての検査はない。

## 4. 先週の同時刻

```python
def get_previous_week_datetime(base_datetime):
    return base_datetime - timedelta(days=7)
```

例えば `2026-11-04 15:00` に対して `2026-10-28 15:00` を得る。曜日と時刻を揃えた比較。

## 5. 勤務開始の決定

```python
def get_shift_start_datetime(base_datetime):
    hour = base_datetime.hour
    if 8 <= hour <= 19:
        return base_datetime.replace(hour=8)
    if hour >= 20:
        return base_datetime.replace(hour=20)
    return (base_datetime - timedelta(days=1)).replace(hour=20)
```

| 基準日時の時刻 | 勤務 | 累積開始 |
|---|---|---|
| 08:00～19:59 | 昼勤 | 当日08:00 |
| 20:00～23:59 | 夜勤 | 当日20:00 |
| 00:00～07:59 | 夜勤 | 前日20:00 |

夜勤が日付をまたぐことに注意。`replace(hour=20)` は**分・秒をそのまま残す**が、このアプリでは入力時に分00を要求しているので、通常の呼び出しでは問題にならない。

## 6. 直近1時間のSQL

```python
def get_operating_time(target_datetime):
    date_hour = target_datetime.strftime("%Y-%m-%d %H:%M")
    with sqlite3.connect(DB_FILE) as conn:
        total_sec = conn.execute(
            """
            SELECT COALESCE(SUM(operating_time_sec), 0)
            FROM production_result
            WHERE date_hour = ?
            """,
            (date_hour,),
        ).fetchone()[0]
    return total_sec
```

- `sqlite3.connect(DB_FILE)`：DBを開く。
- `with ... as conn`：処理の終了時にトランザクションを管理。**接続のclose自体を保証する構文ではない**点に注意。
- `SUM(...)`：対象レコードの稼働秒数を合計。
- `COALESCE(..., 0)`：合計がNULLなら0にする。
- `WHERE date_hour = ?`：指定した1時間のレコードに限定。
- `(date_hour,)`：1要素タプル。カンマが必要。
- `?`：SQLパラメータ。文字列連結より安全で、引用符の処理も任せられる。
- `fetchone()[0]`：1行取得し、その1列目を取り出す。

**ここで取得しているのは「秒数」であり、まだパーセントではない。**

## 7. 累積時間のSQL

```sql
SELECT COALESCE(SUM(operating_time_sec), 0)
FROM production_result
WHERE date_hour >= ? AND date_hour <= ?
```

開始日時から基準日時まで、両端を含めて合計する。1時間単位の開始時刻を格納しているため、終了側の `<=` によって基準時刻の1時間も含む。

### 集計範囲の例

| 基準日時 | 直近1時間 | 勤務累積 |
|---|---|---|
| 11/04 08:00 | 08:00～08:59 | 08:00～08:59 |
| 11/04 15:00 | 15:00～15:59 | 08:00～15:59 |
| 11/04 20:00 | 20:00～20:59 | 20:00～20:59 |
| 11/04 23:00 | 23:00～23:59 | 20:00～23:59 |
| 11/05 02:00 | 02:00～02:59 | 前日20:00～02:59 |

**08:00と20:00は直近と累積が一致して正常。** 今回の「上下のグラフが同じ」現象は、この仕様で説明できる。

## 8. 比率の式を読み解く

直近1時間:

```python
this_week_sec = get_operating_time(base_datetime)
last_week_sec = get_operating_time(previous_week_datetime)
total_sec = this_week_sec + last_week_sec
this_week_rate = round(this_week_sec / total_sec * 100)
last_week_rate = 100 - this_week_rate
ratio_targets[0] = this_week_sec / total_sec
```

例えば今週3,600秒、先週2,400秒なら、今週60%、先週40%。

$$
\text{今週比率(\%)} = \frac{\text{今週稼働秒数}}{\text{今週稼働秒数}+\text{先週稼働秒数}}\times100
$$

`ratio_targets[0]` は描画用の0～1の比率（例: 0.6）、`this_week_rate` は文字表示用の整数（例: 60）。**描画用と文字用は別の変数**。

累積は同じ式を、勤務開始からの合計秒数に適用する。

```python
this_week_total = get_cumulative_operating_time(this_week_start, base_datetime)
last_week_total = get_cumulative_operating_time(last_week_start, previous_week_datetime)
cumulative_total = this_week_total + last_week_total
ratio_targets[1] = this_week_total / cumulative_total
```

**分母が0の場合はエラー表示して中断**する。0除算を避けるため。

### 丸めの影響

`round()` はPythonの丸め（ちょうど `.5` のとき偶数側）を使う。表示は整数%だが、棒の長さは丸め前の比率で決まるため、文字と棒が厳密に同じ精度ではない。写真判定も整数の `this_week_rate` を使う。

## 9. 週間検査数の集計

`get_weekly_production(base_datetime)` は基準日時を含む週の月曜日00:00を求め、月～土の6日について昼勤・夜勤の件数をそれぞれ集計する。

```python
monday = (
    base_datetime - timedelta(days=base_datetime.weekday())
).replace(hour=0, minute=0, second=0, microsecond=0)
```

`weekday()` は月曜0、火曜1、…、日曜6。日数を戻して月曜日を求める。

```text
月曜昼勤 08:00 <= date_hour < 20:00
月曜夜勤 20:00 <= date_hour < 火曜08:00
...
土曜夜勤 20:00 <= date_hour < 日曜08:00
```

SQLの対象列は `production_num_1hour`。昼夜各6回、合計12回の集計SQLを実行する。**週間検査数は稼働秒数ではなく生産数**。現状はこの分かりやすい実装で十分。

### なぜ週間集計は `<`、累積は `<=` なのか

週間の昼勤は `[08:00, 20:00)` の**半開区間**で、20:00を夜勤へ振り分けるため。累積は「基準日時の時間帯を含める」ため終了側を `<=` にする。どちらも仕様に沿っている。

## 10. `show_results()` の更新順序

1. 入力・検証。
2. 直近1時間のSQLと比率計算。
3. `ratio_specs[0]` と `ratio_targets[0]` を更新。
4. 累積のSQLと比率計算。
5. `ratio_specs[1]` と `ratio_targets[1]` を更新。
6. `update_weekly_table()` を実行。
7. 写真表情を決める。
8. `results_visible=True`、タイトル更新、ドラムロール、アニメーション開始。

**保守上の注意:** 途中のDBエラーや0件エラーで中断すると、`ratio_specs[0]` など一部の状態だけ更新済みになり得る。画面を更新する直前に全計算を完了する設計ならより安全だが、現状の説明としては「段階的に更新している」と理解する。

## 11. 画面に出る「今週・先週」と「昼勤・夜勤」

ここは混同しやすい。**棒グラフの左右は今週／先週の比較**であり、昼勤／夜勤の稼働秒数を直接比較しているわけではない。基準日時が属する勤務帯（昼勤または夜勤）について、今週と先週の同じ時刻・勤務開始からの実績を比較する。スタッフ写真は、その比較結果に応じて昼勤・夜勤の表情を切り替える演出。

## 12. 理解度チェック

1. `2026-11-04 20:00` で上下の比率が同じなのはなぜ？
2. `get_operating_time()` は何を返す？
3. 週間集計で終了側が `<` なのはなぜ？
4. `ratio_targets[1]` は整数%か、0～1の小数か？
5. 夜勤の02:00に対して、勤務開始はいつ？

**答え:** 1. 夜勤開始の最初の1時間だけが累積対象だから。2. 指定時間帯の稼働秒数の合計。3. 次の勤務帯との重複を防ぐため。4. 小数。5. 前日20:00。
