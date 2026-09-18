"""主窗口：组装界面、计时状态机、托盘与各类弹窗。"""

import time
import tkinter as tk

from .. import sound, storage
from ..constants import DESIGN_H, DESIGN_W, FONT, THEMES, THEME_ORDER
from ..theme import blend, set_scale, sp
from ..timer import TimerCore
from ..tray import TrayController
from ..widgets import RoundedButton, SegmentedControl, paint_card
from .floating_ball import FloatingBall
from .history_dialog import HistoryDialog
from .settings_dialog import SettingsDialog
from .task_dialog import TaskDialog
from .toast import ToastManager


class PomodoroApp:
    def __init__(self, root):
        self.root = root
        set_scale(root.winfo_fpixels("1i"))
        self.W = sp(DESIGN_W)
        self.H = sp(DESIGN_H)

        self.config = storage.load_config()
        self.animations = bool(self.config.get("animations", True))
        self.stats = storage.load_stats()
        self.core = TimerCore(self.config, self.stats)

        self.theme_name = self.config.get("theme", "dark")
        if self.theme_name not in THEMES:
            self.theme_name = "dark"
        self.palette = THEMES[self.theme_name]
        self.accent = self.core.phase_color(self.palette)

        self.sound_on = bool(self.config["sound"])
        self.tray = TrayController(self)
        self.tray_on = bool(self.config["tray"]) and self.tray.available

        self._offset_x = 0
        self._offset_y = 0
        self._intro_done = False
        self._intro_start = 0.0

        self.toast = ToastManager(self)
        self.ball = FloatingBall(self)

        self._setup_root()
        self.build_ui()
        self.render()
        self.update_stats_label()
        self.restore_window_position()
        self._bind_shortcuts()
        if self.tray_on:
            self.tray.start()
        self._start_intro()
        self.root.after(30000, self._check_day_rollover)

    # ----------------------------- 根窗口 -----------------------------
    def _setup_root(self):
        self.root.title("番茄钟")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", 1)
        self.root.configure(bg=self.palette["magic"])
        try:
            self.root.wm_attributes("-transparentcolor", self.palette["magic"])
        except tk.TclError:
            pass
        if self.animations:
            try:
                self.root.attributes("-alpha", 0.0)
            except tk.TclError:
                pass

    def _bind_shortcuts(self):
        self.root.bind_all("<space>", lambda e: self._hotkey(self.toggle_timer))
        self.root.bind_all("<KeyPress-r>", lambda e: self._hotkey(self.reset_timer))
        self.root.bind_all("<KeyPress-R>", lambda e: self._hotkey(self.reset_timer))
        self.root.bind_all("<Escape>", lambda e: self._hotkey(self.custom_iconify))
        self.root.bind_all("<KeyPress-s>", lambda e: self._hotkey(self.show_settings))
        self.root.bind_all("<KeyPress-S>", lambda e: self._hotkey(self.show_settings))
        self.root.bind_all("<KeyPress-h>", lambda e: self._hotkey(self.show_history))
        self.root.bind_all("<KeyPress-H>", lambda e: self._hotkey(self.show_history))

    def _hotkey(self, action):
        try:
            focused = self.root.focus_get()
        except (KeyError, tk.TclError):
            focused = None
        if isinstance(focused, (tk.Entry, tk.Text)):
            return None
        action()
        return "break"

    # ----------------------------- 启动动画 -----------------------------
    def _start_intro(self):
        """启动时的淡入 + 环形进度扫过；关闭动画或不可用时直接结束。"""
        if not self.animations or not hasattr(self, "ring_arc"):
            self._intro_done = True
            return
        self._intro_value = max(0.0, self.core.display_value())
        self._intro_start = time.perf_counter()
        self._apply_intro(0.0, 0.0)
        self.root.after(16, self._intro_tick)

    def _intro_tick(self):
        if self._intro_done:
            return
        elapsed = time.perf_counter() - self._intro_start
        fade = min(1.0, elapsed / 0.35)
        sweep = min(1.0, elapsed / 0.45)
        self._apply_intro(fade, sweep)
        if fade >= 1.0 and sweep >= 1.0:
            self._finish_intro()
        else:
            self.root.after(16, self._intro_tick)

    def _apply_intro(self, fade, sweep):
        try:
            self.root.attributes("-alpha", 1 - (1 - fade) ** 3)
        except tk.TclError:
            pass
        fraction = self.core.progress(self._intro_value) * (1 - (1 - sweep) ** 3)
        self.ring_canvas.itemconfig(
            self.ring_arc, extent=-359.999 * fraction if fraction > 0 else 0)

    def _finish_intro(self):
        if self._intro_done:
            return
        self._intro_done = True
        try:
            self.root.attributes("-alpha", 1.0)
        except tk.TclError:
            pass
        self.render()

    # ----------------------------- 主界面 -----------------------------
    def build_ui(self):
        p = self.palette
        self.bg_canvas = tk.Canvas(self.root, width=self.W, height=self.H,
                                   bg=p["magic"], highlightthickness=0)
        self.bg_canvas.place(x=0, y=0)
        paint_card(self.bg_canvas, self.W, self.H, sp(24), p["card"], p["magic"])
        self._make_draggable(self.bg_canvas)

        # 顶部标题栏
        self.title_label = tk.Label(self.root, text="●  番茄钟", font=(FONT, 11, "bold"),
                                    fg=self.accent, bg=p["card"])
        self.title_label.place(x=sp(20), y=sp(15))
        self._make_draggable(self.title_label)

        def make_tool(relx_offset, text, command, hover=None):
            lbl = tk.Label(self.root, text=text, font=(FONT, 12), fg=p["muted"],
                           bg=p["card"], cursor="hand2")
            lbl.place(relx=1.0, x=sp(relx_offset), y=sp(15), anchor="ne")
            lbl.bind("<Button-1>", lambda e: command())
            lbl.bind("<Enter>", lambda e: lbl.config(fg=hover or p["text"]))
            lbl.bind("<Leave>", lambda e: lbl.config(fg=p["muted"]))
            return lbl

        self.close_btn = make_tool(-16, "✕", self.quit_app, p["work"])
        self.minimize_btn = make_tool(-48, "—", self.custom_iconify)
        self.sound_btn = make_tool(-80, "♪" if self.sound_on else "♪̶", self.toggle_sound)
        self.theme_btn = make_tool(-112, "◐", self.toggle_theme)

        # 任务
        task_text = self.core.task_name.strip() or "＋ 点击设置任务"
        self.task_label = tk.Label(self.root, text=task_text, font=(FONT, 10),
                                   fg=p["text"] if self.core.task_name.strip() else p["muted"],
                                   bg=p["card"], cursor="hand2")
        self.task_label.place(relx=0.5, y=sp(52), anchor="n")
        self.task_label.bind("<Button-1>", lambda e: self.edit_task())

        # 状态
        self.status_label = tk.Label(self.root, text="工作中", font=(FONT, 10),
                                     fg=p["muted"], bg=p["card"])
        self.status_label.place(relx=0.5, y=sp(78), anchor="n")

        # 环形进度 + 时间
        self.ring_canvas = tk.Canvas(self.root, width=sp(200), height=sp(200), bg=p["card"],
                                     highlightthickness=0)
        self.ring_canvas.place(relx=0.5, y=sp(102), anchor="n")
        self.ring_canvas.create_oval(sp(10), sp(10), sp(190), sp(190),
                                     outline=p["track"], width=sp(12))
        self.ring_arc = self.ring_canvas.create_arc(sp(10), sp(10), sp(190), sp(190), start=90,
                                                    extent=-359.999, style="arc",
                                                    outline=self.accent, width=sp(12))
        self.time_item = self.ring_canvas.create_text(sp(100), sp(100), text="25:00",
                                                      fill=p["text"], font=(FONT, 38, "bold"))

        # 统计
        self.stats_label = tk.Label(self.root, text="", font=(FONT, 9),
                                    fg=p["muted"], bg=p["card"], cursor="hand2")
        self.stats_label.place(relx=0.5, y=sp(310), anchor="n")
        self.stats_label.bind("<Button-1>", lambda e: self.show_history())
        self.stats_label.bind("<Enter>", lambda e: self.stats_label.config(fg=self.accent))
        self.stats_label.bind("<Leave>", lambda e: self.stats_label.config(fg=p["muted"]))

        # 模式切换
        self.mode_control = SegmentedControl(
            self.root, ["倒计时", "正计时"], self.on_mode_change,
            bg=p["card"], track_color=p["card2"], accent=self.palette["work"],
            text_color=p["text"], muted=p["muted"])
        if not self.core.countdown_mode:
            self.mode_control.select(1)
        self.mode_control.place(relx=0.5, y=sp(336), anchor="n")

        # 按钮
        self.reset_btn = RoundedButton(self.root, "重置", self.reset_timer,
                                       width=64, height=44, radius=22,
                                       fill=p["card2"], fill_hover=p["card3"], fg=p["text"],
                                       font=(FONT, 10, "bold"), bg=p["card"])
        self.reset_btn.place(x=sp(18), y=sp(386))

        self.start_pause_btn = RoundedButton(self.root, "开始", self.toggle_timer,
                                             width=140, height=44, radius=22,
                                             fill=self.accent,
                                             fill_hover=blend(self.accent, "#FFFFFF", 0.25),
                                             fg="#FFFFFF", font=(FONT, 11, "bold"),
                                             bg=p["card"])
        self.start_pause_btn.place(relx=0.5, y=sp(386), anchor="n")

        self.settings_btn = RoundedButton(self.root, "设置", self.show_settings,
                                          width=64, height=44, radius=22,
                                          fill=p["card2"], fill_hover=p["card3"], fg=p["text"],
                                          font=(FONT, 10, "bold"), bg=p["card"])
        self.settings_btn.place(relx=1.0, x=sp(-18), y=sp(386), anchor="ne")

    def _make_draggable(self, widget):
        widget.bind("<Button-1>", self.on_drag_start)
        widget.bind("<B1-Motion>", self.on_drag_motion)

    def on_drag_start(self, event):
        self._offset_x = event.x_root - self.root.winfo_x()
        self._offset_y = event.y_root - self.root.winfo_y()

    def on_drag_motion(self, event):
        x = event.x_root - self._offset_x
        y = event.y_root - self._offset_y
        self.root.geometry(f"+{x}+{y}")

    def restore_window_position(self):
        self.root.geometry(f"{self.W}x{self.H}")
        pos = self.config.get("window_pos")
        if isinstance(pos, (list, tuple)) and len(pos) == 2:
            self.root.geometry(f"+{int(pos[0])}+{int(pos[1])}")
        else:
            x = self.root.winfo_screenwidth() - self.W - sp(20)
            self.root.geometry(f"+{x}+{sp(50)}")

    # ----------------------------- 主题 -----------------------------
    def toggle_theme(self):
        idx = (THEME_ORDER.index(self.theme_name) + 1) % len(THEME_ORDER)
        self.set_theme(THEME_ORDER[idx])

    def set_theme(self, name):
        if name not in THEMES:
            return
        self._finish_intro()
        self.theme_name = name
        self.palette = THEMES[name]
        self.config["theme"] = name
        self.root.configure(bg=self.palette["magic"])
        try:
            self.root.wm_attributes("-transparentcolor", self.palette["magic"])
        except tk.TclError:
            pass
        for w in self.root.winfo_children():
            if isinstance(w, tk.Toplevel):
                continue
            w.destroy()
        self.build_ui()
        self.render()
        self.update_stats_label()
        if self.ball.visible:
            self.ball.restyle()
        self.save_config()

    def toggle_sound(self):
        self.sound_on = not self.sound_on
        self.sound_btn.config(text="♪" if self.sound_on else "♪̶")
        self.save_config()

    # ----------------------------- 逻辑 -----------------------------
    def on_mode_change(self, index):
        self.core.countdown_mode = (index == 0)
        self.save_config()
        self.reset_timer()

    def toggle_timer(self):
        self._finish_intro()
        self.core.toggle()
        self.start_pause_btn.set_text("暂停" if self.core.is_running else "继续")
        if self.core.is_running:
            self._tick()

    def _tick(self):
        if not self.core.is_running:
            return
        current, switched = self.core.tick()
        self.render(current)
        if self.ball.visible:
            self.ball.update(current)
        if switched:
            self._handle_phase_end()
        if self.core.is_running:
            self.root.after(200, self._tick)

    def _handle_phase_end(self):
        title, message = self.core.last_event
        self.start_pause_btn.set_text("开始")
        self.render()
        if self.ball.visible:
            self.ball.update()
        self.notify(title, message)
        if self.core.auto_start:
            self.core.start()
            self.start_pause_btn.set_text("暂停")

    def render(self, current=None):
        if current is None:
            current = self.core.display_value()
        minutes = int(current // 60)
        seconds = int(current % 60)
        self.ring_canvas.itemconfig(self.time_item, text=f"{minutes:02d}:{seconds:02d}")
        fraction = self.core.progress(current)
        self.ring_canvas.itemconfig(self.ring_arc,
                                    extent=-359.999 * fraction if fraction > 0 else 0)

        self.accent = self.core.phase_color(self.palette)
        self.ring_canvas.itemconfig(self.ring_arc, outline=self.accent)
        self.start_pause_btn.set_colors(self.accent, blend(self.accent, "#FFFFFF", 0.25))
        self.mode_control.accent = self.accent
        self.mode_control._draw()
        self.title_label.config(fg=self.accent)
        self.status_label.config(text=self.core.phase_text(), fg=self.accent)

    def reset_timer(self):
        self._finish_intro()
        self.core.reset()
        self.start_pause_btn.set_text("开始")
        self.render()
        if self.ball.visible:
            self.ball.update()

    # ----------------------------- 统计 -----------------------------
    def update_stats_label(self):
        count, minutes = self.core.today_stats()
        if hasattr(self, "stats_label"):
            self.stats_label.config(text=f"今日 {count} 个 · 专注 {minutes} 分钟 ›")
        if self.ball.visible:
            self.ball.update()

    def show_history(self):
        HistoryDialog(self).show()

    # ----------------------------- 任务 -----------------------------
    def set_task(self, name):
        self.core.set_task(name)
        if hasattr(self, "task_label"):
            self.task_label.config(
                text=self.core.task_name or "＋ 点击设置任务",
                fg=self.palette["text"] if self.core.task_name else self.palette["muted"])
        self.save_config()

    def _check_day_rollover(self):
        if self.core.check_day_rollover():
            if hasattr(self, "task_label"):
                self.task_label.config(text="＋ 点击设置任务", fg=self.palette["muted"])
            self.update_stats_label()
        self.root.after(30000, self._check_day_rollover)

    def edit_task(self):
        TaskDialog(self).show()

    # ----------------------------- 设置 -----------------------------
    def show_settings(self):
        SettingsDialog(self).show()

    # ----------------------------- 提示 -----------------------------
    def notify(self, title, message):
        if self.sound_on:
            sound.play()
        self.toast.show(title, message)

    # ----------------------------- 悬浮球 -----------------------------
    def custom_iconify(self):
        self.root.withdraw()
        self.ball.show()

    def restore_from_ball(self):
        self.ball.hide()
        self.root.deiconify()
        self.root.lift()

    def show_main(self):
        self.restore_from_ball()
        try:
            self.root.focus_force()
        except tk.TclError:
            pass

    # ----------------------------- 持久化与退出 -----------------------------
    def save_config(self):
        self.core.sync_config()
        self.config["theme"] = self.theme_name
        self.config["sound"] = self.sound_on
        self.config["tray"] = self.tray_on
        self.config["animations"] = self.animations
        storage.save_config(self.config)

    def save_stats(self):
        storage.save_stats(self.stats)

    def quit_app(self):
        try:
            self.config["window_pos"] = [self.root.winfo_x(), self.root.winfo_y()]
        except tk.TclError:
            pass
        self.save_config()
        self.save_stats()
        self.tray.stop()
        try:
            self.root.destroy()
        except tk.TclError:
            pass
