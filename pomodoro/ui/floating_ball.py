"""最小化后的圆形悬浮球。

优先使用 Windows 逐像素 alpha 分层窗口，边缘真正抗锯齿；
不可用时退回色键透明 + Pillow 绘制。
"""

import tkinter as tk

from .. import layered
from ..constants import FONT
from ..theme import sp
from ..widgets import paint_ball, ball_image, _has_pillow


class FloatingBall:
    def __init__(self, app):
        self.app = app
        self.window = None
        self.canvas = None
        self.time_label = None
        self.radius = sp(34)
        self._x_offset = 0
        self._y_offset = 0
        self._accent = None
        self._text = "25:00"
        self._progress = None
        self._current = None
        self._layered = False

    @property
    def visible(self):
        return self.window is not None

    def show(self):
        if self.window is not None:
            return
        app = self.app
        p = app.palette
        d = self.radius * 2
        ball = tk.Toplevel(app.root)
        self.window = ball
        ball.overrideredirect(True)
        ball.wm_attributes("-topmost", 1)
        self._layered = layered.available() and _has_pillow()
        if self._layered:
            ball.configure(bg=p["card"])
        else:
            ball.configure(bg=app.accent)
            self._set_transparent(app.accent)

        x = ball.winfo_screenwidth() - d - sp(10)
        ball.geometry(f"{d}x{d}+{x}+{sp(10)}")

        if self._layered:
            ball.update_idletasks()
        else:
            self.canvas = tk.Canvas(ball, width=d, height=d, bg=app.accent,
                                    highlightthickness=0)
            self.canvas.pack()
            self.time_label = tk.Label(ball, font=(FONT, 11, "bold"),
                                       fg=p["text"], bg=p["card"])
            self.time_label.place(relx=0.5, rely=0.5, anchor="center")
        self._render()

        ball.bind("<Button-1>", self._on_drag_start)
        ball.bind("<B1-Motion>", self._on_drag_motion)
        ball.bind("<Double-Button-1>", lambda e: self.app.restore_from_ball())

    def hide(self):
        if self.window is not None:
            try:
                self.window.destroy()
            except tk.TclError:
                pass
        self.window = None
        self.canvas = None
        self.time_label = None
        self._accent = None

    # ----------------------------- 绘制 -----------------------------
    def _set_transparent(self, color):
        if self.window is None:
            return
        try:
            self.window.wm_attributes("-transparentcolor", color)
        except tk.TclError:
            pass

    def _render(self):
        if self.window is None:
            return
        app = self.app
        p = app.palette
        d = self.radius * 2
        if self._layered:
            current = self._current if self._current is not None else app.core.display_value()
            self._progress = app.core.progress(current)
            img = ball_image(d, p["card"], app.accent, sp(4), self._text,
                             p["text"], int(round(sp(14))),
                             progress=self._progress, track=p["track"])
            layered.set_image(layered._hwnd_of(self.window), img,
                              self.window.winfo_x(), self.window.winfo_y())
        else:
            if self.canvas is None:
                return
            paint_ball(self.canvas, d, p["card"], app.accent, sp(4), app.accent)
            self.canvas.configure(bg=app.accent)
            self.window.configure(bg=app.accent)
            self._set_transparent(app.accent)
            if self.time_label is not None:
                self.time_label.configure(text=self._text)
        self._accent = app.accent

    def update(self, current=None):
        if current is None:
            current = self.app.core.display_value()
        if self.window is None:
            return
        text = f"{int(current // 60):02d}:{int(current % 60):02d}"
        progress = self.app.core.progress(current)
        if (text != self._text or self.app.accent != self._accent
                or self._progress is None or abs(progress - self._progress) > 0.003):
            self._current = current
            self._text = text
            self._render()

    def restyle(self):
        self._render()

    def _on_drag_start(self, event):
        self._x_offset = event.x
        self._y_offset = event.y

    def _on_drag_motion(self, event):
        ball = self.window
        if ball is None:
            return
        x = ball.winfo_x() + event.x - self._x_offset
        y = ball.winfo_y() + event.y - self._y_offset
        ball.geometry(f"+{x}+{y}")
