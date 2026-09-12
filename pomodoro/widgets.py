"""自绘控件：圆角矩形、圆角按钮、分段控件、开关。"""

import tkinter as tk

from .constants import FONT
from .theme import sp


def create_round_rect(canvas, x1, y1, x2, y2, r, **kwargs):
    """在 canvas 上画一个圆角矩形，返回图元 id。"""
    points = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class RoundedButton(tk.Canvas):
    """圆角按钮，带悬停变色。"""

    def __init__(self, parent, text, command=None, width=110, height=44, radius=22,
                 fill="#2A2740", fill_hover="#37314F", fg="#F5F3FF",
                 font=(FONT, 11, "bold"), bg="#1E1B2E"):
        width, height, radius = sp(width), sp(height), sp(radius)
        super().__init__(parent, width=width, height=height, bg=bg,
                         highlightthickness=0, bd=0, cursor="hand2")
        self.command = command
        self._fill = fill
        self._fill_hover = fill_hover
        self._shape = create_round_rect(self, 1, 1, width - 1, height - 1, radius,
                                        fill=fill, outline=fill)
        self._text = self.create_text(width / 2, height / 2, text=text, fill=fg, font=font)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", lambda e: self.command() if self.command else None)

    def _on_enter(self, _):
        self.itemconfig(self._shape, fill=self._fill_hover, outline=self._fill_hover)

    def _on_leave(self, _):
        self.itemconfig(self._shape, fill=self._fill, outline=self._fill)

    def set_text(self, text):
        self.itemconfig(self._text, text=text)

    def set_colors(self, fill, fill_hover=None):
        self._fill = fill
        self._fill_hover = fill_hover or fill
        self.itemconfig(self._shape, fill=self._fill, outline=self._fill)


class SegmentedControl(tk.Canvas):
    """分段选择控件（如 倒计时 / 正计时）。"""

    def __init__(self, parent, options, command, width=176, height=36, radius=18,
                 bg="#1E1B2E", accent="#FF6B6B", text_color="#F5F3FF", muted="#8E8AA6",
                 track_color="#2A2740"):
        width, height, radius = sp(width), sp(height), sp(radius)
        super().__init__(parent, width=width, height=height, bg=bg,
                         highlightthickness=0, bd=0, cursor="hand2")
        self.options = options
        self.command = command
        self.current = 0
        self.width = width
        self.height = height
        self.radius = radius
        self.pad = sp(4)
        self.accent = accent
        self.text_color = text_color
        self.muted = muted
        self.track_color = track_color
        self._draw()
        self.bind("<Button-1>", self._on_click)

    def _draw(self):
        self.delete("all")
        create_round_rect(self, 1, 1, self.width - 1, self.height - 1,
                          self.radius, fill=self.track_color, outline=self.track_color)
        seg_w = (self.width - 2 * self.pad) / len(self.options)
        x0 = self.pad + self.current * seg_w
        create_round_rect(self, x0, self.pad, x0 + seg_w, self.height - self.pad,
                          self.radius - self.pad, fill=self.accent, outline=self.accent)
        for i, opt in enumerate(self.options):
            cx = self.pad + (i + 0.5) * seg_w
            color = self.text_color if i == self.current else self.muted
            self.create_text(cx, self.height / 2, text=opt, fill=color,
                             font=(FONT, 10, "bold"))

    def select(self, index):
        self.current = index
        self._draw()

    def _on_click(self, event):
        seg_w = (self.width - 2 * self.pad) / len(self.options)
        idx = int((event.x - self.pad) // seg_w)
        idx = max(0, min(len(self.options) - 1, idx))
        if idx != self.current:
            self.current = idx
            self._draw()
            self.command(idx)


class Toggle(tk.Canvas):
    """滑动开关。"""

    def __init__(self, parent, value, command=None, width=44, height=24,
                 bg="#1E1B2E", on_color="#FF6B6B", off_color="#37314F",
                 knob_color="#FFFFFF"):
        width, height = sp(width), sp(height)
        super().__init__(parent, width=width, height=height, bg=bg,
                         highlightthickness=0, bd=0, cursor="hand2")
        self.value = bool(value)
        self.command = command
        self.w = width
        self.h = height
        self.on_color = on_color
        self.off_color = off_color
        self.knob_color = knob_color
        self._draw()
        self.bind("<Button-1>", self._click)

    def _draw(self):
        self.delete("all")
        color = self.on_color if self.value else self.off_color
        create_round_rect(self, 1, 1, self.w - 1, self.h - 1, (self.h - 2) / 2,
                          fill=color, outline=color)
        r = self.h - 6
        x = self.w - 3 - r if self.value else 3
        self.create_oval(x, 3, x + r, 3 + r, fill=self.knob_color, outline=self.knob_color)

    def set_value(self, value):
        self.value = bool(value)
        self._draw()

    def _click(self, _):
        self.value = not self.value
        self._draw()
        if self.command:
            self.command(self.value)
