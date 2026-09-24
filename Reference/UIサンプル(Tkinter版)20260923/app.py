import random
import tkinter as tk
from datetime import datetime
from pathlib import Path


# ============================================================
# Settings
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "image"

BOT_IMAGE_1 = IMAGE_DIR / "factory_bot_1.gif"
BOT_IMAGE_2 = IMAGE_DIR / "factory_bot_2.gif"

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

BG_COLOR = "#f4f4f2"
PANEL_COLOR = "#ffffff"
TEXT_COLOR = "#4d4d4d"
LINE_COLOR = "#707070"
SOFT_LINE_COLOR = "#bdbdbd"
HEADER_COLOR = "#aaaaaa"

DAY_COLOR = "#d2a300"
NIGHT_COLOR = "#2e5f8a"
PROGRESS_COLOR = "#94addc"
ACCENT_RED = "#ff5a5a"

BOT_INTERVAL = 500


# ============================================================
# Sample data
# ============================================================
day_staff = ["A", "B", "C", "D", "E", ""]
night_staff = ["F", "G", "H", "I", "J", ""]

day_minutes = 145
night_minutes = 156

elapsed_time = "3:45"

actual_today = 12535
target_today = 13500
achievement_today = 83

actual_total = 12535
target_total = 300000
achievement_total = 5

machines = [
    ("MC557", 3457),
    ("MC560", 3123),
    ("MC577", 2544),
    ("MC595", 957),
    ("MC603", 2884),
]


# ============================================================
# Root window
# ============================================================
root = tk.Tk()

root.title("Factory Visualization Dashboard")
root.geometry(f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}")
root.configure(bg=BG_COLOR)

# Full screen
root.attributes("-fullscreen", True)

# Esc: exit full screen
root.bind(
    "<Escape>",
    lambda event: root.attributes("-fullscreen", False),
)


# ============================================================
# Utility functions
# ============================================================
def create_staff_area(parent, title, staff_list):
    """Create a DAY/NIGHT staff area."""
    frame = tk.Frame(parent, bg=PANEL_COLOR)

    title_label = tk.Label(
        frame,
        text=title,
        bg=PANEL_COLOR,
        fg=TEXT_COLOR,
        font=("Yu Gothic", 20, "bold"),
    )
    title_label.pack(pady=(0, 8))

    grid_frame = tk.Frame(frame, bg=PANEL_COLOR)
    grid_frame.pack()

    for index, staff in enumerate(staff_list):
        row = index // 3
        column = index % 3

        card = tk.Frame(
            grid_frame,
            width=75,
            height=110,
            bg="#fafafa",
            highlightbackground="#888888",
            highlightthickness=2,
        )
        card.grid(
            row=row,
            column=column,
            padx=3,
            pady=3,
        )
        card.grid_propagate(False)

        photo = tk.Label(
            card,
            text=staff if staff else "—",
            bg="#eeeeee",
            fg="#777777",
            font=("Yu Gothic", 28, "bold"),
        )
        photo.pack(fill="both", expand=True)

        name = tk.Label(
            card,
            text="NAME" if staff else "",
            bg="#fafafa",
            fg=TEXT_COLOR,
            font=("Yu Gothic", 9, "bold"),
        )
        name.pack(fill="x")

    return frame


def create_cell(
    parent,
    text,
    row,
    column,
    *,
    bg="white",
    fg=TEXT_COLOR,
    font_size=18,
    bold=True,
    width=10,
):
    """Create one table-like cell."""
    label = tk.Label(
        parent,
        text=text,
        bg=bg,
        fg=fg,
        width=width,
        height=2,
        font=(
            "Yu Gothic",
            font_size,
            "bold" if bold else "normal",
        ),
        relief="solid",
        borderwidth=1,
    )

    label.grid(
        row=row,
        column=column,
        sticky="nsew",
    )

    return label


# ============================================================
# Main dashboard
# ============================================================
dashboard = tk.Frame(
    root,
    bg=BG_COLOR,
)

dashboard.pack(
    fill="both",
    expand=True,
    padx=25,
    pady=20,
)

dashboard.grid_rowconfigure(0, weight=1)
dashboard.grid_rowconfigure(1, weight=1)
dashboard.grid_columnconfigure(0, weight=1)


# ============================================================
# OPERATING TIME panel
# ============================================================
operating_panel = tk.Frame(
    dashboard,
    bg=PANEL_COLOR,
    highlightbackground="#8a8a8a",
    highlightthickness=4,
)

operating_panel.grid(
    row=0,
    column=0,
    sticky="nsew",
    pady=(0, 18),
)

operating_panel.grid_rowconfigure(1, weight=1)
operating_panel.grid_columnconfigure(0, weight=1)


# ------------------------------------------------------------
# Operating header
# ------------------------------------------------------------
operating_header = tk.Frame(
    operating_panel,
    bg=PANEL_COLOR,
)

operating_header.grid(
    row=0,
    column=0,
    sticky="ew",
    padx=15,
    pady=(5, 0),
)

operating_header.grid_columnconfigure(0, weight=1)

title_frame = tk.Frame(
    operating_header,
    bg=PANEL_COLOR,
)
title_frame.grid(row=0, column=0, sticky="w")

tk.Label(
    title_frame,
    text="OPERATING TIME",
    bg=PANEL_COLOR,
    fg=TEXT_COLOR,
    font=("Yu Gothic", 30, "bold"),
).pack(side="left")

tk.Label(
    title_frame,
    text="稼働時間",
    bg=PANEL_COLOR,
    fg=TEXT_COLOR,
    font=("Yu Gothic", 18, "bold"),
).pack(
    side="left",
    padx=(12, 0),
)

last_update_label = tk.Label(
    operating_header,
    text="",
    bg=PANEL_COLOR,
    fg=TEXT_COLOR,
    font=("Yu Gothic", 14, "bold"),
)

last_update_label.grid(
    row=0,
    column=1,
    sticky="e",
)


# ------------------------------------------------------------
# Operating content
# ------------------------------------------------------------
operating_content = tk.Frame(
    operating_panel,
    bg=PANEL_COLOR,
)

operating_content.grid(
    row=1,
    column=0,
    sticky="nsew",
    padx=25,
    pady=10,
)

operating_content.grid_columnconfigure(0, minsize=260)
operating_content.grid_columnconfigure(1, weight=1)
operating_content.grid_columnconfigure(2, minsize=260)
operating_content.grid_rowconfigure(0, weight=1)


# DAY SHIFT
day_staff_frame = create_staff_area(
    operating_content,
    "DAY SHIFT",
    day_staff,
)

day_staff_frame.grid(
    row=0,
    column=0,
    sticky="n",
)


# ------------------------------------------------------------
# Operating center
# ------------------------------------------------------------
operating_main = tk.Frame(
    operating_content,
    bg=PANEL_COLOR,
)

operating_main.grid(
    row=0,
    column=1,
    sticky="nsew",
    padx=20,
)

tk.Label(
    operating_main,
    text=f"ELAPSED TIME = {elapsed_time}",
    bg=PANEL_COLOR,
    fg=TEXT_COLOR,
    font=("Yu Gothic", 16, "bold"),
).pack(pady=(0, 5))


# ------------------------------------------------------------
# DAY / NIGHT ratio
# ------------------------------------------------------------
ratio_canvas = tk.Canvas(
    operating_main,
    height=125,
    bg="white",
    highlightthickness=2,
    highlightbackground="#444444",
)

ratio_canvas.pack(
    fill="x",
    padx=5,
)

total_minutes = day_minutes + night_minutes

if total_minutes:
    day_ratio = day_minutes / total_minutes
else:
    day_ratio = 0.5


# Animation state
ratio_animation_running = False
animated_day_ratio = day_ratio


def draw_ratio_bar(event=None):
    """Draw the DAY/NIGHT operating-time ratio."""
    ratio_canvas.delete("all")

    width = ratio_canvas.winfo_width()
    height = ratio_canvas.winfo_height()

    if width <= 1:
        return

    day_width = width * animated_day_ratio

    ratio_canvas.create_rectangle(
        0,
        0,
        day_width,
        height,
        fill=DAY_COLOR,
        outline="",
    )

    ratio_canvas.create_rectangle(
        day_width,
        0,
        width,
        height,
        fill=NIGHT_COLOR,
        outline="",
    )

    # Keep the displayed values fixed at the actual ratio.
    # Only the DAY/NIGHT boundary moves during animation.
    ratio_canvas.create_text(
        20,
        height / 2 - 18,
        text=f"{day_minutes} min",
        anchor="w",
        fill="white",
        font=("Yu Gothic", 23, "bold"),
    )

    ratio_canvas.create_text(
        20,
        height / 2 + 20,
        text=f"{day_ratio * 100:.0f}%",
        anchor="w",
        fill="white",
        font=("Yu Gothic", 23, "bold"),
    )

    ratio_canvas.create_text(
        width - 20,
        height / 2 - 18,
        text=f"{night_minutes} min",
        anchor="e",
        fill="white",
        font=("Yu Gothic", 23, "bold"),
    )

    ratio_canvas.create_text(
        width - 20,
        height / 2 + 20,
        text=f"{(1 - day_ratio) * 100:.0f}%",
        anchor="e",
        fill="white",
        font=("Yu Gothic", 23, "bold"),
    )


def start_ratio_animation():
    """Start the DAY/NIGHT boundary animation."""
    global ratio_animation_running

    if ratio_animation_running:
        return

    ratio_animation_running = True

    animation_button.configure(
        state="disabled",
        text="ANIMATING...",
    )

    animate_ratio_step(0)


def animate_ratio_step(step):
    """Shake the boundary, then settle at the actual DAY ratio."""
    global animated_day_ratio
    global ratio_animation_running

    total_steps = 30

    if step >= total_steps:
        animated_day_ratio = day_ratio
        ratio_animation_running = False

        draw_ratio_bar()

        animation_button.configure(
            state="normal",
            text="ANIMATION TEST",
        )
        return

    remaining = 1 - step / total_steps

    # Maximum swing starts at +/-8% and gradually approaches zero.
    max_swing = 0.08 * remaining
    offset = random.uniform(-max_swing, max_swing)

    animated_day_ratio = day_ratio + offset

    # Keep the boundary away from the extreme edges.
    animated_day_ratio = max(
        0.15,
        min(animated_day_ratio, 0.85),
    )

    draw_ratio_bar()

    root.after(
        100,
        animate_ratio_step,
        step + 1,
    )


ratio_canvas.bind("<Configure>", draw_ratio_bar)

# Temporary button for checking the boundary animation.
animation_button = tk.Button(
    operating_header,
    text="ANIMATION TEST",
    command=start_ratio_animation,
    font=("Yu Gothic", 11, "bold"),
    padx=12,
    pady=3,
)

animation_button.grid(
    row=0,
    column=2,
    padx=(15, 0),
)


# ------------------------------------------------------------
# Weekly table
# ------------------------------------------------------------
tk.Label(
    operating_main,
    text="累積生産数",
    bg=PANEL_COLOR,
    fg=TEXT_COLOR,
    font=("Yu Gothic", 15, "bold"),
).pack(
    anchor="w",
    padx=5,
    pady=(8, 2),
)

weekly_frame = tk.Frame(
    operating_main,
    bg=PANEL_COLOR,
)

weekly_frame.pack(
    fill="x",
    padx=5,
)

week_headers = ["", "Fri", "Mon", "Tue", "Wed", "Thu", "Fri"]
day_values = ["DAY", "432", "454", "407", "470", "0", "0"]
night_values = ["NIGHT", "447", "430", "442", "156", "0", "0"]

for column, value in enumerate(week_headers):
    create_cell(
        weekly_frame,
        value,
        0,
        column,
        bg="white" if column == 0 else HEADER_COLOR,
        fg="white" if column != 0 else TEXT_COLOR,
        font_size=14,
        width=8,
    )

for column, value in enumerate(day_values):
    label = create_cell(
        weekly_frame,
        value,
        1,
        column,
        bg=HEADER_COLOR if column == 0 else "white",
        fg="white" if column == 0 else TEXT_COLOR,
        font_size=15,
        width=8,
    )

    if column == 4:
        label.configure(
            highlightbackground=ACCENT_RED,
            highlightthickness=3,
        )

for column, value in enumerate(night_values):
    label = create_cell(
        weekly_frame,
        value,
        2,
        column,
        bg=HEADER_COLOR if column == 0 else "white",
        fg="white" if column == 0 else TEXT_COLOR,
        font_size=15,
        width=8,
    )

    if column == 4:
        label.configure(
            highlightbackground=ACCENT_RED,
            highlightthickness=3,
        )

for column in range(7):
    weekly_frame.grid_columnconfigure(column, weight=1)


# NIGHT SHIFT
night_staff_frame = create_staff_area(
    operating_content,
    "NIGHT SHIFT",
    night_staff,
)

night_staff_frame.grid(
    row=0,
    column=2,
    sticky="n",
)


# ============================================================
# TODAY'S PRODUCTION panel
# ============================================================
production_panel = tk.Frame(
    dashboard,
    bg=PANEL_COLOR,
    highlightbackground="#8a8a8a",
    highlightthickness=4,
)

production_panel.grid(
    row=1,
    column=0,
    sticky="nsew",
)

production_panel.grid_rowconfigure(1, weight=1)
production_panel.grid_columnconfigure(0, weight=1)


# ------------------------------------------------------------
# Production header
# ------------------------------------------------------------
production_header = tk.Frame(
    production_panel,
    bg=PANEL_COLOR,
)

production_header.grid(
    row=0,
    column=0,
    sticky="ew",
    padx=15,
    pady=(5, 0),
)

tk.Label(
    production_header,
    text="TODAY'S PRODUCTION",
    bg=PANEL_COLOR,
    fg=TEXT_COLOR,
    font=("Yu Gothic", 30, "bold"),
).pack(side="left")

tk.Label(
    production_header,
    text="本日の生産状況",
    bg=PANEL_COLOR,
    fg=TEXT_COLOR,
    font=("Yu Gothic", 18, "bold"),
).pack(
    side="left",
    padx=(12, 0),
)


# ------------------------------------------------------------
# Production content
# ------------------------------------------------------------
production_content = tk.Frame(
    production_panel,
    bg=PANEL_COLOR,
)

production_content.grid(
    row=1,
    column=0,
    sticky="nsew",
    padx=35,
    pady=10,
)

production_content.grid_columnconfigure(0, minsize=390)
production_content.grid_columnconfigure(1, weight=1)
production_content.grid_columnconfigure(2, minsize=300)
production_content.grid_rowconfigure(0, weight=1)


# ============================================================
# KPI area
# ============================================================
kpi_area = tk.Frame(
    production_content,
    bg=PANEL_COLOR,
)

kpi_area.grid(
    row=0,
    column=0,
    sticky="nsew",
    padx=(0, 20),
)


def create_kpi_block(
    parent,
    title,
    actual,
    target,
    achievement,
):
    """Create one KPI table."""
    block = tk.Frame(
        parent,
        bg=PANEL_COLOR,
    )

    tk.Label(
        block,
        text=title,
        bg=PANEL_COLOR,
        fg=TEXT_COLOR,
        font=("Yu Gothic", 15, "bold"),
    ).pack(
        anchor="w",
        pady=(0, 3),
    )

    table = tk.Frame(
        block,
        bg=PANEL_COLOR,
    )
    table.pack(fill="x")

    headers = ["実 績", "目 標", "達成率"]
    values = [
        f"{actual:,}",
        f"{target:,}",
        f"{achievement}%",
    ]

    for column, value in enumerate(headers):
        create_cell(
            table,
            value,
            0,
            column,
            bg=HEADER_COLOR,
            fg="white",
            font_size=15,
            width=8,
        )

    for column, value in enumerate(values):
        create_cell(
            table,
            value,
            1,
            column,
            bg="white",
            fg=TEXT_COLOR,
            font_size=18,
            width=8,
        )

    for column in range(3):
        table.grid_columnconfigure(
            column,
            weight=1,
        )

    return block


today_kpi = create_kpi_block(
    kpi_area,
    "経過時間生産数",
    actual_today,
    target_today,
    achievement_today,
)

today_kpi.pack(
    fill="x",
    pady=(20, 25),
)

total_kpi = create_kpi_block(
    kpi_area,
    "累積生産数",
    actual_total,
    target_total,
    achievement_total,
)

total_kpi.pack(fill="x")


# ============================================================
# Production center
# ============================================================
production_main = tk.Frame(
    production_content,
    bg=PANEL_COLOR,
)

production_main.grid(
    row=0,
    column=1,
    sticky="nsew",
)

tk.Label(
    production_main,
    text=f"ELAPSED TIME = {elapsed_time}",
    bg=PANEL_COLOR,
    fg=TEXT_COLOR,
    font=("Yu Gothic", 16, "bold"),
).pack(pady=(0, 2))


# ------------------------------------------------------------
# Progress axis
# ------------------------------------------------------------
axis_frame = tk.Frame(
    production_main,
    bg=PANEL_COLOR,
)

axis_frame.pack(
    fill="x",
    padx=5,
)

for column, value in enumerate(
    ["0%", "25%", "50%", "75%", "100%", "125%"]
):
    axis_frame.grid_columnconfigure(column, weight=1)

    tk.Label(
        axis_frame,
        text=value,
        bg=PANEL_COLOR,
        fg=TEXT_COLOR,
        font=("Yu Gothic", 12, "bold"),
    ).grid(
        row=0,
        column=column,
    )


# ------------------------------------------------------------
# Production progress
# ------------------------------------------------------------
progress_canvas = tk.Canvas(
    production_main,
    height=135,
    bg="white",
    highlightbackground="#666666",
    highlightthickness=4,
)

progress_canvas.pack(
    fill="x",
    padx=5,
)


def draw_progress(event=None):
    """Draw production achievement progress."""
    progress_canvas.delete("all")

    width = progress_canvas.winfo_width()
    height = progress_canvas.winfo_height()

    if width <= 1:
        return

    progress_ratio = min(
        achievement_today / 125,
        1,
    )

    progress_canvas.create_rectangle(
        0,
        0,
        width * progress_ratio,
        height,
        fill=PROGRESS_COLOR,
        outline="",
    )

    for percentage in [25, 50, 75, 100]:
        x = width * percentage / 125

        progress_canvas.create_line(
            x,
            0,
            x,
            height,
            fill="#666666",
            width=3,
            dash=() if percentage == 100 else (8, 6),
        )


progress_canvas.bind(
    "<Configure>",
    draw_progress,
)


# ------------------------------------------------------------
# Machine production
# ------------------------------------------------------------
tk.Label(
    production_main,
    text="機械別生産数",
    bg=PANEL_COLOR,
    fg=TEXT_COLOR,
    font=("Yu Gothic", 15, "bold"),
).pack(
    anchor="w",
    padx=5,
    pady=(8, 2),
)

machine_frame = tk.Frame(
    production_main,
    bg=PANEL_COLOR,
)

machine_frame.pack(
    fill="x",
    padx=5,
)

for column, (machine_name, count) in enumerate(machines):
    card = tk.Frame(
        machine_frame,
        bg="white",
        relief="solid",
        borderwidth=1,
    )

    card.grid(
        row=0,
        column=column,
        sticky="nsew",
    )

    machine_frame.grid_columnconfigure(
        column,
        weight=1,
    )

    tk.Label(
        card,
        text=machine_name,
        bg=HEADER_COLOR,
        fg="white",
        font=("Yu Gothic", 15, "bold"),
        pady=6,
    ).pack(fill="x")

    tk.Label(
        card,
        text=f"{count:,}",
        bg="white",
        fg=TEXT_COLOR,
        font=("Yu Gothic", 18, "bold"),
        pady=8,
    ).pack(fill="x")


# ============================================================
# Factory bot
# ============================================================
bot_area = tk.Frame(
    production_content,
    bg=PANEL_COLOR,
)

bot_area.grid(
    row=0,
    column=2,
    sticky="nsew",
    padx=(25, 0),
)

tk.Label(
    bot_area,
    text="👍 Good Job!",
    bg=PANEL_COLOR,
    fg=TEXT_COLOR,
    font=("Yu Gothic", 20, "bold"),
).pack(pady=(10, 5))

bot_label = tk.Label(
    bot_area,
    bg=PANEL_COLOR,
    fg=TEXT_COLOR,
)

bot_label.pack(
    expand=True,
)


# ------------------------------------------------------------
# Load the two GIF images
# ------------------------------------------------------------
bot_images = []

for image_path in [
    BOT_IMAGE_1,
    BOT_IMAGE_2,
]:
    if image_path.exists():
        bot_images.append(
            tk.PhotoImage(file=image_path)
        )


def animate_bot(index=0):
    """Switch between the two GIF images."""
    if not bot_images:
        bot_label.configure(
            text="⚙\nFACTORY BOT",
            font=("Yu Gothic", 24, "bold"),
        )
        return

    bot_label.configure(
        image=bot_images[index],
    )

    next_index = (index + 1) % len(bot_images)

    root.after(
        BOT_INTERVAL,
        animate_bot,
        next_index,
    )


animate_bot()


# ============================================================
# Clock
# ============================================================
def update_clock():
    """Update the last-update display."""
    now = datetime.now()

    last_update_label.configure(
        text=f"LAST UPDATE: {now:%Y/%m/%d %H:%M}"
    )

    root.after(
        60_000,
        update_clock,
    )


update_clock()


# ============================================================
# Start application
# ============================================================
root.mainloop()
