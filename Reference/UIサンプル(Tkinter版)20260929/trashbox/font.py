import tkinter as tk
from tkinter import font

root = tk.Tk()

for name in sorted(font.families()):
    if "デジタル" in name or "UD" in name:
        print(name)

root.destroy()