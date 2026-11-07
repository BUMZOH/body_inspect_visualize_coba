import tkinter as tk

from PIL import Image, ImageTk


GIF_PATH = "crystal.gif"


root = tk.Tk()
root.title("Animated GIF Test")
root.geometry("500x500")


# ================================================
#   Load GIF
# ================================================
gif = Image.open(GIF_PATH)

frames = []

for frame_no in range(gif.n_frames):
    gif.seek(frame_no)

    frame = ImageTk.PhotoImage(gif.copy())
    frames.append(frame)


# ================================================
#   Show GIF
# ================================================
label = tk.Label(root)
label.pack(expand=True)

current_frame = 0


def update_animation():
    global current_frame

    label.configure(image=frames[current_frame])

    current_frame += 1

    if current_frame >= len(frames):
        current_frame = 0

    root.after(50, update_animation)


update_animation()

root.mainloop()