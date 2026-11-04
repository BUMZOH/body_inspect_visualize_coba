# 稼働率勝負 プログラム解説書 ③ Tkinter画面・アニメーション・写真切り替え

> 対象: `main(20261104-112801).py`。画面の作り方とイベント駆動の動作を解説。

## 1. 画面の階層

```text
root (tk.Tk)
└─ main (Frame)
   ├─ head (row=0) : タイトル、結果表示、メンバ入替
   ├─ top  (row=1)
   │  ├─ day_group   : 昼勤6人の写真＋Combobox
   │  ├─ center      : 比率グラフ2本、週間検査数
   │  └─ night_group : 夜勤6人の写真＋Combobox
   ├─ 本日の生産状況 (row=2)
   └─ bottom (row=3)
      ├─ left : 実績/目標/達成率/進捗の表、目標入力
      ├─ mid  : 進捗グラフ2本、号機別生産数
      └─ bot_area : ロボットGIF
```

`create_main_layout()` が画面の大枠を作り、`create_header()`、`create_top_panel()`、`create_bottom_panel()` に処理を任せる。大きな関数を分割することで、どの画面を修正するか探しやすい。

## 2. `grid()` と `pack()` の役割

```python
main.grid_rowconfigure(1, weight=50)
main.grid_rowconfigure(3, weight=50)
```

余った縦方向のスペースを上段・下段へ配分する。`grid_columnconfigure(1, weight=1)` は中央列に余り幅を配る。`sticky="nsew"` はセルの上下左右いっぱいに伸ばす。

```python
row.pack(fill="x")
c.pack(side="left", fill="x", expand=True)
```

`fill="x"` は横方向に伸ばし、`expand=True` は余りスペースの割り当てを受ける。`pack()` は単純な横並び・縦積みに向いている。

```python
card.grid(row=i // 3, column=i % 3)
```

6人の写真を3列×2行に配置。`//` は整数除算、`%` は余り。`i=4` なら `row=1, column=1`。

`grid_propagate(False)` はカードの指定サイズを子部品の要求サイズで変えないために使用。`pack_propagate(False)` も同様の考え方。

## 3. `label()` と `create_table_cell()`

```python
def label(parent, text="", size=16, bold=False, fg=TEXT, bg=PANEL, **kwargs):
    return tk.Label(parent, text=text,
                    font=(FONT, size, "bold" if bold else "normal"),
                    fg=fg, bg=bg, **kwargs)
```

共通のフォント・色を使うための小さなヘルパー。`**kwargs` は追加のキーワード引数をそのままTk Labelへ渡す。例えば `label(..., anchor="w")` のような指定を可能にする。

`create_table_cell()` はLabelを作るだけでなく、`grid()` に配置して、そのLabelを返す。返されたWidgetを保存しておけば、後から `configure(text=...)` で更新できる。

**読み方のコツ:** `create_...` は生成、`draw_...` は描画、`update_...` は既存Widgetの更新、`animate_...` は時間をかけた変化を表す命名。

## 4. スタッフカードの作成

`create_staff_group(parent, title, title_color, shift)` は昼勤または夜勤の6人分を生成する。JSONの `STAFF_INFO[shift][i]` から名前を取り、`STAFF_INFO["staff"][staff_name]` から画像のベース名を得る。

```python
box.combos = []
box.photos = []
```

`box` はTk Frameだが、ここに独自の属性 `combos` と `photos` を追加している。`combos[i]` はi番目のCombobox、`photos[i]` は対応する画像Label。**同じ順番で追加するため `zip()` で対応付けられる**。

```python
box.combos.append(combo)
box.photos.append(pic)
```

写真Labelを`photos`に保存するのは、結果発表時に画像をまとめて切り替えるため。

## 5. 写真を表示する `load_photo()`

1. Pillowが利用可能で、画像パスが存在するか確認。
2. `Image.open(path).convert("RGB")` で読み込み。
3. `thumbnail(size, Image.Resampling.LANCZOS)` で縦横比を保って縮小。
4. 白いキャンバスに中央配置。
5. `ImageTk.PhotoImage(canvas)` に変換してTkinterで表示可能にする。

```python
pic.configure(image=photo)
pic.image = photo
```

**`pic.image = photo` が重要。** Tkinterの画像表示はPython側で画像オブジェクトへの参照がなくなると消えることがある。Labelに属性として保持して寿命を確保している。

画像がない場合は `PHOTO` と表示する。`NAME` は未選択の特別な値として扱う。

## 6. Combobox変更イベントとクロージャ

```python
def change_staff(event, pic=pic):
    combo = event.widget
    name = combo.get()
    ...

combo.bind("<<ComboboxSelected>>", change_staff)
```

`event.widget` はイベントが発生したCombobox。`combo.get()` は選択中の名前。`pic=pic` は**関数定義時の画像Labelをデフォルト引数へ固定**するための工夫。これがないとループ内で作ったイベント関数が意図しない写真Labelを参照する可能性がある。

### `swap_staff()` と `zip()`

```python
for day_combo, night_combo in zip(day_group.combos, night_group.combos):
    day_name = day_combo.get()
    night_name = night_combo.get()
    day_combo.set(night_name)
    night_combo.set(day_name)
    day_combo.event_generate("<<ComboboxSelected>>")
    night_combo.event_generate("<<ComboboxSelected>>")
```

`zip()` は昼勤と夜勤の同じ位置のComboboxをペアで取り出す。`.set()` で名前を交換し、`event_generate()` で写真更新イベントを明示的に発生させる。`.set()` だけでは選択イベントが自動で発生するとは限らないため。

**注意:** このイベント内の `change_staff()` は常に `_normal.png` を読み込む。結果発表後にメンバーを変更・入替すると、該当写真がnormalへ戻る。これは現行コードの動作であり、今後の改善候補。

## 7. 結果発表時の写真切り替え

`show_results()` の末尾で、**直近1時間の整数%** と基準日時の勤務帯から `result_photo_modes` を決める。

```python
is_day_shift = 8 <= base_datetime.hour < 20
if this_week_rate >= 60:
    result_photo_modes = ("smile", "sad") if is_day_shift else ("sad", "smile")
elif this_week_rate <= 40:
    result_photo_modes = ("sad", "smile") if is_day_shift else ("smile", "sad")
else:
    result_photo_modes = ("normal", "normal")
```

タプルは `(昼勤, 夜勤)` の順番。

| 今週の直近1時間比率 | 昼勤基準時 | 夜勤基準時 |
|---|---|---|
| 60%以上 | 昼smile・夜sad | 昼sad・夜smile |
| 40%以下 | 昼sad・夜smile | 昼smile・夜sad |
| 41～59% | 両方normal | 両方normal |

`update_staff_photos(group, mode)` は `zip(group.combos, group.photos)` で選択名と写真Labelを組にし、`{base_name}_{mode}.png` を読み込んで差し替える。**Comboboxの名前は変更しない。**

写真が切り替わるタイミングは、`show_results()` の直後ではなく `animate_ratio_bars()` が終了した時。

## 8. 横棒グラフの描画

`ratio_canvases` は2本のCanvasのリスト。インデックス0は直近1時間、1は累積。

```python
canvas = ratio_canvases[index]
canvas.delete("all")
w, h = canvas.winfo_width(), canvas.winfo_height()
split = w * animated_ratios[index]
canvas.create_rectangle(0, 0, split, h, fill=DAY, outline="")
canvas.create_rectangle(split, 0, w, h, fill=NIGHT, outline="")
```

`animated_ratios[index]` は0～1の数。例えば0.6なら横幅の60%を左側に描き、残り40%を右側に描く。色定数 `DAY` / `NIGHT` は**棒の左右の色**で、左右のラベルは「今週」「先週」。色名だけで昼勤・夜勤の比較と誤解しないよう注意。

`show_percentage=True` のときだけ、`ratio_specs` の整数%をCanvas上に文字で描く。アニメーション中はパーセント表示を出さず、最後に表示する。

## 9. アニメーションの核心 `root.after()`

```python
def animate_ratio_bars(step=0):
    total_steps = 36
    if step >= total_steps:
        # 最終描画、写真切り替え、効果音
        return
    ...
    root.after(70, animate_ratio_bars, step + 1)
```

`root.after(70, ...)` は**70ミリ秒後に関数を1回呼ぶよう予約**する。`time.sleep()` と違いTkinterの画面更新を止めにくい。36ステップ×70msなので、待ち時間の目安は約2.52秒（描画負荷などで前後する）。

### 動きの計算

```python
progress = step / total_steps
ease = 1 - (1 - progress) ** 3
wobble = math.sin(step * 0.65) * 0.30 * (1 - progress ** 3)
animated_ratios[i] = 0.5 + (target - 0.5) * ease + wobble
animated_ratios[i] = max(0.02, min(0.98, animated_ratios[i]))
```

- `progress`：進行度（0→約1）。
- `ease`：終盤ほど動きがゆっくりになる補間。
- `wobble`：正弦波を使った揺れ。終了に近づくほど小さくなる。
- `max/min`：アニメーション中の比率を2～98%に制限し、棒が消えないようにする。

終了時は `animated_ratios[i] = ratio_targets[i]` として**正確な目標比率**に戻す。この最終代入は2～98%の制限を受けない。

### 結果発表の順序

```text
show_results()
  → ドラムロール再生
  → animate_ratio_bars(0)
  → 70msごとに再描画
  → 36ステップ到達
  → 正確な棒と整数%を表示
  → 昼勤・夜勤の写真変更
  → 結果音を再生
```

**注意:** 「結果表示」を短時間に連続クリックすると複数の`after()`系列が重なる可能性がある。現行コードには多重実行防止や`after_cancel()`がない。今後の改造時に検討する価値がある。

## 10. `lambda` と `enumerate()`

```python
for i, (title, _, _) in enumerate(ratio_specs):
    ...
    c.bind("<Configure>", lambda e, idx=i: draw_ratio_bar(idx))
```

`enumerate()` は要素と番号を同時に取り出す。`(title, _, _)` はタプルのうちタイトルだけ使い、残りは使わないという書き方。`<Configure>` はCanvasのサイズ変更などで発生するイベント。

`lambda e, idx=i` の `idx=i` は**その周回の番号を固定**する工夫。単に `lambda e: draw_ratio_bar(i)` とすると、後で呼ばれる際に最後のiを参照してしまう可能性がある。

## 11. 週間検査数の表示

`create_weekly_table()` は見出し行と昼勤・夜勤の2行、月～土の6列を作り、各数値セルのLabelを `weekly_cells` に保存する。

```python
weekly_cells[row][col].configure(
    text=f"{count:,}",
    bg=ACCENT if is_today else "white",
    fg="white" if is_today else "#111111",
)
```

`f"{count:,}"` は桁区切り表示。`base_datetime.weekday()` に一致する列の**数値セル**を赤背景にする。日曜日は0～5の列に該当しないため赤表示されない。

## 12. 下段の表示は現状サンプル

- `create_kpi_table()`：実績・目標・達成率・進捗の表。達成率は `round(actual / target * 100)`、目標0なら0。
- `create_progress_section()`：125%を共通スケールとする横棒グラフを2本作る。
- `create_bot_section()`：GIFをPillowでフレームごとに読み込む。
- `animate_bot()`：`root.after(100, ...)` で約100msごとにフレーム更新。

**注意:** 下段の数値（例: 113、105、実績、号機別生産数）はSQLiteから読み込んでいない。`目標入力` ボタンにも現時点で`command`は設定されていない。

### 進捗グラフの共通目盛り

```python
width_ratio = display_max / 125
```

125%を全幅の基準とし、`display_max=100` のグラフは幅を80%にする。これで2本の100%位置を揃える。`Canvas` の内部では `display_max` に対する割合で棒の長さを計算する。

## 13. 終了時のJSON保存

`root.protocol("WM_DELETE_WINDOW", on_close)` はウィンドウを閉じる操作を `on_close()` に接続する。

```python
def on_close():
    save_staff_info()
    root.destroy()
```

`save_staff_info()` は現在の昼勤・夜勤Comboboxの選択名をJSONへ書き戻す。`json.dump(..., ensure_ascii=False, indent=4)` は日本語をそのまま書き、4スペースで整形する。**保存するのは担当者名であり、smile/sadなどの表情状態ではない。**

## 14. さらに理解しておきたい保守ポイント

1. `main` という名前がFrame変数と起動関数で衝突している（①参照）。
2. `show_results()` は長く、DB集計途中で共有状態を書き換える。
3. 結果発表後にメンバー変更すると、その写真はnormalに戻る。
4. 結果表示ボタン連打時にアニメーションが重なり得る。
5. 写真/GIFはPillow依存、音声はWindowsの`winsound`依存。
6. 画面の下段は仮データなので、上段の実データ処理と混同しない。

これらは**現状の読み解きから分かる注意点**であり、この解説書の作成にあたってプログラムは変更していない。

## 15. 理解度チェック

1. なぜ `pic.image = photo` が必要？
2. `lambda e, idx=i` の `idx=i` は何を防ぐ？
3. `root.after(70, ...)` と `time.sleep(0.07)` の違いは？
4. `update_staff_photos()` はComboboxの選択名を変更する？
5. 下段の達成率はDBから取得している？

**答え:** 1. 画像参照の保持。2. ループ変数の遅延参照。3. afterは後で呼ぶ予約、sleepはその場で処理を止める。4. しない。5. いいえ、現在はサンプル値から計算。
