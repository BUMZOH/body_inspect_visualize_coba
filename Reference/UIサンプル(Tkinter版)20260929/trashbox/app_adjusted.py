import math
import tkinter as tk
from tkinter import ttk
from pathlib import Path

try:
    from PIL import Image, ImageTk, ImageSequence
except ImportError:
    Image = ImageTk = ImageSequence = None

# ============================================================
# Settings
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "image"
BOT_GIF = IMAGE_DIR / "factory_bot.gif"

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

FONT = "Yu Gothic"
STAFF_NAMES = ["NAME", "佐藤", "鈴木", "高橋", "田中", "伊藤", "山本", "渡辺", "中村"]
DAY_PHOTOS = [IMAGE_DIR / f"day_{i}.png" for i in range(1, 7)]
NIGHT_PHOTOS = [IMAGE_DIR / f"night_{i}.png" for i in range(1, 7)]

# Sample values shown in the reference layout
recent_this_week = 60
recent_last_week = 40
total_this_week = 52
total_last_week = 48
weekly_day = [3250, 3740, 3200, 3700, "", ""]
weekly_night = [3420, 3860, 2890, "", "", ""]
actual_recent = 13535
target_recent = 13500
actual_total = 155000
target_total = 150000
machine_counts = [("No.412", 3457), ("No.413", 3123), ("No.416", 2544), ("No.421", 957), ("No.428", 2884)]

# ============================================================
# Root / style
# ============================================================
root = tk.Tk()
root.title("稼働率勝負")
root.geometry(f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}")
root.configure(bg=BG)
root.attributes("-fullscreen", True)
root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))

style = ttk.Style(root)
try:
    style.theme_use("clam")
except tk.TclError:
    pass
style.configure("Staff.TCombobox", font=(FONT, 11), padding=2)
root.option_add("*TCombobox*Listbox.font", (FONT, 11))

# ============================================================
# Helpers
# ============================================================
def label(parent, text="", size=16, bold=False, fg=TEXT, bg=PANEL, **kwargs):
    return tk.Label(parent, text=text, font=(FONT, size, "bold" if bold else "normal"), fg=fg, bg=bg, **kwargs)


def load_photo(path, size=(105, 118)):
    if Image is None or not path.exists():
        return None
    im = Image.open(path).convert("RGB")
    im.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, "white")
    x = (size[0] - im.width) // 2
    y = (size[1] - im.height) // 2
    canvas.paste(im, (x, y))
    return ImageTk.PhotoImage(canvas)


def create_staff_group(parent, title, title_color, photo_paths):
    box = tk.Frame(parent, bg=PANEL, highlightbackground=LINE, highlightthickness=2)
    label(box, title, 18, True, title_color).pack(pady=(0, 8))
    grid = tk.Frame(box, bg=PANEL)
    grid.pack(padx=7, pady=(0, 7))
    refs = []
    for i in range(6):
        card = tk.Frame(grid, width=112, height=154, bg=PANEL, highlightbackground=LINE, highlightthickness=1)
        card.grid(row=i // 3, column=i % 3, padx=0, pady=0)
        card.grid_propagate(False)
        photo = load_photo(photo_paths[i])
        if photo:
            pic = tk.Label(card, image=photo, bg="white")
            refs.append(photo)
        else:
            pic = tk.Label(card, text="PHOTO", bg="#eeeeee", fg="#888888", font=(FONT, 12, "bold"))
        pic.pack(fill="both", expand=True)
        combo = ttk.Combobox(card, values=STAFF_NAMES, state="readonly", style="Staff.TCombobox", justify="center")
        combo.set("NAME")
        combo.pack(fill="x")
    box._photo_refs = refs
    return box


def create_table_cell(parent, text, row, col, bg="white", fg="#111111", size=15, width=10, bold=True):
    w = tk.Label(parent, text=text, bg=bg, fg=fg, font=(FONT, size, "bold" if bold else "normal"),
                 relief="solid", borderwidth=1, width=width, pady=7)
    w.grid(row=row, column=col, sticky="nsew")
    return w


def create_kpi_table(parent, title_text, actual, target, status):
    block = tk.Frame(parent, bg=PANEL)
    label(block, title_text, 18, True).pack(anchor="w", pady=(0, 2))
    table = tk.Frame(block, bg=PANEL)
    table.pack(fill="x")
    for c, h in enumerate(["実 績", "目 標", "達成率", "進捗"]):
        create_table_cell(table, h, 0, c, HEADER, "white", 14, 9)
    rate = round(actual / target * 100) if target else 0
    vals = [f"{actual:,}", f"{target:,}", f"{rate}%", status]
    for c, v in enumerate(vals):
        create_table_cell(table, v, 1, c, "white", "#111111", 14, 9)
        table.grid_columnconfigure(c, weight=1)
    return block

# ============================================================
# Main layout
# ============================================================
main = tk.Frame(root, bg=BG)
main.pack(fill="both", expand=True, padx=15, pady=12)
main.grid_columnconfigure(0, weight=1)
main.grid_rowconfigure(1, weight=50)
main.grid_rowconfigure(3, weight=50)

# Top title row
head = tk.Frame(main, bg=BG)
head.grid(row=0, column=0, sticky="ew", pady=(0, 6))
head.grid_columnconfigure(0, weight=1)
label(head, "稼働率勝負", 28, True, bg=BG).grid(row=0, column=0, sticky="w")
button_style = dict(font=(FONT, 15), padx=28, pady=7, relief="ridge", borderwidth=2)
tk.Button(head, text="結果表示", **button_style).grid(row=0, column=1, padx=5)
tk.Button(head, text="メンバ入替", **button_style).grid(row=0, column=2, padx=5)

# ============================================================
# Top panel
# ============================================================
top = tk.Frame(main, bg=PANEL, highlightbackground=LINE, highlightthickness=4)
top.grid(row=1, column=0, sticky="nsew")
top.grid_columnconfigure(0, minsize=350)
top.grid_columnconfigure(1, weight=1)
top.grid_columnconfigure(2, minsize=350)
top.grid_rowconfigure(0, weight=1)

day_group = create_staff_group(top, "昼勤メンバー", "#f0782b", DAY_PHOTOS)
day_group.grid(row=0, column=0, padx=15, pady=28, sticky="nsew")
night_group = create_staff_group(top, "夜勤メンバー", "#356bb3", NIGHT_PHOTOS)
night_group.grid(row=0, column=2, padx=15, pady=28, sticky="nsew")

center = tk.Frame(top, bg=PANEL)
center.grid(row=0, column=1, sticky="nsew", padx=20, pady=12)
center.grid_columnconfigure(0, weight=1)

# Animated ratio bars
ratio_canvases = []
ratio_specs = [("【直近1時間】（18：00〜19：00）", recent_this_week, recent_last_week),
               ("【全経過時間】（8：00〜19：00）", total_this_week, total_last_week)]
animated_ratios = [0.5, 0.5]
ratio_targets = [a / (a + b) if a + b else 0.5 for _, a, b in ratio_specs]

def draw_ratio(index):
    canvas = ratio_canvases[index]
    canvas.delete("all")
    w, h = canvas.winfo_width(), canvas.winfo_height()
    if w <= 1:
        return
    split = w * animated_ratios[index]
    canvas.create_rectangle(0, 0, split, h, fill=DAY, outline="")
    canvas.create_rectangle(split, 0, w, h, fill=NIGHT, outline="")
    _, left, right = ratio_specs[index]
    canvas.create_text(24, h / 2, text=f"{left} %", anchor="w", fill="white", font=(FONT, 21, "bold"))
    canvas.create_text(w - 24, h / 2, text=f"{right} %", anchor="e", fill="black", font=(FONT, 21, "bold"))


def animate_ratios(step=0):
    total_steps = 36
    if step >= total_steps:
        for i, target in enumerate(ratio_targets):
            animated_ratios[i] = target
            draw_ratio(i)
        root.after(5000, animate_ratios, 0)
        return
    progress = step / total_steps
    ease = 1 - (1 - progress) ** 3
    wobble = math.sin(step * 1.25) * 0.035 * (1 - progress)
    for i, target in enumerate(ratio_targets):
        animated_ratios[i] = 0.5 + (target - 0.5) * ease + wobble * (1 if i == 0 else -1)
        animated_ratios[i] = max(0.08, min(0.92, animated_ratios[i]))
        draw_ratio(i)
    root.after(70, animate_ratios, step + 1)

for i, (title, _, _) in enumerate(ratio_specs):
    label(center, title, 19, True).pack(pady=(0 if i == 0 else 18, 4))
    row = tk.Frame(center, bg=PANEL)
    row.pack(fill="x")
    label(row, "今週", 17, True).pack(side="left", padx=(0, 10))
    c = tk.Canvas(row, height=68, bg="white", highlightbackground="#222222", highlightthickness=2)
    c.pack(side="left", fill="x", expand=True)
    label(row, "先週", 17, True).pack(side="left", padx=(10, 0))
    ratio_canvases.append(c)
    c.bind("<Configure>", lambda e, idx=i: draw_ratio(idx))

# Weekly inspection table
label(center, "週間検査数", 17, True).pack(anchor="w", pady=(10, 0))
weekly = tk.Frame(center, bg=PANEL)
weekly.pack(fill="x")
headers = ["", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
for c, h in enumerate(headers):
    create_table_cell(weekly, h, 0, c, "white" if c == 0 else HEADER, "white" if c else TEXT, 14, 9)
for r, (shift, vals) in enumerate([("昼 勤", weekly_day), ("夜 勤", weekly_night)], start=1):
    create_table_cell(weekly, shift, r, 0, HEADER, "white", 14, 9)
    for c, v in enumerate(vals, start=1):
        cell = create_table_cell(weekly, str(v), r, c, "white", "#111111", 14, 9)
        if c == 4:
            cell.configure(highlightbackground=ACCENT, highlightthickness=3)
for c in range(7):
    weekly.grid_columnconfigure(c, weight=1)

# separator title
label(main, "本日の生産状況", 26, True, bg=BG).grid(row=2, column=0, sticky="w", pady=(8, 3))

# ============================================================
# Bottom panel
# ============================================================
bottom = tk.Frame(main, bg=PANEL, highlightbackground=LINE, highlightthickness=4)
bottom.grid(row=3, column=0, sticky="nsew")
bottom.grid_columnconfigure(0, minsize=520)
bottom.grid_columnconfigure(1, weight=1)
bottom.grid_columnconfigure(2, minsize=330)
bottom.grid_rowconfigure(0, weight=1)

left = tk.Frame(bottom, bg=PANEL)
left.grid(row=0, column=0, sticky="nsew", padx=14, pady=10)
create_kpi_table(left, "直近1時間（18：00〜19：00）", actual_recent, target_recent, "順調").pack(fill="x")
create_kpi_table(left, "累積生産数（8：00〜19：00）", actual_total, target_total, "超順調").pack(fill="x", pady=(8, 20))
control = tk.Frame(left, bg=PANEL)
control.pack(fill="x", side="bottom")
tk.Button(
    control,
    text="目標入力",
    font=(FONT, 15),
    padx=32,
    pady=8,
).grid(row=0, column=0, padx=(10, 18), sticky="w")

create_table_cell(control, "目標生産数", 0, 1, "white", "#111111", 15, 11)
create_table_cell(control, "300000", 0, 2, "white", "#111111", 15, 11)

mid = tk.Frame(bottom, bg=PANEL)
mid.grid(row=0, column=1, sticky="nsew", padx=14, pady=10)

def make_progress(title_text, value, max_value=125):
    label(mid, title_text, 16, True).pack(anchor="w")
    axis = tk.Frame(mid, bg=PANEL)
    axis.pack(fill="x")
    for c, t in enumerate(["0%", "25%", "50%", "75%", "100%", "125%"]):
        axis.grid_columnconfigure(c, weight=1)
        label(axis, t, 13, True).grid(row=0, column=c)
    cv = tk.Canvas(mid, height=64, bg="white", highlightbackground="#555555", highlightthickness=3)
    cv.pack(fill="x", pady=(0, 10))
    def draw(e=None):
        cv.delete("all")
        w, h = cv.winfo_width(), cv.winfo_height()
        cv.create_rectangle(0, 0, w * min(value / max_value, 1), h, fill=PROGRESS, outline="")
        for p in (25, 50, 75, 100):
            x = w * p / max_value
            cv.create_line(x, 0, x, h, fill="#666666", width=3, dash=() if p == 100 else (8, 5))
    cv.bind("<Configure>", draw)

make_progress("直近1時間（18：00〜19：00）", 113)
make_progress("累積生産数（8：00〜19：00）", 105)
label(mid, "号機別生産数", 18, True).pack(anchor="w", pady=(0, 2))
machine = tk.Frame(mid, bg=PANEL)
machine.pack(fill="x")
for c, (name, count) in enumerate(machine_counts):
    create_table_cell(machine, name, 0, c, HEADER, "white", 13, 9)
    create_table_cell(machine, f"{count:,}", 1, c, "white", "#111111", 14, 9)
    machine.grid_columnconfigure(c, weight=1)

# ============================================================
# Animated GIF (single GIF file, self-managed frames)
# ============================================================
bot_area = tk.Frame(bottom, bg=PANEL)
bot_area.grid(row=0, column=2, sticky="nsew", padx=18, pady=10)
bot_label = tk.Label(bot_area, bg=PANEL)
bot_label.pack(expand=True)
bot_frames = []

if Image is not None and BOT_GIF.exists():
    gif = Image.open(BOT_GIF)
    for frame in ImageSequence.Iterator(gif):
        im = frame.convert("RGBA")
        im.thumbnail((300, 300), Image.Resampling.LANCZOS)
        bot_frames.append(ImageTk.PhotoImage(im))

def animate_bot(index=0):
    if not bot_frames:
        bot_label.configure(text="ANIMATION GIF\nimage/factory_bot.gif", fg=TEXT, font=(FONT, 18, "bold"))
        return
    bot_label.configure(image=bot_frames[index])
    root.after(100, animate_bot, (index + 1) % len(bot_frames))

animate_bot()
root.after(300, animate_ratios, 0)
root.mainloop()
