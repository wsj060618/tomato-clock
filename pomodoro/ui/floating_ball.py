"""最小化后的圆形悬浮球。"""

import tkinter as tk

from ..constants import FONT
from ..theme import sp, blend
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
        ball.configure(bg=app.accent)
        self._set_transparent(app.accent)

        x = ball.winfo_screenwidth() - d - sp(10)
        ball.geometry(f"{d}x{d}+{x}+{sp(10)}")

        self.canvas = tk.Canvas(ball, width=d, height=d, bg=app.accent, highlightthickness=0)
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

    def _set_transparent(self, color):
        if self.window is None:
            return
        try:
            self.window.wm_attributes("-transparentcolor", color)
        except tk.TclError:
            pass

    def _paint(self):
        if self.canvas is None:
            return
        app = self.app
        p = app.palette
        # 用当前强调色作为透明键，圆环用几乎同色的近色，
        # 使抗锯齿边缘过渡到自身颜色，避免黑/白毛边与锯齿。
        magic = app.accent
        ring = blend(app.accent, "#FFFFFF", 0.05)
        paint_ball(self.canvas, self.radius * 2, p["card"], ring, sp(4), magic)
        self.canvas.configure(bg=magic)
        if self.window is not None:
            self.window.configure(bg=magic)
        self._set_transparent(magic)
        self._accent = app.accent

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
        self._paint()
        if self.time_label is not None:
            self.time_label.configure(bg=self.app.palette["card"],
                                      fg=self.app.palette["text"])

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
