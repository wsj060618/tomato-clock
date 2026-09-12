"""Windows 逐像素 alpha 分层窗口（让无边框窗口边缘真正抗锯齿）。

仅依赖标准库 ctypes + Pillow；非 Windows 或失败时返回 False，调用方退回色键方案。
"""

import ctypes
import os
import sys

WS_EX_LAYERED = 0x00080000
GWL_EXSTYLE = -20
ULW_ALPHA = 0x00000002
AC_SRC_OVER = 0x00
AC_SRC_ALPHA = 0x01


class _BLENDFUNCTION(ctypes.Structure):
    _fields_ = [("BlendOp", ctypes.c_byte),
                ("BlendFlags", ctypes.c_byte),
                ("SourceConstantAlpha", ctypes.c_byte),
                ("AlphaFormat", ctypes.c_byte)]


class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class _SIZE(ctypes.Structure):
    _fields_ = [("cx", ctypes.c_long), ("cy", ctypes.c_long)]


class _BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", ctypes.c_uint32), ("biWidth", ctypes.c_int32),
                ("biHeight", ctypes.c_int32), ("biPlanes", ctypes.c_uint16),
                ("biBitCount", ctypes.c_uint16), ("biCompression", ctypes.c_uint32),
                ("biSizeImage", ctypes.c_uint32), ("biXPelsPerMeter", ctypes.c_int32),
                ("biYPelsPerMeter", ctypes.c_int32), ("biClrUsed", ctypes.c_uint32),
                ("biClrImportant", ctypes.c_uint32)]


class _BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", _BITMAPINFOHEADER), ("bmiColors", ctypes.c_uint32 * 3)]


def available():
    return os.name == "nt"


def _hwnd_of(widget):
    """取 Tk 顶层窗口真正的 HWND。"""
    user32 = ctypes.windll.user32
    user32.GetParent.restype = ctypes.c_void_p
    user32.GetParent.argtypes = [ctypes.c_void_p]
    return user32.GetParent(ctypes.c_void_p(widget.winfo_id()))


def _premultiplied_bgra(image):
    """RGBA -> 预乘 BGRA 字节。"""
    img = image.convert("RGBA")
    data = bytearray(img.tobytes("raw", "RGBA"))
    for i in range(0, len(data), 4):
        alpha = data[i + 3]
        if alpha != 255:
            data[i] = (data[i] * alpha + 127) // 255
            data[i + 1] = (data[i + 1] * alpha + 127) // 255
            data[i + 2] = (data[i + 2] * alpha + 127) // 255
    # RGBA -> BGRA
    out = bytearray(len(data))
    for i in range(0, len(data), 4):
        out[i] = data[i + 2]
        out[i + 1] = data[i + 1]
        out[i + 2] = data[i]
        out[i + 3] = data[i + 3]
    return bytes(out)


def set_image(hwnd, image, x=0, y=0):
    """把 PIL RGBA 图片以逐像素 alpha 贴到分层窗口 (x, y) 位置。成功返回 True。"""
    if not available():
        return False
    try:
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32

        user32.GetWindowLongW.restype = ctypes.c_long
        user32.GetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int]
        user32.SetWindowLongW.restype = ctypes.c_long
        user32.SetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_long]
        user32.UpdateLayeredWindow.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(_POINT),
            ctypes.POINTER(_SIZE), ctypes.c_void_p, ctypes.POINTER(_POINT),
            ctypes.c_uint32, ctypes.POINTER(_BLENDFUNCTION), ctypes.c_uint32]
        gdi32.CreateCompatibleDC.restype = ctypes.c_void_p
        gdi32.CreateCompatibleDC.argtypes = [ctypes.c_void_p]
        gdi32.CreateDIBSection.restype = ctypes.c_void_p
        gdi32.CreateDIBSection.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(_BITMAPINFO), ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p, ctypes.c_uint32]
        gdi32.SelectObject.restype = ctypes.c_void_p
        gdi32.SelectObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

        user32.GetDC.restype = ctypes.c_void_p
        user32.GetDC.argtypes = [ctypes.c_void_p]
        user32.ReleaseDC.restype = ctypes.c_int
        user32.ReleaseDC.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        gdi32.DeleteObject.argtypes = [ctypes.c_void_p]
        gdi32.DeleteDC.argtypes = [ctypes.c_void_p]

        hwnd = ctypes.c_void_p(hwnd)
        ex = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex | WS_EX_LAYERED)

        img = image.convert("RGBA")
        w, h = img.size
        buf = _premultiplied_bgra(img)

        hdc_screen = user32.GetDC(None)
        hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
        bmi = _BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(_BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = w
        bmi.bmiHeader.biHeight = -h
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = 0
        ppv = ctypes.c_void_p()
        hbmp = gdi32.CreateDIBSection(hdc_mem, ctypes.byref(bmi), 0,
                                      ctypes.byref(ppv), None, 0)
        ctypes.memmove(ppv, buf, len(buf))
        old = gdi32.SelectObject(hdc_mem, hbmp)

        blend = _BLENDFUNCTION(AC_SRC_OVER, 0, 255, AC_SRC_ALPHA)
        size = _SIZE(w, h)
        src = _POINT(0, 0)
        dst = _POINT(int(x), int(y))
        user32.UpdateLayeredWindow(hwnd, hdc_screen,
                                   ctypes.byref(dst), ctypes.byref(size),
                                   hdc_mem, ctypes.byref(src),
                                   0, ctypes.byref(blend), ULW_ALPHA)

        gdi32.SelectObject(hdc_mem, old)
        gdi32.DeleteObject(ctypes.c_void_p(hbmp))
        gdi32.DeleteDC(ctypes.c_void_p(hdc_mem))
        user32.ReleaseDC(None, hdc_screen)
        return True
    except Exception:
        return False
