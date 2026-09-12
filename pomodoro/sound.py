"""提示音（Windows 使用 winsound，其它平台静默）。"""

try:
    import winsound
except ImportError:
    winsound = None


def play():
    """播放一声系统提示音，失败时忽略。"""
    if winsound is None:
        return
    try:
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except RuntimeError:
        pass
