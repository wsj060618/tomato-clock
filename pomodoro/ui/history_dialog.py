"""历史记录对话框：按天汇总番茄数与专注时长，支持删除。"""

import tkinter as tk
from datetime import date, datetime

from ..constants import FONT
from ..theme import sp
from ..widgets import RoundedButton, paint_card, enable_drag
from .prompt import ConfirmDialog


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
        self.win = None
        self.inner = None
        self.container = None
        self.summary_label = None
        self.empty_label = None

    def show(self):
        app = self.app
        p = app.palette
        W, H = sp(360), sp(470)
        win = tk.Toplevel(app.root)
        self.win = win
        win.overrideredirect(True)
        win.wm_attributes("-topmost", 1)
        win.configure(bg=p["magic"])
        try:
            win.wm_attributes("-transparentcolor", p["magic"])
        except tk.TclError:
            pass
        x = app.root.winfo_x() + (app.W - W) // 2
        y = app.root.winfo_y() + sp(30)
        win.geometry(f"{W}x{H}+{max(0, x)}+{max(0, y)}")

        canvas = tk.Canvas(win, width=W, height=H, bg=p["magic"], highlightthickness=0)
        canvas.place(x=0, y=0)
        paint_card(canvas, W, H, sp(20), p["card"], p["magic"])

        tk.Label(win, text="历史记录", font=(FONT, 13, "bold"), fg=p["text"],
                 bg=p["card"]).place(x=sp(24), y=sp(16))

        RoundedButton(win, "清空", self._clear_all, width=52, height=26, radius=13,
                      fill=p["card2"], fill_hover=p["card3"], fg=p["muted"],
                      font=(FONT, 9), bg=p["card"]).place(
            relx=1.0, x=sp(-50), y=sp(13), anchor="ne")

        close_btn = tk.Label(win, text="✕", font=(FONT, 12), fg=p["muted"], bg=p["card"],
                             cursor="hand2")
        close_btn.place(relx=1.0, x=sp(-20), y=sp(16), anchor="ne")
        close_btn.bind("<Button-1>", lambda e: win.destroy())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=p["work"]))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=p["muted"]))

        self.summary_label = tk.Label(win, text="", font=(FONT, 9), fg=p["muted"],
                                      bg=p["card"])
        self.summary_label.place(x=sp(24), y=sp(50))

        top = sp(80)
        bottom = sp(20)
        self.container = tk.Canvas(win, bg=p["card"], highlightthickness=0)
        self.container.place(x=sp(16), y=top, width=W - sp(32), height=H - top - bottom)
        self.inner = tk.Frame(self.container, bg=p["card"])
        window_id = self.container.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>",
                        lambda e: self.container.configure(scrollregion=self.container.bbox("all")))
        self.container.bind("<Configure>",
                            lambda e: self.container.itemconfig(window_id, width=e.width))
        win.bind("<MouseWheel>",
                 lambda e: self.container.yview_scroll(int(-e.delta / 120), "units"))
        enable_drag(win, canvas, win)

        self._refresh()

    # ----------------------------- 列表 -----------------------------
    def _refresh(self):
        for child in self.inner.winfo_children():
            child.destroy()
        daily = self.app.stats.get("daily", {})

        days = len(daily)
        total = sum(d.get("count", 0) for d in daily.values())
        seconds = sum(d.get("focus_seconds", 0) for d in daily.values())
        hours, minutes = seconds // 3600, (seconds % 3600) // 60
        if hours:
            summary = f"累计 {total} 个 · 专注 {hours} 小时 {minutes} 分钟 · {days} 天"
        else:
            summary = f"累计 {total} 个 · 专注 {minutes} 分钟 · {days} 天"
        self.summary_label.config(text=summary)

        if not daily:
            tk.Label(self.inner, text="还没有完成记录\n完成一个番茄后就会出现在这里",
                     font=(FONT, 10), fg=self.app.palette["muted"], bg=self.app.palette["card"],
                     justify="center").pack(pady=sp(40))
        else:
            for key in sorted(daily.keys(), reverse=True):
                self._build_row(key, daily[key])
        self.inner.update_idletasks()
        self.container.configure(scrollregion=self.container.bbox("all"))

    def _build_row(self, key, data):
        p = self.app.palette
        count = data.get("count", 0)
        minutes = data.get("focus_seconds", 0) // 60
        tasks = data.get("tasks", {})

        row = tk.Frame(self.inner, bg=p["card2"])
        row.pack(fill="x", pady=sp(4))
        tk.Frame(row, bg=p["work"], width=sp(4)).pack(side="left", fill="y")

        body = tk.Frame(row, bg=p["card2"])
        body.pack(side="left", fill="both", expand=True, padx=sp(12), pady=sp(8))

        line = tk.Frame(body, bg=p["card2"])
        line.pack(fill="x")

        delete_btn = tk.Label(line, text="✕", font=(FONT, 9), fg=p["muted"], bg=p["card2"],
                              cursor="hand2")
        delete_btn.pack(side="right", padx=(sp(8), 0))
        delete_btn.bind("<Button-1>", lambda e, k=key: self._delete_day(k))
        delete_btn.bind("<Enter>", lambda e: delete_btn.config(fg=p["work"]))
        delete_btn.bind("<Leave>", lambda e: delete_btn.config(fg=p["muted"]))

        tk.Label(line, text=f"{count} 个 · {minutes} 分钟", font=(FONT, 9), fg=p["muted"],
                 bg=p["card2"]).pack(side="right")
        tk.Label(line, text=_format_day(key), font=(FONT, 10, "bold"), fg=p["text"],
                 bg=p["card2"]).pack(side="left")

        if tasks:
            detail = "、".join(f"{name} ×{n}" for name, n in
                             sorted(tasks.items(), key=lambda kv: -kv[1]))
            tk.Label(body, text=detail, font=(FONT, 8), fg=p["muted"], bg=p["card2"],
                     anchor="w", justify="left").pack(fill="x", pady=(sp(4), 0))

    # ----------------------------- 删除 -----------------------------
    def _delete_day(self, key):
        ok = ConfirmDialog(self.app, "删除记录",
                           f"确定删除「{_format_day(key)}」的记录吗？",
                           confirm_text="删除", parent=self.win).show()
        if not ok:
            return
        self.app.stats.get("daily", {}).pop(key, None)
        self.app.save_stats()
        self.app.update_stats_label()
        self._refresh()

    def _clear_all(self):
        daily = self.app.stats.get("daily", {})
        if not daily:
            return
        ok = ConfirmDialog(self.app, "清空历史",
                           "确定清空全部历史记录吗？此操作不可恢复。",
                           confirm_text="清空", parent=self.win).show()
        if not ok:
            return
        self.app.stats["daily"] = {}
        self.app.save_stats()
        self.app.update_stats_label()
        self._refresh()
