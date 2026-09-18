"""系统托盘封装（依赖 pystray + Pillow，缺失时自动不可用）。"""

import os
import queue
import threading
import tkinter as tk

from .resources import resource_path

try:
    import pystray
except ImportError:
    pystray = None

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = None
    ImageDraw = None


# 与 exe 图标使用同一份资源
ICON_PNG = resource_path("assets", "tomato.png")


def is_available():
    return pystray is not None and Image is not None and ImageDraw is not None


class TrayController:
    """管理托盘图标；菜单动作通过 root.after 回到 Tk 主线程执行。"""

    def __init__(self, app):
        self.app = app
        self.icon = None
        self.available = is_available()
        self._queue = queue.Queue()

    @property
    def running(self):
        return self.icon is not None

    def _image(self):
        """托盘图标：优先加载与 exe 相同的 assets/tomato.png，缺失时运行时绘制。"""
        size = 64
        if Image is not None and os.path.exists(ICON_PNG):
            try:
                return Image.open(ICON_PNG).convert("RGBA").resize((size, size),
                                                                   Image.LANCZOS)
            except Exception:
                pass
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        palette = self.app.palette
        draw.ellipse((6, 12, size - 6, size - 6), fill=palette["work"])
        draw.polygon([(size // 2 - 10, 14), (size // 2, 4), (size // 2 + 10, 14)],
                     fill=palette["break"])
        return img

    def start(self):
        if not self.available or self.icon is not None:
            return
        menu = pystray.Menu(
            pystray.MenuItem("显示主界面",
                             lambda i, it: self._enqueue("show"), default=True),
            pystray.MenuItem("收起为小球",
                             lambda i, it: self._enqueue("ball")),
            pystray.MenuItem("退出",
                             lambda i, it: self._enqueue("quit")),
        )
        self.icon = pystray.Icon("pomodoro", self._image(), "番茄钟", menu)
        threading.Thread(target=self.icon.run, daemon=True).start()
        self._schedule_poll()

    def _enqueue(self, action):
        """从托盘线程投递动作；由主线程轮询执行，避免跨线程操作 Tk。"""
        self._queue.put(action)

    def _schedule_poll(self):
        try:
            self.app.root.after(100, self._poll)
        except tk.TclError:
            pass

    def _poll(self):
        while True:
            try:
                action = self._queue.get_nowait()
            except queue.Empty:
                break
            if action == "show":
                self.app.show_main()
            elif action == "ball":
                self.app.custom_iconify()
            elif action == "quit":
                self.app.quit_app()
                return
        if self.icon is not None:
            self._schedule_poll()

    def stop(self):
        if self.icon is None:
            return
        try:
            self.icon.stop()
        except Exception:
            pass
        self.icon = None
