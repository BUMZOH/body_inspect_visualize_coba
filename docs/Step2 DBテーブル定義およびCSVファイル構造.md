
# Step2 DBテーブル定義およびCSVファイル構造
最終更新: 2026/11/11

## テーブル：measurement_result

| No. | カラム名 | データ型 | PK | 説明 | 例 |
|---:|---|---|:---:|---|---|
| 1 | insp_machine_no | INTEGER | ✓ | 検査機番号 | 412 |
| 2 | inspection_item | TEXT | ✓ | 検査項目名 | total_length (下記参照) |
| 3 | measured_at | TEXT | ✓ | 測定日時 | 2026-11-08 15:20:30 |
| 4 | part_no | TEXT | | 品番 | 299526-3220 |
| 5 | proc_machine_no | INTEGER | | 加工機No | 170 |
| 6 | process_date | TEXT | | 加工日 | 2026-10-25 |
| 7 | measured_value | REAL | | 測定値 | 3.526 |
| 8 | judgment | TEXT | | 判定 | OK / NG |
| 9 | upper_limit | REAL | | 許容値上限 | 3.400 |
| 10 | lower_limit | REAL | | 許容値下限 | 3.600 |

### 検査項目 (inspection_item) 
| No. | 検査項目 | 値 |
| --- | --- | :--- |
| 1 | 全長 | total_length |
| 2 | 厚み | thickness |
| 3 | ボトム厚 | bottom_thickness |
| 4 | φ0.71深さ | depth_phi071 |
| 5 | 内径 | inner_diameter |

### 備考
- DBファイル名: body_insp_measurement_data.db (SQLite)
<BR><BR><BR>
---
## CSVファイル構造

### カラム
- 上記`measurement_result`テーブルの`insp_machine_no`と`inspection_item`を除外した全て
- `insp_machine_no` は通信時のIPアドレスから判明するため不要
- `inspection_item` はCSVファイル名から判明するため不要
- カラムおよび値にはダブルクオーテーションは不要

### CSVファイル 命名規則
CSVファイルは、各検査項目に対し1時間ごとに分割する。
```
(検査項目名)_(年月日)_(時間).csv

例: total_length_20261108_05.csv
```

### CSVファイル 保存場所
SDカード内の`inspection_data`フォルダ内に保存する
```
SD
└─ inspection_data
   ├─ total_length_20261108_05.csv
   ├─ total_length_20261108_06.csv
   ├─ ...
   ├─ thickness_20261108_05.csv
   ├─ thickness_20261108_06.csv
   ├─ ...
   ├─ bottom_thickness_20261108_05.csv
   ├─ bottom_thickness_20261108_06.csv
   └─ ...
```
<BR><BR><BR>

---
## 制御関連

### 加工機Noおよび加工日のチェック
- 加工機Noおよび加工日は検査装置のタッチパネルから入力される
- PLCは自動運転開始時に入力値を検証する（バリデーション）
- ロットごとの記録時（記録用PCによるDB登録時）にゼロリセットする（変更忘れに対するポカヨケ）

### PCからのCSVファイルアクセス
- PCは最新のCSVファイルにはアクセスしない(FTPでダウンロードしない)
- PLCがCSVファイルにデータ書き込み中にアクセスるのは危険であるため
- 1時間程度のタイムラグが発生する。
- タイムラグを小さくする場合は10分ごとのファイル分割を検討する。

### CSVファイルの削除
- PCはDB登録した後、読み取ったCSVファイルを削除する（ファイル数が過大となるため）

### PLCのSDカード挿入チェック、空き容量チェック
- PLCは自動運転開始時にSDカードが挿入されていない場合にアラームを発生させる
- 空き容量が少ない場合、アラームまたは警報（表示のみ）を出す



