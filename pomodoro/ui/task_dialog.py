"""当前任务编辑对话框。"""

import tkinter as tk

from ..constants import FONT
from ..theme import sp, blend
from ..widgets import RoundedButton, paint_card, enable_drag


class TaskDialog:
    def __init__(self, app):
        self.app = app

    def show(self):
        app = self.app
        p = app.palette
        dlg = tk.Toplevel(app.root)
        dlg.overrideredirect(True)
        dlg.wm_attributes("-topmost", 1)
        dlg.configure(bg=p["magic"])
        try:
            dlg.wm_attributes("-transparentcolor", p["magic"])
        except tk.TclError:
            pass

        W, H = sp(280), sp(156)
        x = app.root.winfo_x() + (app.W - W) // 2
        y = app.root.winfo_y() + sp(90)
        dlg.geometry(f"{W}x{H}+{max(0, x)}+{max(0, y)}")

        canvas = tk.Canvas(dlg, width=W, height=H, bg=p["magic"], highlightthickness=0)
        canvas.place(x=0, y=0)
        paint_card(canvas, W, H, sp(20), p["card"], p["magic"])
        tk.Label(dlg, text="当前任务", font=(FONT, 12, "bold"), fg=p["text"],
                 bg=p["card"]).place(x=sp(24), y=sp(18))

        entry = tk.Entry(dlg, font=(FONT, 11), bg=p["card2"], fg=p["text"], relief="flat",
                         insertbackground=p["text"], highlightthickness=1,
                         highlightbackground=p["card3"], highlightcolor=app.accent)
        entry.insert(0, app.core.task_name)
        entry.place(x=sp(24), y=sp(52), width=W - sp(48), height=sp(34))
        entry.focus_set()
        entry.select_range(0, "end")

        def confirm(_=None):
            app.set_task(entry.get())
            dlg.destroy()

        entry.bind("<Return>", confirm)
        dlg.bind("<Escape>", lambda e: dlg.destroy())

        RoundedButton(dlg, "取消", dlg.destroy, width=90, height=36, radius=18,
                      fill=p["card2"], fill_hover=p["card3"], fg=p["text"],
                      font=(FONT, 10, "bold"), bg=p["card"]).place(x=sp(24), y=sp(102))
        RoundedButton(dlg, "确定", confirm, width=90, height=36, radius=18,
                      fill=app.accent, fill_hover=blend(app.accent, "#FFFFFF", 0.25),
                      fg="#FFFFFF", font=(FONT, 10, "bold"), bg=p["card"]).place(
            relx=1.0, x=sp(-24), y=sp(102), anchor="ne")

        enable_drag(dlg, canvas, dlg)
