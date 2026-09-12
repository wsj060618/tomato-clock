"""最小化后的圆形悬浮球。"""

import tkinter as tk

from ..constants import FONT
from ..theme import sp
from ..widgets import paint_ball


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
        ball.configure(bg=p["magic"])
        try:
            ball.wm_attributes("-transparentcolor", p["magic"])
        except tk.TclError:
            pass

        x = ball.winfo_screenwidth() - d - sp(10)
        ball.geometry(f"{d}x{d}+{x}+{sp(10)}")

        self.canvas = tk.Canvas(ball, width=d, height=d, bg=p["magic"], highlightthickness=0)
        self.canvas.pack()
        self.time_label = tk.Label(ball, font=(FONT, 11, "bold"), fg=p["text"], bg=p["card"])
        self.time_label.place(relx=0.5, rely=0.5, anchor="center")
        self._paint()
        self.update()

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

    def _paint(self):
        p = self.app.palette
        paint_ball(self.canvas, self.radius * 2, p["card"], self.app.accent,
                   sp(4), p["magic"])
        self._accent = self.app.accent

    def update(self, current=None):
        if current is None:
            current = self.app.core.display_value()
        minutes = int(current // 60)
        seconds = int(current % 60)
        if self.time_label is not None:
            self.time_label.config(text=f"{minutes:02d}:{seconds:02d}")
        if self.canvas is not None and self.app.accent != self._accent:
            self._paint()

    def restyle(self):
        if self.canvas is None:
            return
        p = self.app.palette
        self.canvas.configure(bg=p["magic"])
        self._paint()
        if self.time_label is not None:
            self.time_label.configure(bg=p["card"], fg=p["text"])

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
