"""资源文件定位（兼容 PyInstaller 打包后的临时目录）。"""

import os
import sys


def resource_path(*parts):
    """返回资源文件的绝对路径。

    - 源码运行：项目根目录下的相对路径
    - PyInstaller 打包后：解压目录（sys._MEIPASS）下的相对路径
    """
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)
