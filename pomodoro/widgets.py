"""自绘控件：圆角矩形、圆角按钮、分段控件、开关。

优先用 Pillow 超采样渲染，得到抗锯齿的圆角；Pillow 不可用时退回 Tk 多边形。
"""

import tkinter as tk

from .constants import FONT
from .theme import sp

try:
    from PIL import Image, ImageDraw, ImageTk, ImageFont
except ImportError:
    Image = ImageDraw = ImageTk = None
    ImageFont = None

_FONT_CANDIDATES = (
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
)


def _load_font(size):
    if ImageFont is None:
        return None
    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def ball_image(diameter, fill, outline, ring, text, text_color, font_size):
    """生成带真实 alpha 的悬浮球 RGBA 图片（供逐像素透明贴图）。"""
    s = 4
    size = diameter * s
    rw = max(1, int(ring * s))
    inset = rw // 2
    shape = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(shape).ellipse([inset, inset, size - 1 - inset, size - 1 - inset],
                                  fill=fill, outline=outline, width=rw)
    shape = shape.resize((diameter, diameter), Image.LANCZOS)
    draw = ImageDraw.Draw(shape)
    font = _load_font(font_size)
    if font is not None:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((diameter - tw) / 2 - bbox[0], (diameter - th) / 2 - bbox[1]),
                  text, font=font, fill=text_color)
    return shape


def _has_pillow():
    return Image is not None and ImageTk is not None


def create_round_rect(canvas, x1, y1, x2, y2, r, **kwargs):
    """在 canvas 上画一个圆角矩形（无抗锯齿，作回退用）。"""
    points = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


def _aa_rounded_rect(width, height, radius, fill, background, supersample=4):
    """抗锯齿圆角矩形，混合到 background 上。"""
    s = supersample
    shape = Image.new("RGBA", (width * s, height * s), (0, 0, 0, 0))
    ImageDraw.Draw(shape).rounded_rectangle(
        [0, 0, width * s - 1, height * s - 1], radius=max(0, radius * s), fill=fill)
    shape = shape.resize((width, height), Image.LANCZOS)
    base = Image.new("RGBA", (width, height), background)
    base.alpha_composite(shape)
    return base.convert("RGB")


def _aa_rounded_rect_on_magic(width, height, radius, fill, magic, supersample=4):
    """抗锯齿圆角矩形，混合到透明色（magic）上，供窗口抠除四角。"""
    return _aa_rounded_rect(width, height, radius, fill, magic, supersample)


def paint_card(canvas, width, height, radius, fill, magic):
    """在 canvas 上画抗锯齿圆角卡片窗口背景。"""
    if _has_pillow():
        try:
            photo = ImageTk.PhotoImage(_aa_rounded_rect_on_magic(width, height, radius,
                                                                 fill, magic))
            canvas.create_image(0, 0, anchor="nw", image=photo)
            canvas.image = photo
            return
        except Exception:
            pass
    create_round_rect(canvas, 0, 0, width, height, radius, fill=fill, outline=fill)


def _circle_image(diameter, fill, outline, ring, magic, supersample=4):
    s = supersample
    size = diameter * s
    rw = max(1, int(ring * s))
    inset = rw // 2
    shape = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(shape).ellipse([inset, inset, size - 1 - inset, size - 1 - inset],
                                  fill=fill, outline=outline, width=rw)
    shape = shape.resize((diameter, diameter), Image.LANCZOS)
    base = Image.new("RGBA", (diameter, diameter), magic)
    base.alpha_composite(shape)
    return base.convert("RGB")


def paint_ball(canvas, diameter, fill, outline, ring, magic):
    """在 canvas 上画抗锯齿圆形悬浮球。"""
    canvas.delete("all")
    if _has_pillow():
        try:
            photo = ImageTk.PhotoImage(_circle_image(diameter, fill, outline, ring, magic))
            canvas.create_image(0, 0, anchor="nw", image=photo)
            canvas.image = photo
            return
        except Exception:
            pass
    pad = sp(4)
    canvas.create_oval(pad, pad, diameter - pad, diameter - pad,
                       outline=outline, width=sp(4), fill=fill)


def enable_drag(window, *widgets):
    """让无边框 window 可以通过拖动指定控件来移动。"""
    state = {"x": 0, "y": 0}

    def on_start(event):
        state["x"] = event.x_root - window.winfo_x()
        state["y"] = event.y_root - window.winfo_y()

    def on_move(event):
        window.geometry(f"+{event.x_root - state['x']}+{event.y_root - state['y']}")

    for widget in widgets:
        widget.bind("<Button-1>", on_start, add="+")
        widget.bind("<B1-Motion>", on_move, add="+")


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
        self._bg = bg
        self._bw, self._bh, self._br = width, height, radius
        self._img_item = None
        self._image = None
        self._draw(fill)
        self._text = self.create_text(width / 2, height / 2, text=text, fill=fg, font=font)
        self.bind("<Enter>", lambda e: self._draw(self._fill_hover))
        self.bind("<Leave>", lambda e: self._draw(self._fill))
        self.bind("<Button-1>", lambda e: self.command() if self.command else None)

    def _draw(self, color):
        if _has_pillow():
            try:
                photo = ImageTk.PhotoImage(
                    _aa_rounded_rect(self._bw, self._bh, self._br, color, self._bg))
                if self._img_item is None:
                    self._img_item = self.create_image(0, 0, anchor="nw", image=photo)
                else:
                    self.itemconfig(self._img_item, image=photo)
                self._image = photo
                return
            except Exception:
                pass
        if self._img_item is None:
            self._img_item = create_round_rect(self, 1, 1, self._bw - 1, self._bh - 1,
                                               self._br, fill=color, outline=color)
        else:
            self.itemconfig(self._img_item, fill=color, outline=color)

    def set_text(self, text):
        self.itemconfig(self._text, text=text)

    def set_colors(self, fill, fill_hover=None):
        self._fill = fill
        self._fill_hover = fill_hover or fill
        self._draw(fill)


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
        self._bg = bg
        self._image = None
        self._draw()
        self.bind("<Button-1>", self._on_click)

    def _image_data(self):
        s = 4
        shape = Image.new("RGBA", (self.width * s, self.height * s), (0, 0, 0, 0))
        draw = ImageDraw.Draw(shape)
        draw.rounded_rectangle([0, 0, self.width * s - 1, self.height * s - 1],
                               radius=int(self.radius * s), fill=self.track_color)
        seg_w = (self.width - 2 * self.pad) / len(self.options)
        x0 = self.pad + self.current * seg_w
        draw.rounded_rectangle([x0 * s, self.pad * s, (x0 + seg_w) * s,
                                (self.height - self.pad) * s],
                               radius=int((self.radius - self.pad) * s), fill=self.accent)
        shape = shape.resize((self.width, self.height), Image.LANCZOS)
        base = Image.new("RGBA", (self.width, self.height), self._bg)
        base.alpha_composite(shape)
        return base.convert("RGB")

    def _draw(self):
        self.delete("all")
        self._img_item = None
        drawn = False
        if _has_pillow():
            try:
                self._image = ImageTk.PhotoImage(self._image_data())
                self.create_image(0, 0, anchor="nw", image=self._image)
                drawn = True
            except Exception:
                drawn = False
        if not drawn:
            create_round_rect(self, 1, 1, self.width - 1, self.height - 1,
                              self.radius, fill=self.track_color, outline=self.track_color)
            seg_w = (self.width - 2 * self.pad) / len(self.options)
            x0 = self.pad + self.current * seg_w
            create_round_rect(self, x0, self.pad, x0 + seg_w, self.height - self.pad,
                              self.radius - self.pad, fill=self.accent, outline=self.accent)
        seg_w = (self.width - 2 * self.pad) / len(self.options)
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
        self._bg = bg
        self._image = None
        self._draw()
        self.bind("<Button-1>", self._click)

    def _image_data(self):
        s = 4
        color = self.on_color if self.value else self.off_color
        shape = Image.new("RGBA", (self.w * s, self.h * s), (0, 0, 0, 0))
        draw = ImageDraw.Draw(shape)
        draw.rounded_rectangle([0, 0, self.w * s - 1, self.h * s - 1],
                               radius=int((self.h - 2) * s / 2), fill=color)
        r = self.h - 6
        x = self.w - 3 - r if self.value else 3
        draw.ellipse([x * s, 3 * s, (x + r) * s, (3 + r) * s], fill=self.knob_color)
        shape = shape.resize((self.w, self.h), Image.LANCZOS)
        base = Image.new("RGBA", (self.w, self.h), self._bg)
        base.alpha_composite(shape)
        return base.convert("RGB")

    def _draw(self):
        self.delete("all")
        drawn = False
        if _has_pillow():
            try:
                self._image = ImageTk.PhotoImage(self._image_data())
                self.create_image(0, 0, anchor="nw", image=self._image)
                drawn = True
            except Exception:
                drawn = False
        if not drawn:
            color = self.on_color if self.value else self.off_color
            create_round_rect(self, 1, 1, self.w - 1, self.h - 1, (self.h - 2) / 2,
                              fill=color, outline=color)
            r = self.h - 6
            x = self.w - 3 - r if self.value else 3
            self.create_oval(x, 3, x + r, 3 + r, fill=self.knob_color,
                             outline=self.knob_color)

    def set_value(self, value):
        self.value = bool(value)
        self._draw()

    def _click(self, _):
        self.value = not self.value
        self._draw()
        if self.command:
            self.command(self.value)
