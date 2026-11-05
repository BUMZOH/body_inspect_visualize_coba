import json
import math
import sqlite3
import tkinter as tk
import winsound
from tkinter import ttk, simpledialog, messagebox
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image, ImageTk, ImageSequence

# ================================================
# region Settings
# ================================================
BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "data" / "body_inspection_machine.db"
IMAGE_DIR = BASE_DIR / "image"
BOT_GIF = IMAGE_DIR / "factory_bot.gif"

STAFF_PHOTO_DIR = BASE_DIR / "staff_photo"
STAFF_INFO_FILE = BASE_DIR / "staff_shift_info.json"

SOUND_DIR = BASE_DIR / "sound"
DRUM_SOUND = SOUND_DIR / "drum_roll.wav"
BANG_SOUND = SOUND_DIR / "result_bang.wav"

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
BG = "#f7f7f7"
PANEL = "#ffffff"
TEXT = "#5b5b5b"
LINE = "#9b9b9b"
HEADER = "#aaaaaa"
DAY = "#c89a00"
NIGHT = "#ffc928"
PROGRESS = "#a9bfe4"
ACCENT = "#ff5959"

# FONT = "Yu Gothic"
FONT = "UD デジタル 教科書体 NP"

# endregion

# ================================================
# region Sample Data (bottom panel)
# ================================================
# Sample values shown in the reference layout
recent_this_week = 60
recent_last_week = 40
total_this_week = 52
total_last_week = 48
actual_recent = 13535
target_recent = 13500
actual_total = 155000
target_total = 150000
machine_counts = [("No.412", 3457), ("No.413", 3123), ("No.416", 2544), ("No.421", 957), ("No.428", 2884)]

# endregion

# ================================================
# region Global Variables
# ================================================
# Tkinter root and main widgets
root = None
frm_main = None
frm_center = None
btn_result = None
frm_day_group = None
frm_night_group = None

# Ratio bars
results_visible = False
cvs_ratios = []
lbl_ratio_titles = []
ratio_specs = [
    ("【直近1時間】（18：00〜19：00）", recent_this_week, recent_last_week),
    ("【全経過時間】（8：00〜19：00）", total_this_week, total_last_week),
]
animated_ratios = [0.5, 0.5]
ratio_targets = [a / (a + b) if a + b else 0.5 for _, a, b in ratio_specs]
result_photo_modes = ("normal", "normal")  # (day, night)

# Weekly production and robot animation
lbl_weekly_cells = []
lbl_bot = None
bot_frames = []

# Staff settings (loaded in main)
STAFF_INFO = {}     # 設定JSONファイル格納用
STAFF_NAMES = []    # Combobox リスト作成用

# 下段左側の生産状況表示用
kpi_value_labels = {}
kpi_title_labels = {}
lbl_daily_goal = None  # 生産日の目標生産数を表示するLabel

# 下段中央の進捗グラフ（Canvas・見出し・達成率）
progress_charts = {}
# endregion

# ================================================
# region Database Functions
# ================================================

def get_previous_week_datetime(base_datetime):
    return base_datetime - timedelta(days=7)

def get_shift_start_datetime(base_datetime):
    hour = base_datetime.hour

    if 8 <= hour <= 19:
        return base_datetime.replace(hour=8)

    if hour >= 20:
        return base_datetime.replace(hour=20)

    return (base_datetime - timedelta(days=1)).replace(hour=20)

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

def get_cumulative_operating_time(start_datetime, end_datetime):
    start_str = start_datetime.strftime("%Y-%m-%d %H:%M")
    end_str = end_datetime.strftime("%Y-%m-%d %H:%M")

    with sqlite3.connect(DB_FILE) as conn:
        total_sec = conn.execute(
            """
            SELECT COALESCE(SUM(operating_time_sec), 0)
            FROM production_result
            WHERE date_hour >= ? AND date_hour <= ?
            """,
            (start_str, end_str),
        ).fetchone()[0]

    return total_sec

def get_weekly_production(base_datetime):
    # 基準日を含む週の月曜日
    monday = (
        base_datetime - timedelta(days=base_datetime.weekday())
    ).replace(hour=0, minute=0, second=0, microsecond=0)

    weekly_day = []
    weekly_night = []

    with sqlite3.connect(DB_FILE) as conn:
        for i in range(6):
            day = monday + timedelta(days=i)

            day_start = day.replace(hour=8)
            day_end = day.replace(hour=20)

            night_start = day_end
            night_end = day_end + timedelta(hours=12)

            day_count = conn.execute(
                """
                SELECT COALESCE(SUM(production_num_1hour), 0)
                FROM production_result
                WHERE date_hour >= ? AND date_hour < ?
                """,
                (
                    day_start.strftime("%Y-%m-%d %H:%M"),
                    day_end.strftime("%Y-%m-%d %H:%M"),
                ),
            ).fetchone()[0]

            night_count = conn.execute(
                """
                SELECT COALESCE(SUM(production_num_1hour), 0)
                FROM production_result
                WHERE date_hour >= ? AND date_hour < ?
                """,
                (
                    night_start.strftime("%Y-%m-%d %H:%M"),
                    night_end.strftime("%Y-%m-%d %H:%M"),
                ),
            ).fetchone()[0]

            weekly_day.append(day_count)
            weekly_night.append(night_count)

    return weekly_day, weekly_night


def get_production_summary(base_datetime):
    """直近1時間と、生産日8:00から基準の1時間後までの実績・目標を取得。"""
    # 生産日は8:00に切り替わる（0:00～7:00は前日扱い）
    production_date = base_datetime
    if base_datetime.hour < 8:
        production_date -= timedelta(days=1)

    # 累積生産数は生産日の8:00から集計する
    start_datetime = production_date.replace(
        hour=8, minute=0, second=0, microsecond=0
    )

    # 基準時間の1時間分も集計に含めるため、終了時刻は1時間後とする
    # SQLでは終了時刻を含まない（date_hour < end_datetime）
    end_datetime = base_datetime + timedelta(hours=1)

    with sqlite3.connect(DB_FILE) as conn:
        # 直近1時間と累積生産数を、1回のSQLで取得する
        # CASE WHENは基準時間以降のデータだけを直近1時間に加算する
        recent_actual, total_actual = conn.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN date_hour >= ?
                    THEN production_num_1hour ELSE 0 END), 0),
                COALESCE(SUM(production_num_1hour), 0)
            FROM production_result
            WHERE date_hour >= ? AND date_hour < ?
            """,
            (
                base_datetime.strftime("%Y-%m-%d %H:%M"),
                start_datetime.strftime("%Y-%m-%d %H:%M"),
                end_datetime.strftime("%Y-%m-%d %H:%M"),
            ),
        ).fetchone()

        # 0:00～7:00の場合、目標も前日の生産日から取得する
        row = conn.execute(
            "SELECT production_goal FROM production_goal WHERE date = ?",
            (production_date.strftime("%Y-%m-%d"),),
        ).fetchone()

    if row is None:
        raise ValueError("生産日の生産目標が登録されていません。")

    daily_goal = row[0]
    if daily_goal <= 0:
        raise ValueError("生産日の生産目標は正の数である必要があります。")

    # 1時間の目標は24時間分の目標を24で割る
    recent_target = daily_goal / 24

    # 8:00から基準時間の1時間後までの経過時間を求める
    # 例：翌日5:00が基準なら、翌日6:00までの22時間
    elapsed_hours = (end_datetime - start_datetime).total_seconds() / 3600
    total_target = recent_target * elapsed_hours

    return recent_actual, recent_target, total_actual, total_target


def get_production_status(actual, target):
    rate = actual / target * 100
    if rate < 50:
        return "超遅れ"
    if rate < 100:
        return "遅れ"
    if rate < 125:
        return "順調"
    return "作りすぎ"

# endregion

# ================================================
# region UI Helper Functions
# ================================================

def label(parent, text="", size=16, bold=False, fg=TEXT, bg=PANEL, **kwargs):
    return tk.Label(parent, text=text, font=(FONT, size, "bold" if bold else "normal"), fg=fg, bg=bg, **kwargs)

def load_photo(path, size=(105, 118)):
    if not path.exists():
        return None
    im = Image.open(path).convert("RGB")
    im.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, "white")
    x = (size[0] - im.width) // 2
    y = (size[1] - im.height) // 2
    canvas.paste(im, (x, y))
    return ImageTk.PhotoImage(canvas)

def create_staff_group(parent, title, title_color, shift):
    frm_staff = tk.Frame(
        parent,
        bg=PANEL,
        highlightbackground=LINE,
        highlightthickness=2,
    )

    # Frameインスタンスにcombos属性を動的に追加
    # 各Comboboxを登録し、アプリ終了時の設定保存に使用する
    frm_staff.combos = []
    frm_staff.photos = []

    label(frm_staff, title, 18, True, title_color).pack(pady=(0, 8))

    frm_grid = tk.Frame(frm_staff, bg=PANEL)
    frm_grid.pack(padx=7, pady=(0, 7))

    for i in range(6):
        frm_card = tk.Frame(
            frm_grid,
            width=112,
            height=154,
            bg=PANEL,
            highlightbackground=LINE,
            highlightthickness=1,
        )
        frm_card.grid(row=i // 3, column=i % 3)
        frm_card.grid_propagate(False)

        # Find the staff member assigned to this position
        staff_name = STAFF_INFO[shift][i]
        photo_path = None

        if staff_name != "NAME":
            base_name = STAFF_INFO["staff"][staff_name]
            photo_path = STAFF_PHOTO_DIR / f"{base_name}_normal.png"

        # Display photo
        photo = load_photo(photo_path) if photo_path else None

        lbl_photo = tk.Label(frm_card, bg="white")

        if photo:
            lbl_photo.configure(image=photo)
            lbl_photo.image = photo
        else:
            lbl_photo.configure(text="PHOTO")

        lbl_photo.pack(fill="both", expand=True)

        # Staff selection
        cmb_staff = ttk.Combobox(
            frm_card,
            values=STAFF_NAMES,
            state="readonly",
            style="Staff.TCombobox",
            justify="center",
        )
        cmb_staff.set(staff_name)
        cmb_staff.pack(fill="x")

        frm_staff.combos.append(cmb_staff)
        frm_staff.photos.append(lbl_photo)

        # デフォルト引数(lbl_photo=lbl_photo)の役割に注意する
        def change_staff(event, lbl_photo=lbl_photo):
            cmb_staff = event.widget
            name = cmb_staff.get()

            if name == "NAME":
                lbl_photo.configure(image="", text="PHOTO")
                lbl_photo.image = None
                return

            base_name = STAFF_INFO["staff"][name]
            photo_path = STAFF_PHOTO_DIR / f"{base_name}_normal.png"
            new_photo = load_photo(photo_path)

            if new_photo:
                lbl_photo.configure(image=new_photo, text="")
                lbl_photo.image = new_photo
            else:
                lbl_photo.configure(image="", text="PHOTO")
                lbl_photo.image = None

        cmb_staff.bind("<<ComboboxSelected>>", change_staff)

    return frm_staff

def update_staff_photos(frm_group, mode):
    """選択中のメンバーを変えずに、写真の表情だけを更新する。"""
    for cmb_staff, lbl_photo in zip(frm_group.combos, frm_group.photos):
        name = cmb_staff.get()
        if name == "NAME":
            lbl_photo.configure(image="", text="PHOTO")
            lbl_photo.image = None
            continue

        base_name = STAFF_INFO["staff"][name]
        photo_path = STAFF_PHOTO_DIR / f"{base_name}_{mode}.png"
        photo = load_photo(photo_path)

        if photo:
            lbl_photo.configure(image=photo, text="")
            lbl_photo.image = photo
        else:
            lbl_photo.configure(image="", text="PHOTO")
            lbl_photo.image = None


def create_table_cell(parent, text, row, col, bg="white", fg="#111111", size=15, width=10, bold=True):
    lbl_cell = tk.Label(parent, text=text, bg=bg, fg=fg, font=(FONT, size, "bold" if bold else "normal"),
                 relief="solid", borderwidth=1, width=width, pady=7)
    lbl_cell.grid(row=row, column=col, sticky="nsew")
    return lbl_cell

def create_kpi_table(parent, title_text, actual, target, status, key):
    frm_block = tk.Frame(parent, bg=PANEL)
    lbl_title = label(frm_block, title_text, 18, True)
    lbl_title.pack(anchor="w", pady=(0, 6))
    # 結果表示時に集計時間を更新できるよう、見出しLabelを保存
    kpi_title_labels[key] = lbl_title
    frm_table = tk.Frame(frm_block, bg=PANEL)
    frm_table.pack(fill="x")

    for c, heading in enumerate(["実 績", "目 標", "達成率", "進捗"]):
        create_table_cell(frm_table, heading, 0, c, HEADER, "white", 14, 9)

    rate = round(actual / target * 100) if target else 0
    values = [f"{actual:,}", f"{target:,.0f}", f"{rate}%", status]
    kpi_value_labels[key] = []

    for c, value in enumerate(values):
        lbl_cell = create_table_cell(
            frm_table, value, 1, c, "white", "#111111", 14, 9
        )
        kpi_value_labels[key].append(lbl_cell)
        frm_table.grid_columnconfigure(c, weight=1)

    return frm_block


def update_kpi_table(key, actual, target):
    rate = actual / target * 100
    status = get_production_status(actual, target)
    values = [f"{actual:,}", f"{target:,.0f}", f"{round(rate)}%", status]

    for lbl_cell, value in zip(kpi_value_labels[key], values):
        lbl_cell.configure(text=value)

# endregion

# ================================================
# region UI Functions
# ================================================
def draw_ratio_bar(index, show_percentage=False):
    if not results_visible:
        return

    cvs_ratio = cvs_ratios[index]

    # 前回描画したバーと文字を消去して描き直す
    cvs_ratio.delete("all")

    w, h = cvs_ratio.winfo_width(), cvs_ratio.winfo_height()
    if w <= 1:
        return

    # Canvasの横幅に昼勤の比率を掛けて、左右の境界位置を求める
    # 例：横幅1000px、比率0.6なら境界位置は600px
    split = w * animated_ratios[index]

    # 境界位置を基準に、左側を昼勤、右側を夜勤の色で描画
    cvs_ratio.create_rectangle(0, 0, split, h, fill=DAY, outline="")
    cvs_ratio.create_rectangle(split, 0, w, h, fill=NIGHT, outline="")

    # アニメーション終了後だけパーセントを表示
    if show_percentage:
        _, left, right = ratio_specs[index]

        cvs_ratio.create_text(
            24, h / 2,
            text=f"{left} %",
            anchor="w",
            fill="white",
            font=(FONT, 21, "bold"),
        )

        cvs_ratio.create_text(
            w - 24, h / 2,
            text=f"{right} %",
            anchor="e",
            fill="black",
            font=(FONT, 21, "bold"),
        )


def animate_ratio_bars(step=0):
    # 36段階 × 70ms = 約2.52秒のアニメーション
    total_steps = 36

    # アニメーション終了時処理
    if step >= total_steps:
        for i in range(2):
            # 揺れを含む途中の値を、正確な最終比率に置き換える
            animated_ratios[i] = ratio_targets[i]
            draw_ratio_bar(i, show_percentage=True)

        update_staff_photos(frm_day_group, result_photo_modes[0])
        update_staff_photos(frm_night_group, result_photo_modes[1])

        # 結果発表音
        winsound.PlaySound(
            str(BANG_SOUND),
            winsound.SND_FILENAME | winsound.SND_ASYNC,
        )
        return

    # 進行度を0～1で表す（開始時0、終了時1）
    progress = step / total_steps

    # Ease Out Cubic：最初は速く、終了に近づくほど減速する
    # progress=0.5の時点で、目標までの87.5%に到達する
    ease = 1 - (1 - progress) ** 3

    # wobble：バーを左右に揺らす演出
    # sin()：プラス・マイナスを繰り返す周期的な揺れ
    # 0.30：揺れの最大振幅（比率換算で30%）
    # (1 - progress ** 3)：終了に近づくにつれて揺れを減衰させる
    wobble = math.sin(step * 0.65) * 0.30 * (1 - progress ** 3)

    for i in range(2):
        target = ratio_targets[i]

        # 50%を開始位置として、目標比率へ徐々に近づける
        # (target - 0.5) * ease：目標へ向かう基本的な動き
        # + wobble：基本的な動きに左右の揺れを加える
        animated_ratios[i] = (
            0.5 + (target - 0.5) * ease + wobble
        )

        # 揺れによって比率が極端にならないよう2～98%に制限
        animated_ratios[i] = max(
            0.02, min(0.98, animated_ratios[i])
        )

        draw_ratio_bar(i)

    # 70ms後にstepを1増やして再実行（GUIを停止させない）
    root.after(70, animate_ratio_bars, step + 1)


def update_weekly_table(base_datetime):
    day_counts, night_counts = get_weekly_production(base_datetime)
    weekday = (base_datetime - timedelta(hours=8)).weekday()

    for row, counts in enumerate([day_counts, night_counts]):
        for col, count in enumerate(counts):
            is_today = col == weekday

            lbl_weekly_cells[row][col].configure(
                text=f"{count:,}",
                bg=ACCENT if is_today else "white",
                fg="white" if is_today else "#111111",
            )

def create_header():
    global btn_result, button_style

    frm_header = tk.Frame(frm_main, bg=BG)
    frm_header.grid(row=0, column=0, sticky="ew", pady=(0, 6))
    # 0列目だけが余った横幅を受け取る設定(ボタンが右寄せになる)
    frm_header.grid_columnconfigure(0, weight=1)
    label(frm_header, "可動率勝負", 28, True, bg=BG).grid(row=0, column=0, sticky="w")
    button_style = dict(
        font=(FONT, 15),
        bg="#f0f0f0",
        fg="#222222",
        activebackground="#e5e5e5",
        activeforeground="#222222",
        relief="solid",
        borderwidth=1,
        padx=28,
        pady=7,
    )
    # 以下"**"は辞書展開 → 辞書の内容をキーワード引数として渡す
    btn_result = tk.Button(frm_header, text="結果表示", **button_style)
    btn_result.grid(row=0, column=1, padx=5)
    tk.Button(frm_header, text="メンバ入替", command=swap_staff, **button_style).grid(row=0, column=2, padx=5)

def create_ratio_section():
    global lbl_ratio_titles

    lbl_ratio_titles = []

    # 上下2つの可動率グラフを作成する
    for i, (title, _, _) in enumerate(ratio_specs):
        lbl_title = label(frm_center, "", 19, True)
        lbl_title.pack(pady=(0 if i == 0 else 18, 4))
        lbl_ratio_titles.append(lbl_title)

        frm_row = tk.Frame(frm_center, bg=PANEL)
        frm_row.pack(fill="x")
        label(frm_row, "今週", 17, True).pack(side="left", padx=(0, 10))
        cvs_ratio = tk.Canvas(frm_row, height=68, bg="white", highlightbackground="#222222", highlightthickness=2)
        cvs_ratio.pack(side="left", fill="x", expand=True)
        label(frm_row, "先週", 17, True).pack(side="left", padx=(10, 0))
        cvs_ratios.append(cvs_ratio)
        cvs_ratio.bind("<Configure>", lambda e, idx=i: draw_ratio_bar(idx))

def create_weekly_table():
    global lbl_weekly_cells

    # Weekly inspection table
    label(frm_center, "週間検査数", 17, True).pack(anchor="w", pady=(10, 0))

    frm_weekly = tk.Frame(frm_center, bg=PANEL)
    frm_weekly.pack(fill="x")

    headers = ["", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    lbl_weekly_cells = []

    for c, h in enumerate(headers):
        create_table_cell(
            frm_weekly, h, 0, c,
            "white" if c == 0 else HEADER,
            "white" if c else TEXT, 14, 9,
        )

    for r, shift in enumerate(["昼 勤", "夜 勤"], start=1):
        create_table_cell(frm_weekly, shift, r, 0, HEADER, "white", 14, 9)

        row_cells = []
        for c in range(1, 7):
            lbl_cell = create_table_cell(
                frm_weekly, "0", r, c, "white", "#111111", 14, 9,
            )
            row_cells.append(lbl_cell)

        lbl_weekly_cells.append(row_cells)

    for c in range(7):
        frm_weekly.grid_columnconfigure(c, weight=1)

def create_top_panel():
    global frm_day_group, frm_night_group, frm_center

    frm_top = tk.Frame(frm_main, bg=PANEL, highlightbackground=LINE, highlightthickness=4)
    frm_top.grid(row=1, column=0, sticky="nsew")
    frm_top.grid_columnconfigure(0, minsize=350)
    frm_top.grid_columnconfigure(1, weight=1)   # 中央の列に、余った横幅を割り当てる
    frm_top.grid_columnconfigure(2, minsize=350)
    frm_top.grid_rowconfigure(0, weight=1)

    frm_day_group = create_staff_group(frm_top, "昼勤メンバー", "#f0782b", "day")
    frm_day_group.grid(row=0, column=0, padx=15, pady=28, sticky="nsew")

    frm_night_group = create_staff_group(frm_top, "夜勤メンバー", "#356bb3", "night")
    frm_night_group.grid(row=0, column=2, padx=15, pady=28, sticky="nsew")

    frm_center = tk.Frame(frm_top, bg=PANEL)
    frm_center.grid(row=0, column=1, sticky="nsew", padx=20, pady=12)

    create_ratio_section()
    create_weekly_table()

def create_bottom_panel():
    global lbl_daily_goal
    frm_bottom = tk.Frame(frm_main, bg=PANEL, highlightbackground=LINE, highlightthickness=4)
    frm_bottom.grid(row=3, column=0, sticky="nsew")
    frm_bottom.grid_columnconfigure(0, minsize=520)
    frm_bottom.grid_columnconfigure(1, weight=1)
    frm_bottom.grid_columnconfigure(2, minsize=330)
    frm_bottom.grid_rowconfigure(0, weight=1)

    frm_left = tk.Frame(frm_bottom, bg=PANEL)
    frm_left.grid(row=0, column=0, sticky="nsew", padx=14, pady=10)
    create_kpi_table(
        frm_left, "直近1時間", 0, 0, "-", "recent"
    ).pack(fill="x")
    create_kpi_table(
        frm_left, "累積生産数", 0, 0, "-", "total"
    ).pack(fill="x", pady=(8, 20))
    frm_control = tk.Frame(frm_left, bg=PANEL)
    frm_control.pack(fill="x", pady=(12, 0))
    tk.Button(
        frm_control,
        text="目標入力",
        **button_style,
    ).grid(row=0, column=0, padx=(10, 18), sticky="w")

    create_table_cell(frm_control, "目標生産数", 0, 1, "white", "#111111", 15, 11)
    # 結果表示時にDBの目標生産数へ更新できるようLabelを保持する
    lbl_daily_goal = create_table_cell(
        frm_control, "-", 0, 2, "white", "#111111", 15, 11
    )

    frm_middle = tk.Frame(frm_bottom, bg=PANEL)
    frm_middle.grid(row=0, column=1, sticky="nsew", padx=14, pady=10)

    create_progress_section(frm_middle)
    label(frm_middle, "号機別生産数", 18, True).pack(anchor="w", pady=(0, 2))
    frm_machine = tk.Frame(frm_middle, bg=PANEL)
    frm_machine.pack(fill="x")
    for c, (name, count) in enumerate(machine_counts):
        create_table_cell(frm_machine, name, 0, c, HEADER, "white", 13, 9)
        create_table_cell(frm_machine, f"{count:,}", 1, c, "white", "#111111", 14, 9)
        frm_machine.grid_columnconfigure(c, weight=1)

    create_bot_section(frm_bottom)

def create_progress_section(frm_middle):
    def make_progress(key, title_text, display_max=125):
        """共通の0～125%スケールで進捗グラフを作成する。"""
        lbl_title = label(frm_middle, title_text, 16, True)
        lbl_title.pack(anchor="w")

        # 2つのグラフは共通の125%スケールを使う
        # 累積側は100%まで表示するため、横幅を全体の80%にする
        width_ratio = display_max / 125

        frm_progress = tk.Frame(frm_middle, bg=PANEL, height=92)
        frm_progress.pack(fill="x", pady=(0, 10))
        frm_progress.pack_propagate(False)

        frm_axis = tk.Frame(frm_progress, bg=PANEL)
        frm_axis.place(relx=0, rely=0, relwidth=width_ratio, height=25)

        percentages = list(range(0, display_max + 1, 25))

        # 目盛りを縦線の位置に正確に合わせるためplace()を使う
        for p in percentages:
            if p == 0:
                anchor = "w"
            elif p == display_max:
                anchor = "e"
            else:
                anchor = "center"

            label(frm_axis, f"{p}%", 13, True).place(
                relx=p / display_max,
                rely=0.5,
                anchor=anchor,
            )

        cvs_progress = tk.Canvas(
            frm_progress,
            bg="white",
            highlightbackground="#555555",
            highlightthickness=3,
        )
        cvs_progress.place(relx=0, y=25, relwidth=width_ratio, height=64)

        # 結果表示時とCanvasのサイズ変更時に再描画できるよう保存
        progress_charts[key] = {
            "title": lbl_title,
            "canvas": cvs_progress,
            "rate": 0,
            "display_max": display_max,
        }
        cvs_progress.bind(
            "<Configure>", lambda event, k=key: draw_progress_chart(k)
        )

    make_progress("recent", "直近1時間", display_max=125)
    make_progress("total", "累積生産数", display_max=100)


def draw_progress_chart(key):
    """保存した達成率をもとに進捗バーと目盛り線を描き直す。"""
    chart = progress_charts[key]
    cvs_progress = chart["canvas"]
    display_max = chart["display_max"]
    rate = chart["rate"]

    cvs_progress.delete("all")
    w, h = cvs_progress.winfo_width(), cvs_progress.winfo_height()
    if w <= 1:
        return

    # 達成率が表示上限を超えた場合は、バーを右端で止める
    # 例：150%のとき、125%スケールでは125%まで塗りつぶす
    bar_ratio = max(0, min(rate / display_max, 1))
    cvs_progress.create_rectangle(
        0, 0, w * bar_ratio, h, fill=PROGRESS, outline=""
    )

    # 25%刻みの目盛り線をバーの上に重ねる
    for p in range(25, display_max + 1, 25):
        x = w * p / display_max
        cvs_progress.create_line(
            x, 0, x, h,
            fill="#666666",
            width=3,
            dash=() if p == display_max else (8, 5),
        )


def update_progress_chart(key, actual, target, title_text):
    """左側KPIと同じ実績・目標から達成率を計算して更新する。"""
    rate = actual / target * 100 if target > 0 else 0
    progress_charts[key]["rate"] = rate
    progress_charts[key]["title"].configure(text=title_text)
    draw_progress_chart(key)


def create_bot_section(frm_bottom):
    global lbl_bot, bot_frames

    frm_bot = tk.Frame(frm_bottom, bg=PANEL)
    frm_bot.grid(row=0, column=2, sticky="nsew", padx=18, pady=10)
    lbl_bot = tk.Label(frm_bot, bg=PANEL)
    lbl_bot.pack(expand=True)
    bot_frames = []

    if BOT_GIF.exists():
        gif = Image.open(BOT_GIF)
        for frame in ImageSequence.Iterator(gif):
            im = frame.convert("RGBA")
            im.thumbnail((300, 300), Image.Resampling.LANCZOS)
            bot_frames.append(ImageTk.PhotoImage(im))

    animate_bot()

def animate_bot(index=0):
    if not bot_frames:
        lbl_bot.configure(text="ANIMATION GIF\nimage/factory_bot.gif", fg=TEXT, font=(FONT, 18, "bold"))
        return
    lbl_bot.configure(image=bot_frames[index])
    root.after(100, animate_bot, (index + 1) % len(bot_frames))

# endregion

# ================================================
# region Event Handlers
# ================================================

def toggle_fullscreen(event=None):
    """Toggle full-screen mode with F11."""
    is_fullscreen = root.attributes("-fullscreen")
    root.attributes("-fullscreen", not is_fullscreen)

def swap_staff():
    for day_combo, night_combo in zip(frm_day_group.combos, frm_night_group.combos):
        day_name = day_combo.get()
        night_name = night_combo.get()

        day_combo.set(night_name)
        night_combo.set(day_name)

        day_combo.event_generate("<<ComboboxSelected>>")
        night_combo.event_generate("<<ComboboxSelected>>")

def save_staff_info():
    STAFF_INFO["day"] = [
        combo.get() for combo in frm_day_group.combos
    ]

    STAFF_INFO["night"] = [
        combo.get() for combo in frm_night_group.combos
    ]

    with open(STAFF_INFO_FILE, "w", encoding="utf-8") as file:
        json.dump(STAFF_INFO, file, ensure_ascii=False, indent=4)

def on_close():
    save_staff_info()
    root.destroy()

def show_results():
    global results_visible, result_photo_modes

    # 現在時刻の前の時間をデフォルト値とする
    now = (datetime.now() - timedelta(hours=1)).replace(
        minute=0, second=0, microsecond=0
    )

    # 基準日時を入力
    date_str = simpledialog.askstring(
        "結果表示",
        "基準日時を入力してください (YYYY-MM-DD HH:MM)",
        initialvalue=now.strftime("%Y-%m-%d %H:%M"),
        parent=root,
    )

    if date_str is None:
        return

    try:
        base_datetime = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        if base_datetime.minute != 0:
            raise ValueError
    except ValueError:
        messagebox.showerror(
            "入力エラー",
            "日時は YYYY-MM-DD HH:00 の形式で入力してください。",
            parent=root,
        )
        return

    # 下段左側の生産実績・目標を取得
    try:
        recent_actual, recent_target, total_actual, total_target = (
            get_production_summary(base_datetime)
        )
    except (sqlite3.Error, ValueError) as error:
        messagebox.showerror("生産データエラー", str(error), parent=root)
        return

    # 先週の同じ曜日・同じ時刻(7日前の同時刻)
    previous_week_datetime = get_previous_week_datetime(base_datetime)

    # 今週・先週の稼働時間を取得
    try:
        this_week_sec = get_operating_time(base_datetime)
        last_week_sec = get_operating_time(previous_week_datetime)
    except sqlite3.Error as error:
        messagebox.showerror("DBエラー", str(error), parent=root)
        return

    # 稼働時間を分単位で表示
    print(
        f"This week ({base_datetime:%Y-%m-%d %H:%M}): "
        f"{this_week_sec / 60:.1f} min"
    )
    print(
        f"Last week ({previous_week_datetime:%Y-%m-%d %H:%M}): "
        f"{last_week_sec / 60:.1f} min"
    )

    # 今週・先週の割合を計算
    total_sec = this_week_sec + last_week_sec

    if total_sec == 0:
        messagebox.showerror(
            "データエラー",
            "今週と先週の稼働時間が両方とも0秒です。",
            parent=root,
        )
        return

    this_week_rate = round(this_week_sec / total_sec * 100)
    last_week_rate = 100 - this_week_rate

    print(f"Ratio: {this_week_rate}% / {last_week_rate}%")

    # 上段グラフのデータを更新
    ratio_specs[0] = (
        f"【直近1時間】"
        f"（{base_datetime:%H:%M}〜"
        f"{base_datetime + timedelta(hours=1):%H:%M}）",
        this_week_rate,
        last_week_rate,
    )

    ratio_targets[0] = this_week_sec / total_sec

    # 今週・先週の累積開始日時
    this_week_start = get_shift_start_datetime(base_datetime)
    last_week_start = get_shift_start_datetime(previous_week_datetime)

    # 今週・先週の累積稼働時間を取得
    try:
        this_week_total = get_cumulative_operating_time(
            this_week_start, base_datetime
        )
        last_week_total = get_cumulative_operating_time(
            last_week_start, previous_week_datetime
        )
    except sqlite3.Error as error:
        messagebox.showerror("DBエラー", str(error), parent=root)
        return

    # 累積稼働時間を分単位で出力
    print(
        f"Cumulative this week: {this_week_total / 60:.1f} min"
    )
    print(
        f"Cumulative last week: {last_week_total / 60:.1f} min"
    )

    # 今週・先週の累積稼働時間比率
    cumulative_total = this_week_total + last_week_total

    if cumulative_total == 0:
        messagebox.showerror(
            "データエラー",
            "今週と先週の累積稼働時間が両方とも0秒です。",
            parent=root,
        )
        return

    this_week_cumulative_rate = round(
        this_week_total / cumulative_total * 100
    )
    last_week_cumulative_rate = 100 - this_week_cumulative_rate

    print(
        f"Cumulative ratio: "
        f"{this_week_cumulative_rate}% / "
        f"{last_week_cumulative_rate}%"
    )

    # 下段グラフのデータを更新
    ratio_specs[1] = (
        f"【全経過時間】"
        f"（{this_week_start:%H:%M}〜"
        f"{base_datetime + timedelta(hours=1):%H:%M}）",
        this_week_cumulative_rate,
        last_week_cumulative_rate,
    )

    ratio_targets[1] = this_week_total / cumulative_total

    # 週間検査数を更新
    try:
        update_weekly_table(base_datetime)
    except sqlite3.Error as error:
        messagebox.showerror("DBエラー", str(error), parent=root)
        return

    # 基準時間の勤務帯と直近1時間の比率で写真の表情を決める
    is_day_shift = 8 <= base_datetime.hour < 20
    if this_week_rate >= 60:
        result_photo_modes = ("smile", "sad") if is_day_shift else ("sad", "smile")
    elif this_week_rate <= 40:
        result_photo_modes = ("sad", "smile") if is_day_shift else ("smile", "sad")
    else:
        result_photo_modes = ("normal", "normal")

    # 生産日は8:00開始。0:00～7:00の基準日時は前日8:00から集計する
    production_date = base_datetime
    if base_datetime.hour < 8:
        production_date -= timedelta(days=1)

    start_datetime = production_date.replace(
        hour=8, minute=0, second=0, microsecond=0
    )
    end_datetime = base_datetime + timedelta(hours=1)

    # 下段左側の見出しに、今回の集計時間を表示する
    kpi_title_labels["recent"].configure(
        text=(
            f"直近1時間（{base_datetime:%H:%M} ～ "
            f"{end_datetime:%H:%M}）"
        )
    )
    kpi_title_labels["total"].configure(
        text=(
            f"累積生産数（{start_datetime:%H:%M} ～ "
            f"{end_datetime:%H:%M}）"
        )
    )

    # 直近1時間の目標は生産日の目標生産数を24で割った値
    # 0:00～7:00の場合も、前日の生産目標が使われる
    daily_goal = round(recent_target * 24)
    lbl_daily_goal.configure(text=f"{daily_goal:,}")

    # 下段左側の生産状況を更新
    update_kpi_table("recent", recent_actual, recent_target)
    update_kpi_table("total", total_actual, total_target)

    # 下段中央の進捗グラフも左側KPIと同じ実績・目標で更新する
    update_progress_chart(
        "recent", recent_actual, recent_target,
        kpi_title_labels["recent"].cget("text"),
    )
    update_progress_chart(
        "total", total_actual, total_target,
        kpi_title_labels["total"].cget("text"),
    )

    # 両方のグラフを表示
    results_visible = True

    lbl_ratio_titles[0].configure(text=ratio_specs[0][0])
    lbl_ratio_titles[1].configure(text=ratio_specs[1][0])

    # ドラムロール再生
    winsound.PlaySound(
        str(DRUM_SOUND),
        winsound.SND_FILENAME | winsound.SND_ASYNC,
    )

    # 2つのグラフを同時にアニメーション
    animate_ratio_bars()

# endregion

# ================================================
# region Main
# ================================================

def initialize_app():
    global root

    root = tk.Tk()
    root.title("可動率勝負")
    root.geometry(f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}")
    root.configure(bg=BG)
    root.attributes("-fullscreen", True)

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("Staff.TCombobox", font=(FONT, 11), padding=2)
    root.option_add("*TCombobox*Listbox.font", (FONT, 11))

def create_main_layout():
    global frm_main

    frm_main = tk.Frame(root, bg=BG)
    frm_main.pack(fill="both", expand=True, padx=15, pady=12)
    frm_main.grid_columnconfigure(0, weight=1)
    frm_main.grid_rowconfigure(1, weight=50)    # 1行目=上段パネル(可動率勝負)
    frm_main.grid_rowconfigure(3, weight=50)    # 3行目=下段パネル(生産数表示)

    create_header()
    create_top_panel()
    # separator title
    label(frm_main, "本日の生産状況", 26, True, bg=BG).grid(row=2, column=0, sticky="w", pady=(8, 3))

    create_bottom_panel()

def setup_events():
    btn_result.configure(command=show_results)
    root.bind("<F11>", toggle_fullscreen)
    root.bind("<Escape>", lambda event: root.attributes("-fullscreen", False))
    root.protocol("WM_DELETE_WINDOW", on_close)

def main():
    global STAFF_INFO, STAFF_NAMES

    with open(STAFF_INFO_FILE, encoding="utf-8") as file:
        STAFF_INFO = json.load(file)
    STAFF_NAMES = ["NAME"] + list(STAFF_INFO["staff"].keys())

    initialize_app()
    create_main_layout()
    setup_events()
    root.mainloop()


if __name__ == "__main__":
    main()

# endregion

