"""设置对话框。"""

import tkinter as tk

from .. import __version__
from ..constants import FONT, THEME_ORDER
from ..theme import sp, blend
from ..widgets import RoundedButton, SegmentedControl, Toggle, paint_card, enable_drag
from .prompt import MessageDialog


class SettingsDialog:
    def __init__(self, app):
        self.app = app

    def show(self):
        app = self.app
        core = app.core
        p = app.palette
        win = tk.Toplevel(app.root)
        win.overrideredirect(True)
        win.wm_attributes("-topmost", 1)
        win.configure(bg=p["magic"])
        try:
            win.wm_attributes("-transparentcolor", p["magic"])
        except tk.TclError:
            pass

        W, H = sp(340), sp(400)
        x = app.root.winfo_x() + (app.W - W) // 2
        y = app.root.winfo_y() + sp(40)
        win.geometry(f"{W}x{H}+{max(0, x)}+{max(0, y)}")

        canvas = tk.Canvas(win, width=W, height=H, bg=p["magic"], highlightthickness=0)
        canvas.place(x=0, y=0)
        paint_card(canvas, W, H, sp(20), p["card"], p["magic"])

        tk.Label(win, text="设置", font=(FONT, 13, "bold"), fg=p["text"],
                 bg=p["card"]).place(x=sp(24), y=sp(18))

        close_btn = tk.Label(win, text="✕", font=(FONT, 12), fg=p["muted"], bg=p["card"],
                             cursor="hand2")
        close_btn.place(relx=1.0, x=sp(-20), y=sp(18), anchor="ne")
        close_btn.bind("<Button-1>", lambda e: win.destroy())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=p["work"]))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=p["muted"]))

        def add_field(label, value, x, y, width=140):
            x, y, width = sp(x), sp(y), sp(width)
            tk.Label(win, text=label, font=(FONT, 9), fg=p["muted"],
                     bg=p["card"]).place(x=x, y=y)
            entry = tk.Entry(win, font=(FONT, 11), bg=p["card2"], fg=p["text"], relief="flat",
                             insertbackground=p["text"], justify="center",
                             highlightthickness=1, highlightbackground=p["card3"],
                             highlightcolor=app.accent)
            entry.insert(0, str(value))
            entry.place(x=x, y=y + sp(20), width=width, height=sp(32))
            return entry

        work_entry = add_field("工作时长（分钟）", core.work_duration // 60, 24, 56)
        break_entry = add_field("休息时长（分钟）", core.break_duration // 60, 176, 56)
        long_entry = add_field("长休息（分钟）", core.long_break_duration // 60, 24, 126)
        cycle_entry = add_field("长休息间隔（个）", core.cycles_before_long_break, 176, 126)

        # 主题
        tk.Label(win, text="主题", font=(FONT, 9), fg=p["muted"],
                 bg=p["card"]).place(x=sp(24), y=sp(196))
        theme_control = SegmentedControl(win, ["深色", "浅色"], lambda i: None,
                                         width=100, height=30, radius=15, bg=p["card"],
                                         track_color=p["card2"], accent=app.accent,
                                         text_color=p["text"], muted=p["muted"])
        theme_control.select(THEME_ORDER.index(app.theme_name))
        theme_control.place(x=sp(176), y=sp(192))

        # 开关
        auto_toggle = Toggle(win, core.auto_start, bg=p["card"], on_color=app.accent,
                             off_color=p["card3"])
        sound_toggle = Toggle(win, app.sound_on, bg=p["card"], on_color=app.accent,
                              off_color=p["card3"])
        tray_toggle = Toggle(win, app.tray_on, bg=p["card"], on_color=app.accent,
                             off_color=p["card3"])
        if not app.tray.available:
            tray_toggle.bind("<Button-1>", lambda e: None)

        rows = [("自动开始下一阶段", auto_toggle, 236), ("提示音", sound_toggle, 272),
                ("系统托盘", tray_toggle, 308)]
        for label, toggle, y in rows:
            tk.Label(win, text=label, font=(FONT, 10), fg=p["text"],
                     bg=p["card"]).place(x=sp(24), y=sp(y))
            toggle.place(relx=1.0, x=sp(-24), y=sp(y - 4), anchor="ne")

        def save_settings():
            try:
                work = int(work_entry.get())
                btime = int(break_entry.get())
                ltime = int(long_entry.get())
                cycles = int(cycle_entry.get())
                if min(work, btime, ltime, cycles) <= 0:
                    raise ValueError
            except ValueError:
                MessageDialog(app, "输入错误", "请输入大于 0 的整数").show()
                return

            core.apply_settings(work, btime, ltime, cycles, auto_toggle.value)
            app.sound_on = sound_toggle.value
            new_theme = THEME_ORDER[theme_control.current]
            tray_requested = tray_toggle.value and app.tray.available

            app.reset_timer()
            app.save_config()

            if tray_requested != app.tray.running:
                app.tray_on = tray_requested
                if tray_requested:
                    app.tray.start()
                else:
                    app.tray.stop()

            win.destroy()
            if new_theme != app.theme_name:
                app.set_theme(new_theme)
            else:
                app.sound_btn.config(text="♪" if app.sound_on else "♪̶")
                app.save_config()

        RoundedButton(win, "保存", save_settings, width=120, height=40, radius=20,
                      fill=app.accent, fill_hover=blend(app.accent, "#FFFFFF", 0.25),
                      fg="#FFFFFF", font=(FONT, 11, "bold"), bg=p["card"]).place(
            relx=0.5, y=sp(344), anchor="n")

        tk.Label(win, text=f"v{__version__}", font=(FONT, 8), fg=p["muted"],
                 bg=p["card"]).place(x=sp(24), y=sp(378))

        # 窗口拖动
        enable_drag(win, canvas, win)
