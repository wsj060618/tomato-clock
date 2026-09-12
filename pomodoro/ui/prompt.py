"""主题化的确认框与提示框（替代系统原生 messagebox）。"""

import tkinter as tk

from ..constants import FONT
from ..theme import sp, blend
from ..widgets import RoundedButton, paint_card, enable_drag


class _BaseDialog:
    def __init__(self, app, title, message, parent=None):
        self.app = app
        self.result = False
        self.win = None
        self._parent = parent
        self._title = title
        self._message = message

    def _create(self, width=300, height=176):
        app = self.app
        p = app.palette
        W, H = sp(width), sp(height)
        ref = self._parent if self._parent is not None else app.root
        try:
            px, py = ref.winfo_x(), ref.winfo_y()
            pw, ph = ref.winfo_width(), ref.winfo_height()
        except tk.TclError:
            px = py = 0
            pw = ph = 0
        x = px + (pw - W) // 2
        y = py + (ph - H) // 2

        win = tk.Toplevel(app.root)
        self.win = win
        win.overrideredirect(True)
        win.wm_attributes("-topmost", 1)
        win.configure(bg=p["magic"])
        try:
            win.wm_attributes("-transparentcolor", p["magic"])
        except tk.TclError:
            pass
        win.geometry(f"{W}x{H}+{max(0, x)}+{max(0, y)}")

        canvas = tk.Canvas(win, width=W, height=H, bg=p["magic"], highlightthickness=0)
        canvas.place(x=0, y=0)
        paint_card(canvas, W, H, sp(18), p["card"], p["magic"])
        enable_drag(win, canvas, win)

        tk.Label(win, text=self._title, font=(FONT, 12, "bold"), fg=p["text"],
                 bg=p["card"]).place(x=sp(24), y=sp(18))
        tk.Label(win, text=self._message, font=(FONT, 10), fg=p["muted"], bg=p["card"],
                 wraplength=W - sp(48), justify="left").place(x=sp(24), y=sp(50))
        return win, W, H

    def _finish(self):
        self.win.update_idletasks()
        try:
            self.win.grab_set()
        except tk.TclError:
            pass
        self.app.root.wait_window(self.win)
        return self.result


class ConfirmDialog(_BaseDialog):
    def __init__(self, app, title, message, confirm_text="确定", cancel_text="取消",
                 danger=True, parent=None):
        super().__init__(app, title, message, parent)
        self._confirm_text = confirm_text
        self._cancel_text = cancel_text
        self._danger = danger

    def show(self):
        p = self.app.palette
        win, W, H = self._create()

        def confirm(_=None):
            self.result = True
            win.destroy()

        def cancel(_=None):
            self.result = False
            win.destroy()

        accent = p["work"] if self._danger else self.app.accent
        RoundedButton(win, self._cancel_text, cancel, width=110, height=40, radius=20,
                      fill=p["card2"], fill_hover=p["card3"], fg=p["text"],
                      font=(FONT, 10, "bold"), bg=p["card"]).place(
            x=sp(24), y=H - sp(56))
        RoundedButton(win, self._confirm_text, confirm, width=110, height=40, radius=20,
                      fill=accent, fill_hover=blend(accent, "#FFFFFF", 0.25),
                      fg="#FFFFFF", font=(FONT, 10, "bold"), bg=p["card"]).place(
            relx=1.0, x=sp(-24), y=H - sp(56), anchor="ne")
        win.bind("<Escape>", cancel)
        return self._finish()


class MessageDialog(_BaseDialog):
    def __init__(self, app, title, message, button_text="知道了", parent=None):
        super().__init__(app, title, message, parent)
        self._button_text = button_text

    def show(self):
        p = self.app.palette
        win, W, H = self._create()

        def close(_=None):
            win.destroy()

        RoundedButton(win, self._button_text, close, width=120, height=40, radius=20,
                      fill=self.app.accent, fill_hover=blend(self.app.accent, "#FFFFFF", 0.25),
                      fg="#FFFFFF", font=(FONT, 10, "bold"), bg=p["card"]).place(
            relx=0.5, y=H - sp(56), anchor="n")
        win.bind("<Escape>", close)
        return self._finish()
