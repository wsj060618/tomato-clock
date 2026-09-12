"""历史记录对话框：按天汇总番茄数与专注时长。"""

import tkinter as tk
from datetime import date, datetime

from ..constants import FONT
from ..theme import sp
from ..widgets import create_round_rect, enable_drag


def _format_day(key):
    """把 2026-09-13 格式化为 今天 / 昨天 / 9月13日 周六。"""
    try:
        d = datetime.strptime(key, "%Y-%m-%d").date()
    except ValueError:
        return key
    delta = (date.today() - d).days
    if delta == 0:
        return "今天"
    if delta == 1:
        return "昨天"
    weekday = "一二三四五六日"[d.weekday()]
    return f"{d.month}月{d.day}日 周{weekday}"


class HistoryDialog:
    def __init__(self, app):
        self.app = app

    def show(self):
        app = self.app
        p = app.palette
        stats = app.stats
        daily = stats.get("daily", {})

        win = tk.Toplevel(app.root)
        win.overrideredirect(True)
        win.wm_attributes("-topmost", 1)
        win.configure(bg=p["magic"])
        try:
            win.wm_attributes("-transparentcolor", p["magic"])
        except tk.TclError:
            pass

        W, H = sp(360), sp(470)
        x = app.root.winfo_x() + (app.W - W) // 2
        y = app.root.winfo_y() + sp(30)
        win.geometry(f"{W}x{H}+{max(0, x)}+{max(0, y)}")

        canvas = tk.Canvas(win, width=W, height=H, bg=p["magic"], highlightthickness=0)
        canvas.place(x=0, y=0)
        create_round_rect(canvas, 0, 0, W, H, sp(20), fill=p["card"], outline=p["card"])

        tk.Label(win, text="历史记录", font=(FONT, 13, "bold"), fg=p["text"],
                 bg=p["card"]).place(x=sp(24), y=sp(16))

        close_btn = tk.Label(win, text="✕", font=(FONT, 12), fg=p["muted"], bg=p["card"],
                             cursor="hand2")
        close_btn.place(relx=1.0, x=sp(-20), y=sp(16), anchor="ne")
        close_btn.bind("<Button-1>", lambda e: win.destroy())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=p["work"]))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=p["muted"]))

        # 汇总
        days = len(daily)
        total = sum(d.get("count", 0) for d in daily.values())
        seconds = sum(d.get("focus_seconds", 0) for d in daily.values())
        hours, minutes = seconds // 3600, (seconds % 3600) // 60
        if hours:
            summary = f"累计 {total} 个 · 专注 {hours} 小时 {minutes} 分钟 · {days} 天"
        else:
            summary = f"累计 {total} 个 · 专注 {minutes} 分钟 · {days} 天"
        tk.Label(win, text=summary, font=(FONT, 9), fg=p["muted"],
                 bg=p["card"]).place(x=sp(24), y=sp(50))

        # 滚动区域
        top = sp(80)
        bottom = sp(20)
        container = tk.Canvas(win, bg=p["card"], highlightthickness=0)
        container.place(x=sp(16), y=top, width=W - sp(32), height=H - top - bottom)
        inner = tk.Frame(container, bg=p["card"])
        window_id = container.create_window((0, 0), window=inner, anchor="nw")

        inner.bind("<Configure>",
                   lambda e: container.configure(scrollregion=container.bbox("all")))
        container.bind("<Configure>",
                       lambda e: container.itemconfig(window_id, width=e.width))

        def on_wheel(event):
            container.yview_scroll(int(-event.delta / 120), "units")

        win.bind("<MouseWheel>", on_wheel)
        enable_drag(win, canvas, win)

        if not daily:
            tk.Label(inner, text="还没有完成记录\n完成一个番茄后就会出现在这里",
                     font=(FONT, 10), fg=p["muted"], bg=p["card"], justify="center").pack(
                pady=sp(40))
        else:
            for key in sorted(daily.keys(), reverse=True):
                self._build_row(inner, key, daily[key])

    def _build_row(self, parent, key, data):
        p = self.app.palette
        count = data.get("count", 0)
        minutes = data.get("focus_seconds", 0) // 60
        tasks = data.get("tasks", {})

        row = tk.Frame(parent, bg=p["card2"])
        row.pack(fill="x", pady=sp(4))
        tk.Frame(row, bg=self.app.palette["work"], width=sp(4)).pack(side="left", fill="y")

        body = tk.Frame(row, bg=p["card2"])
        body.pack(side="left", fill="both", expand=True, padx=sp(12), pady=sp(8))

        line = tk.Frame(body, bg=p["card2"])
        line.pack(fill="x")
        tk.Label(line, text=_format_day(key), font=(FONT, 10, "bold"), fg=p["text"],
                 bg=p["card2"]).pack(side="left")
        tk.Label(line, text=f"{count} 个 · {minutes} 分钟", font=(FONT, 9), fg=p["muted"],
                 bg=p["card2"]).pack(side="right")

        if tasks:
            detail = "、".join(f"{name} ×{n}" for name, n in
                             sorted(tasks.items(), key=lambda kv: -kv[1]))
            tk.Label(body, text=detail, font=(FONT, 8), fg=p["muted"], bg=p["card2"],
                     anchor="w", justify="left").pack(fill="x", pady=(sp(4), 0))
