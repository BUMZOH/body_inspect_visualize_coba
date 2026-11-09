# Tkinter UIレイアウト解説書

対象：`main(20261105-134158).py`（2026-11-05版）

## 1. この解説書の目的

このプログラムの画面を構成するFrameの**親子関係・画面上の位置・配置方法**を理解し、後からレイアウトを修正できるようにする。説明は添付コードの実装に基づく。

**最重要ポイント：** `row` と `column` は画面全体の座標ではなく、**そのウィジェットの親Frame内**での位置である。同じ `row=0, column=0` でも、親が違えば別の場所になる。

## 2. 画面全体の構造

```text
root（Tkウィンドウ：全画面表示）
└── frm_main（画面全体の余白を除いた領域）
    ├── row=0, column=0 : frm_header（タイトル・操作ボタン）
    ├── row=1, column=0 : frm_top（上段パネル）
    │   ├── row=0, column=0 : frm_day_group（昼勤メンバー）
    │   ├── row=0, column=1 : frm_center（可動率グラフ・週間検査数）
    │   └── row=0, column=2 : frm_night_group（夜勤メンバー）
    ├── row=2, column=0 : 「本日の生産状況」ラベル
    └── row=3, column=0 : frm_bottom（下段パネル）
        ├── row=0, column=0 : frm_left（生産実績・目標入力）
        ├── row=0, column=1 : frm_middle（進捗グラフ・号機別生産数）
        └── row=0, column=2 : frm_bot（GIFアニメーション）
```

概略図（幅や高さは正確な縮尺ではない）：

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ root                                                                     │
│ ┌──────────────────────────── frm_main ────────────────────────────────┐ │
│ │ row 0 : frm_header  可動率勝負                   [結果表示][メンバ入替] │ │
│ ├──────────────────────────────────────────────────────────────────────┤ │
│ │ row 1 : frm_top                                                      │ │
│ │ ┌────────────────┬─────────────────────────────┬───────────────────┐ │ │
│ │ │ col 0          │ col 1                       │ col 2             │ │ │
│ │ │ frm_day_group  │ frm_center                  │ frm_night_group   │ │ │
│ │ │ 昼勤メンバー    │ 可動率バー × 2               │  夜勤メンバー      │ │ │
│ │ │ 写真カード6枚   │ 週間検査数テーブル            │  写真カード6枚     │ │ │
│ │ └────────────────┴─────────────────────────────┴───────────────────┘ │ │
│ │ row 2 : 本日の生産状況                                                │ │
│ │ row 3 : frm_bottom                                                   │ │
│ │ ┌──────────────────┬─────────────────────────┬─────────────────────┐ │ │
│ │ │ col 0            │ col 1                   │ col 2               │ │ │
│ │ │ frm_left         │ frm_middle              │ frm_bot             │ │ │
│ │ │ 実績・目標表      │ 進捗グラフ・号機別表      │ ロボットGIF          │ │ │
│ │ └──────────────────┴─────────────────────────┴─────────────────────┘ │ │
│ └──────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

## 3. root と frm_main

### 3.1 root：アプリ全体のウィンドウ

`initialize_app()` で作成する。

```python
root = tk.Tk()
root.geometry(f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}")
root.attributes("-fullscreen", True)
```

設定値は `SCREEN_WIDTH = 1920`、`SCREEN_HEIGHT = 1080`。ただし実際の表示は `-fullscreen` により全画面となるため、画面の実サイズに依存する。

### 3.2 frm_main：全体レイアウトの土台

`create_main_layout()`：

```python
frm_main = tk.Frame(root, bg=BG)
frm_main.pack(fill="both", expand=True, padx=15, pady=12)
frm_main.grid_columnconfigure(0, weight=1)
frm_main.grid_rowconfigure(1, weight=50)
frm_main.grid_rowconfigure(3, weight=50)
```

- 親は `root`。
- `pack(fill="both", expand=True)`：親の空き領域に合わせて縦横に広がる。
- `padx=15`：左右に15pxの外側余白。
- `pady=12`：上下に12pxの外側余白。
- `frm_main` の子は `grid()` で4行に配置される。
- `column=0` に `weight=1` を指定し、横方向の余剰領域を受け取る。
- `row=1` と `row=3` に同じ `weight=50` を指定しているため、**余った縦方向の領域を同じ比率で分配**する。ただし両パネルの最終的な高さが必ず同じになるという意味ではない。各行の必要最小サイズも関係する。

> `frm_main` 自体は親 `root` の中で `pack()`、`frm_main` の子は `grid()`。**異なる親の中で使い分けているため問題ない。**

## 4. frm_main の4行を詳しく見る

| 行 | 子ウィジェット | 役割 | 作成場所 |
|---|---|---|---|
| 0 | `frm_header` | タイトルとボタン | `create_header()` |
| 1 | `frm_top` | 昼勤・中央・夜勤 | `create_top_panel()` |
| 2 | ラベル | 「本日の生産状況」 | `create_main_layout()` |
| 3 | `frm_bottom` | 生産実績・進捗・GIF | `create_bottom_panel()` |

### 4.1 row=0：frm_header

```python
frm_header = tk.Frame(frm_main, bg=BG)
frm_header.grid(row=0, column=0, sticky="ew", pady=(0, 6))
frm_header.grid_columnconfigure(0, weight=1)
```

`sticky="ew"` は東西（左右）へ伸ばす指定。`pady=(0, 6)` は上0px・下6px。

ヘッダー内も `grid()`：

| row | column | 内容 | 配置 |
|---|---|---|---|
| 0 | 0 | 「可動率勝負」 | `sticky="w"` で左寄せ |
| 0 | 1 | 「結果表示」ボタン | `padx=5` |
| 0 | 2 | 「メンバ入替」ボタン | `padx=5` |

`column=0` の `weight=1` によりタイトルの列が伸び、ボタンは右側に寄る。

### 4.2 row=1：frm_top

```python
frm_top = tk.Frame(
    frm_main, bg=PANEL,
    highlightbackground=LINE, highlightthickness=4,
)
frm_top.grid(row=1, column=0, sticky="nsew")
frm_top.grid_columnconfigure(0, minsize=350)
frm_top.grid_columnconfigure(1, weight=1)
frm_top.grid_columnconfigure(2, minsize=350)
frm_top.grid_rowconfigure(0, weight=1)
```

- `sticky="nsew"`：上下左右へ広がり、割り当てられたセルを埋める。
- 左右列（0, 2）は最低350px。
- 中央列（1）は `weight=1` で追加の横幅を受け取る。
- `minsize=350` は固定幅350pxという意味ではない。子の必要サイズなどによって広がり得る。
- `grid_rowconfigure(0, weight=1)` で中の1行が縦方向の余剰領域を受け取る。

子Frameの配置：

```python
frm_day_group.grid(row=0, column=0, padx=15, pady=28, sticky="nsew")
frm_center.grid(row=0, column=1, sticky="nsew", padx=20, pady=12)
frm_night_group.grid(row=0, column=2, padx=15, pady=28, sticky="nsew")
```

左右のメンバー枠は上下28px、中央枠は上下12pxの余白を持つ。したがって、**3つのFrameが同じ行にあっても上下の余白は異なる**。

### 4.3 row=2：見出しラベル

```python
label(frm_main, "本日の生産状況", 26, True, bg=BG).grid(
    row=2, column=0, sticky="w", pady=(8, 3)
)
```

Frameではなく `frm_main` 直下のLabel。`sticky="w"` で左寄せ、上8px・下3pxの余白。

### 4.4 row=3：frm_bottom

```python
frm_bottom = tk.Frame(
    frm_main, bg=PANEL,
    highlightbackground=LINE, highlightthickness=4,
)
frm_bottom.grid(row=3, column=0, sticky="nsew")
frm_bottom.grid_columnconfigure(0, minsize=520)
frm_bottom.grid_columnconfigure(1, weight=1)
frm_bottom.grid_columnconfigure(2, minsize=330)
frm_bottom.grid_rowconfigure(0, weight=1)
```

下段も3列構成だが、**上段と列幅の設定は独立**している。

| 列 | 子Frame | 内容 | 列の設定 |
|---|---|---|---|
| 0 | `frm_left` | KPIテーブル・目標入力 | 最低520px |
| 1 | `frm_middle` | 進捗グラフ・号機別表 | `weight=1` |
| 2 | `frm_bot` | GIF | 最低330px |

```python
frm_left.grid(row=0, column=0, sticky="nsew", padx=14, pady=10)
frm_middle.grid(row=0, column=1, sticky="nsew", padx=14, pady=10)
frm_bot.grid(row=0, column=2, sticky="nsew", padx=18, pady=10)
```

## 5. 上段：メンバーFrameの内部構造

`create_staff_group(parent, title, title_color, shift)` は、昼勤と夜勤で共通利用される関数。

```text
frm_top
└── frm_day_group または frm_night_group（frm_staffとして作成）
    ├── タイトルLabel（pack）
    └── frm_grid（pack）
        ├── row=0 : frm_card 0 / frm_card 1 / frm_card 2
        └── row=1 : frm_card 3 / frm_card 4 / frm_card 5
            ├── lbl_photo（pack）
            └── cmb_staff（pack）
```

重要な部分：

```python
frm_grid = tk.Frame(frm_staff, bg=PANEL)
frm_grid.pack(padx=7, pady=(0, 7))

for i in range(6):
    frm_card = tk.Frame(frm_grid, width=112, height=154, bg=PANEL)
    frm_card.grid(row=i // 3, column=i % 3)
    frm_card.grid_propagate(False)
```

`i // 3` は行番号（0,0,0,1,1,1）、`i % 3` は列番号（0,1,2,0,1,2）を生成する。

`grid_propagate(False)` により、カードFrameが子ウィジェットの要求サイズに合わせて自動的にサイズ変更されるのを防ぎ、指定した112×154pxを維持しやすくしている。

カード内は `pack()` で写真が残りの縦領域を使用し、Comboboxが下部に配置される。

**補足：** `frm_staff` は関数内のローカル変数名だが、返されたFrameが `frm_day_group` または `frm_night_group` に保持され、さらに親子関係によってTkinter側にも管理される。

## 6. 上段中央：frm_centerの内部構造

```text
frm_center
├── 1つ目の比率タイトルLabel（pack）
├── 1つ目の frm_row（pack）
│   ├── 「今週」Label（左からpack）
│   ├── cvs_ratio（左からpack、横に拡張）
│   └── 「先週」Label（左からpack）
├── 2つ目の比率タイトルLabel（pack）
├── 2つ目の frm_row（pack）
│   └── 同じ構成
├── 「週間検査数」Label（pack）
└── frm_weekly（pack）
    └── gridによる表：見出し1行＋昼勤・夜勤の2行、7列
```

比率グラフ：

```python
frm_row = tk.Frame(frm_center, bg=PANEL)
frm_row.pack(fill="x")
label(frm_row, "今週", 17, True).pack(side="left", padx=(0, 10))
cvs_ratio.pack(side="left", fill="x", expand=True)
label(frm_row, "先週", 17, True).pack(side="left", padx=(10, 0))
```

`side="left"` で左から横に並べる。Canvasだけが `expand=True` なので、横方向の空き領域を受け取る。

週間検査数の表は `frm_weekly` 内で `grid()` を使用する。列0が昼勤・夜勤ラベル、列1〜6が月〜土。`grid_columnconfigure(c, weight=1)` によって7列に横方向の余剰領域を分配する。

## 7. 下段左：frm_leftの内部構造

```text
frm_left
├── frm_block（直近1時間のKPI）［pack］
│   ├── タイトルLabel［pack］
│   └── frm_table［pack］
│       └── 2行×4列のLabel表［grid］
├── frm_block（累積生産数のKPI）［pack］
│   └── 同じ構成
└── frm_control［pack］
    ├── column=0 : 「目標入力」ボタン［grid］
    ├── column=1 : 「目標生産数」Label［grid］
    └── column=2 : 「300000」Label［grid］
```

`create_kpi_table()` はFrameを**作成して返す**関数であり、返されたFrameの配置は呼び出し側が行う。

```python
create_kpi_table(...).pack(fill="x")
create_kpi_table(...).pack(fill="x", pady=(8, 20))
```

この書き方は、生成と配置を1行で行っている。

## 8. 下段中央：frm_middleの内部構造

```text
frm_middle
├── 進捗タイトルLabel［pack］
├── frm_progress（直近1時間）［pack］
│   ├── frm_axis［place］
│   │   └── 目盛りLabel群［place］
│   └── cvs_progress［place］
├── 進捗タイトルLabel［pack］
├── frm_progress（累積生産数）［pack］
│   ├── frm_axis［place］
│   └── cvs_progress［place］
├── 「号機別生産数」Label［pack］
└── frm_machine［pack］
    └── 2行×5列のLabel表［grid］
```

### 8.1 なぜ進捗グラフは place() なのか

```python
frm_progress = tk.Frame(frm_middle, bg=PANEL, height=92)
frm_progress.pack(fill="x", pady=(0, 10))
frm_progress.pack_propagate(False)

frm_axis = tk.Frame(frm_progress, bg=PANEL)
frm_axis.place(relx=0, rely=0, relwidth=width_ratio, height=25)

cvs_progress.place(relx=0, y=25, relwidth=width_ratio, height=64)
```

`frm_progress` 自体は `pack()` で縦に並ぶ。一方、その**内部の目盛りとCanvasは位置・高さを細かく指定する必要があるため** `place()` を使用する。

- `relx=0`：親の左端から。
- `rely=0`：親の上端から。
- `y=25`：親の上端から25px。
- `relwidth=width_ratio`：親の幅に対する割合。
- `height=25` / `height=64`：高さをピクセル指定。

`display_max=125` なら `width_ratio=1.0`、`display_max=100` なら `width_ratio=0.8`。**両グラフの100%地点を同じ横位置に揃える**ための仕組みである。

`pack_propagate(False)` は `frm_progress` の指定高さ92pxが内部の子ウィジェットの要求サイズによって変わるのを防ぐ。

## 9. 下段右：frm_bot

```python
frm_bot = tk.Frame(frm_bottom, bg=PANEL)
frm_bot.grid(row=0, column=2, sticky="nsew", padx=18, pady=10)
lbl_bot = tk.Label(frm_bot, bg=PANEL)
lbl_bot.pack(expand=True)
```

`frm_bot` は `frm_bottom` の右列。内部の `lbl_bot` は `pack(expand=True)` によって余剰領域を受け取り、GIF表示を行う。`fill` は指定していないため、Label自体をFrameいっぱいに引き伸ばす指定ではない。

## 10. pack / grid / place の使い分け

| 配置方法 | このプログラムでの用途 | 得意なこと |
|---|---|---|
| `pack()` | 全体土台、Frame内の縦積み、ラベルとCanvasの横並び | 順番に並べる |
| `grid()` | 上下パネルの位置、3列分割、表、カード6枚 | 行と列で配置する |
| `place()` | 進捗バーの目盛り・Canvas | 座標や割合で精密配置する |

**同じ親Frameの直接の子に対して `pack()` と `grid()` を混在させない。** ただし親Frameが異なれば問題ない。

例：`frm_top` は `frm_main` 内で `grid()`、`frm_center` も `frm_top` 内で `grid()`、しかし `frm_center` の子は `pack()`。これは正常な設計。

## 11. 重要なオプション

| 指定 | 意味 | 注意点 |
|---|---|---|
| `row=1, column=0` | 親の1行目・0列目 | 番号は0始まり |
| `sticky="nsew"` | セル内で上下左右に伸ばす | セルの大きさ自体を決めるわけではない |
| `sticky="ew"` | セル内で左右に伸ばす | 縦には伸ばさない |
| `sticky="w"` | 左寄せ | `w` はwest（西） |
| `weight=1` | 余剰スペースの分配比率 | 必要最小サイズとは別 |
| `minsize=350` | 行・列の最低サイズ | 固定サイズではない |
| `padx=(10, 0)` | 左10px・右0px | `padx=10` なら左右10px |
| `pady=(8, 3)` | 上8px・下3px | 位置の微調整に便利 |
| `fill="x"` | 横方向に伸ばす | `pack()` の指定 |
| `expand=True` | 親の余剰領域の割当てを受ける | `fill` とは役割が異なる |
| `pack_propagate(False)` | 子の要求サイズによる親の自動サイズ調整を抑止 | `pack()` 管理の子に関係する |
| `grid_propagate(False)` | 同上（`grid()` 用） | 固定サイズのカードに使用 |
| `relwidth=0.8` | 親幅の80% | `place()` の指定 |

## 12. レイアウトを変更するときの探し方

### 上段と下段の高さ配分を変えたい

`create_main_layout()` の次の2行を確認する。

```python
frm_main.grid_rowconfigure(1, weight=50)
frm_main.grid_rowconfigure(3, weight=50)
```

例えば `weight=60` と `weight=40` にすると、**余剰領域の分配比率**が6:4になる。ただし最終的なパネル高さが必ず6:4になるわけではない。

### 上段中央を広くしたい

`create_top_panel()` の列設定と各Frameの余白を確認する。

```python
frm_top.grid_columnconfigure(0, minsize=350)
frm_top.grid_columnconfigure(1, weight=1)
frm_top.grid_columnconfigure(2, minsize=350)
```

左右の `minsize` や子の要求サイズが中央幅に影響する。中央は既に余剰幅を受け取る設定になっている。

### 下段の左・中央・右の幅を変えたい

`create_bottom_panel()` の `grid_columnconfigure()` を確認する。上段とは独立している。

### メンバー写真の大きさを変えたい

`create_staff_group()` の `frm_card` の `width=112, height=154` と、`load_photo()` の既定サイズ `(105, 118)` の**両方**を確認する。

### 進捗バーの高さ・幅を変えたい

`create_progress_section()` の `frm_progress` の `height=92`、`frm_axis.place()`、`cvs_progress.place()`、および `width_ratio` を確認する。

### 表の列幅や行の高さを変えたい

`create_table_cell()` の `tk.Label(... width=width, pady=7)` と、表を置くFrameの `grid_columnconfigure()` を確認する。Labelの `width` は通常ピクセルではなく文字数ベースである。

## 13. よくある勘違い

1. **`row=0` は画面の一番上とは限らない。** 親Frame内の0行目を意味する。
2. **`weight=1` は幅を1pxにする意味ではない。** 余剰スペースの分配比率を意味する。
3. **`minsize=350` は幅350px固定ではない。** 最小値である。
4. **`sticky="nsew"` だけでウィンドウ全体が伸縮するわけではない。** 親の行・列の設定も必要。
5. **`pack()` と `grid()` の混在禁止は、同じ親の直接の子に対しての話。** Frameごとに使い分けるのは正常。
6. **Frameを生成しただけでは配置されない。** `pack()`・`grid()`・`place()` のいずれかで配置する必要がある。
7. **コードの並び順がすべての画面位置を決めるわけではない。** `grid()` では `row` と `column` が位置を決める。

## 14. UI作成処理の実行順

```text
main()
 ├── JSONからスタッフ設定を読み込む
 ├── initialize_app()
 │    └── rootを作成
 ├── create_main_layout()
 │    ├── frm_mainを作成
 │    ├── create_header()          → row=0
 │    ├── create_top_panel()       → row=1
 │    │    ├── create_staff_group() × 2
 │    │    ├── create_ratio_section()
 │    │    └── create_weekly_table()
 │    ├── 見出しラベルを作成       → row=2
 │    └── create_bottom_panel()    → row=3
 │         ├── create_kpi_table() × 2
 │         ├── create_progress_section()
 │         └── create_bot_section()
 ├── setup_events()
 └── root.mainloop()
```

## 15. まとめ

このUIは、**`frm_main` の縦4行 → 上下パネル内の横3列 → 各領域内の小さなFrame**という階層構造でできている。

レイアウトを修正するときは、まず「変更したいウィジェットの**親Frameは何か**」を確認する。そのうえで、親Frameの `grid_rowconfigure()` / `grid_columnconfigure()` と、対象ウィジェットの `pack()` / `grid()` / `place()` を調べる。

これが最も混乱しにくい確認順序である。

---

*対象ソース：`main(20261105-134158).py`。本書はコードのレイアウト構造を解説するものであり、実行画面の実測寸法を示すものではない。*
