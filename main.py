"""程序入口：单实例保护，声明 DPI 感知后启动番茄钟。"""

import ctypes
import os
import tkinter as tk

from pomodoro.theme import setup_dpi_awareness
from pomodoro.ui.app import PomodoroApp

# 单实例互斥体名称（Local\ 作用域 = 当前登录会话）
_MUTEX_NAME = "Local\\TomatoClock_SingleInstance"
_ERROR_ALREADY_EXISTS = 183
_mutex_handle = None


def _acquire_single_instance():
    """Windows 下用命名互斥体保证单实例；返回是否已有实例在运行。"""
    if os.name != "nt":
        return False
    global _mutex_handle
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
    # 句柄保存在模块级变量，进程存活期间不释放
    _mutex_handle = kernel32.CreateMutexW(None, False, _MUTEX_NAME)
    return ctypes.get_last_error() == _ERROR_ALREADY_EXISTS


def _activate_existing():
    """尽力把已运行实例的主窗口提到前台；找不到就忽略。"""
    if os.name != "nt":
        return
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.FindWindowW.restype = ctypes.c_void_p
    user32.FindWindowW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
    hwnd = user32.FindWindowW(None, "番茄钟")
    if hwnd:
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetForegroundWindow(hwnd)


def main():
    if _acquire_single_instance():
        _activate_existing()
        return
    setup_dpi_awareness()
    root = tk.Tk()
    PomodoroApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
