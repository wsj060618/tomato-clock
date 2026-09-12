"""系统托盘封装（依赖 pystray + Pillow，缺失时自动不可用）。"""

import threading

try:
    import pystray
except ImportError:
    pystray = None

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = None
    ImageDraw = None


def is_available():
    return pystray is not None and Image is not None and ImageDraw is not None


class TrayController:
    """管理托盘图标；菜单动作通过 root.after 回到 Tk 主线程执行。"""

    def __init__(self, app):
        self.app = app
        self.icon = None
        self.available = is_available()

    @property
    def running(self):
        return self.icon is not None

    def _image(self):
        size = 64
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
        root = self.app.root
        menu = pystray.Menu(
            pystray.MenuItem("显示主界面",
                             lambda i, it: root.after(0, self.app.show_main), default=True),
            pystray.MenuItem("收起为小球",
                             lambda i, it: root.after(0, self.app.custom_iconify)),
            pystray.MenuItem("退出",
                             lambda i, it: root.after(0, self.app.quit_app)),
        )
        self.icon = pystray.Icon("pomodoro", self._image(), "番茄钟", menu)
        threading.Thread(target=self.icon.run, daemon=True).start()

    def stop(self):
        if self.icon is None:
            return
        try:
            self.icon.stop()
        except Exception:
            pass
        self.icon = None
