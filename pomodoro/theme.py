"""主题与 DPI 缩放工具。"""

import os

# 全局缩放系数：真实 DPI / 96，启动时由 set_scale 设定
SCALE = 1.0


def sp(value):
    """把设计像素换算为设备像素。"""
    return int(round(value * SCALE))


def set_scale(dpi):
    """根据屏幕 DPI 设置全局缩放系数。"""
    global SCALE
    SCALE = max(1.0, dpi / 96.0)
    return SCALE


def setup_dpi_awareness():
    """在创建 Tk 窗口前声明 DPI 感知，避免高缩放屏字体发虚。"""
    if os.name != "nt":
        return
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def _hex_to_rgb(color):
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def blend(color, other, t):
    """把 color 向 other 混合 t（0~1），用于生成悬停色。"""
    r1, g1, b1 = _hex_to_rgb(color)
    r2, g2, b2 = _hex_to_rgb(other)
    return "#%02X%02X%02X" % (
        round(r1 + (r2 - r1) * t),
        round(g1 + (g2 - g1) * t),
        round(b1 + (b2 - b1) * t),
    )
