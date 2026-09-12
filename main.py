"""程序入口：声明 DPI 感知后启动番茄钟。"""

import tkinter as tk

from pomodoro.theme import setup_dpi_awareness
from pomodoro.ui.app import PomodoroApp


def main():
    setup_dpi_awareness()
    root = tk.Tk()
    PomodoroApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
