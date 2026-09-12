"""根据 pomodoro.__version__ 生成 PyInstaller 版本信息文件 version_info.txt。

运行：python tools/make_version_info.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pomodoro import __version__  # noqa: E402

OUT = os.path.join(ROOT, "version_info.txt")

TEMPLATE = """VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({nums}),
    prodvers=({nums}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        '080404b0',
        [StringStruct('FileDescription', 'Tomato Clock'),
        StringStruct('FileVersion', '{ver}'),
        StringStruct('InternalName', 'TomatoClock'),
        StringStruct('OriginalFilename', 'TomatoClock-v{ver}.exe'),
        StringStruct('ProductName', 'Tomato Clock'),
        StringStruct('ProductVersion', '{ver}')])
      ]),
    VarFileInfo([VarStruct('Translation', [2052, 1200])])
  ]
)
"""


def main():
    parts = [int(x) for x in __version__.split(".")]
    parts = (parts + [0, 0, 0, 0])[:4]
    content = TEMPLATE.format(nums=", ".join(str(p) for p in parts), ver=__version__)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(content)
    print("wrote", OUT, "version", __version__)


if __name__ == "__main__":
    main()
