"""右下角轻量浮层通知。"""

import tkinter as tk

from ..constants import FONT
from ..theme import sp
from ..widgets import paint_card


class ToastManager:
    def __init__(self, app):
        self.app = app
        self.window = None

    def show(self, title, message):
        app = self.app
        p = app.palette
        accent = app.accent
        self._dismiss()

        t = tk.Toplevel(app.root)
        self.window = t
        t.overrideredirect(True)
        t.wm_attributes("-topmost", 1)
        t.configure(bg=p["magic"])
        try:
            t.wm_attributes("-transparentcolor", p["magic"])
        except tk.TclError:
            pass

        W, H = sp(260), sp(84)
        x = t.winfo_screenwidth() - W - sp(20)
        y = t.winfo_screenheight() - H - sp(60)
        t.geometry(f"{W}x{H}+{x}+{y}")

        canvas = tk.Canvas(t, width=W, height=H, bg=p["magic"], highlightthickness=0)
        canvas.pack()
        paint_card(canvas, W, H, sp(16), p["card"], p["magic"])
        canvas.create_rectangle(0, 0, sp(5), H, fill=accent, outline=accent)
        canvas.create_text(sp(20), sp(26), text=title, anchor="w", fill=accent,
                           font=(FONT, 11, "bold"))
        canvas.create_text(sp(20), sp(52), text=message, anchor="w", fill=p["text"],
                           font=(FONT, 9))

        t.bind("<Button-1>", lambda e: self._dismiss())
        t.after(4000, self._dismiss)

    def _dismiss(self):
        if self.window is not None:
            try:
                self.window.destroy()
            except tk.TclError:
                pass
            self.window = None
