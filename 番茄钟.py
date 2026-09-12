import json
import os
import threading
import time
import tkinter as tk
from tkinter import messagebox

try:
    import winsound
except ImportError:
    winsound = None

try:
    import pystray
except ImportError:
    pystray = None

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = None
    ImageDraw = None

# ----------------------------- DPI 缩放 -----------------------------
SCALE = 1.0


def sp(value):
    return int(round(value * SCALE))


def setup_dpi_awareness():
    if os.name != "nt":
        return
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


# ----------------------------- 路径与配置 -----------------------------
APP_DIR = os.path.join(os.path.expanduser("~"), ".pomodoro_timer")
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
STATS_PATH = os.path.join(APP_DIR, "stats.json")

DEFAULT_CONFIG = {
    "work_duration": 25,
    "break_duration": 5,
    "long_break_duration": 15,
    "cycles_before_long_break": 4,
    "auto_start": False,
    "countdown_mode": True,
    "theme": "dark",
    "sound": True,
    "tray": True,
    "task": "",
    "window_pos": None,
}

# ----------------------------- 主题 -----------------------------
THEMES = {
    "dark": {
        "magic": "#010203",
        "card": "#1E1B2E",
        "card2": "#2A2740",
        "card3": "#37314F",
        "track": "#171425",
        "text": "#F5F3FF",
        "muted": "#8E8AA6",
        "work": "#FF6B6B",
        "break": "#4ECDC4",
        "long": "#9B87F5",
    },
    "light": {
        "magic": "#010203",
        "card": "#FFFFFF",
        "card2": "#F0EEF7",
        "card3": "#E2DEF0",
        "track": "#E8E5F3",
        "text": "#241F35",
        "muted": "#7C7893",
        "work": "#FF5A5A",
        "break": "#1FA99E",
        "long": "#7C63E6",
    },
}
THEME_ORDER = ["dark", "light"]
THEME_LABELS = {"dark": "深色", "light": "浅色"}

FONT = "Segoe UI"


def create_round_rect(canvas, x1, y1, x2, y2, r, **kwargs):
    points = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


def _hex_to_rgb(color):
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def blend(color, other, t):
    r1, g1, b1 = _hex_to_rgb(color)
    r2, g2, b2 = _hex_to_rgb(other)
    return "#%02X%02X%02X" % (
        round(r1 + (r2 - r1) * t),
        round(g1 + (g2 - g1) * t),
        round(b1 + (b2 - b1) * t),
    )


class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command=None, width=110, height=44, radius=22,
                 fill="#2A2740", fill_hover="#37314F", fg="#F5F3FF",
                 font=(FONT, 11, "bold"), bg="#1E1B2E"):
        width, height, radius = sp(width), sp(height), sp(radius)
        super().__init__(parent, width=width, height=height, bg=bg,
                         highlightthickness=0, bd=0, cursor="hand2")
        self.command = command
        self._fill = fill
        self._fill_hover = fill_hover
        self._shape = create_round_rect(self, 1, 1, width - 1, height - 1, radius,
                                        fill=fill, outline=fill)
        self._text = self.create_text(width / 2, height / 2, text=text, fill=fg, font=font)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", lambda e: self.command() if self.command else None)

    def _on_enter(self, _):
        self.itemconfig(self._shape, fill=self._fill_hover, outline=self._fill_hover)

    def _on_leave(self, _):
        self.itemconfig(self._shape, fill=self._fill, outline=self._fill)

    def set_text(self, text):
        self.itemconfig(self._text, text=text)

    def set_colors(self, fill, fill_hover=None):
        self._fill = fill
        self._fill_hover = fill_hover or fill
        self.itemconfig(self._shape, fill=self._fill, outline=self._fill)


class SegmentedControl(tk.Canvas):
    def __init__(self, parent, options, command, width=176, height=36, radius=18,
                 bg="#1E1B2E", accent="#FF6B6B", text_color="#F5F3FF", muted="#8E8AA6",
                 track_color="#2A2740"):
        width, height, radius = sp(width), sp(height), sp(radius)
        super().__init__(parent, width=width, height=height, bg=bg,
                         highlightthickness=0, bd=0, cursor="hand2")
        self.options = options
        self.command = command
        self.current = 0
        self.width = width
        self.height = height
        self.radius = radius
        self.pad = sp(4)
        self.accent = accent
        self.text_color = text_color
        self.muted = muted
        self.track_color = track_color
        self._draw()
        self.bind("<Button-1>", self._on_click)

    def _draw(self):
        self.delete("all")
        create_round_rect(self, 1, 1, self.width - 1, self.height - 1,
                          self.radius, fill=self.track_color, outline=self.track_color)
        seg_w = (self.width - 2 * self.pad) / len(self.options)
        x0 = self.pad + self.current * seg_w
        create_round_rect(self, x0, self.pad, x0 + seg_w, self.height - self.pad,
                          self.radius - self.pad, fill=self.accent, outline=self.accent)
        for i, opt in enumerate(self.options):
            cx = self.pad + (i + 0.5) * seg_w
            color = self.text_color if i == self.current else self.muted
            self.create_text(cx, self.height / 2, text=opt, fill=color,
                             font=(FONT, 10, "bold"))

    def select(self, index):
        self.current = index
        self._draw()

    def _on_click(self, event):
        seg_w = (self.width - 2 * self.pad) / len(self.options)
        idx = int((event.x - self.pad) // seg_w)
        idx = max(0, min(len(self.options) - 1, idx))
        if idx != self.current:
            self.current = idx
            self._draw()
            self.command(idx)


class Toggle(tk.Canvas):
    def __init__(self, parent, value, command=None, width=44, height=24,
                 bg="#1E1B2E", on_color="#FF6B6B", off_color="#37314F",
                 knob_color="#FFFFFF"):
        width, height = sp(width), sp(height)
        super().__init__(parent, width=width, height=height, bg=bg,
                         highlightthickness=0, bd=0, cursor="hand2")
        self.value = bool(value)
        self.command = command
        self.w = width
        self.h = height
        self.on_color = on_color
        self.off_color = off_color
        self.knob_color = knob_color
        self._draw()
        self.bind("<Button-1>", self._click)

    def _draw(self):
        self.delete("all")
        color = self.on_color if self.value else self.off_color
        create_round_rect(self, 1, 1, self.w - 1, self.h - 1, (self.h - 2) / 2,
                          fill=color, outline=color)
        r = self.h - 6
        x = self.w - 3 - r if self.value else 3
        self.create_oval(x, 3, x + r, 3 + r, fill=self.knob_color, outline=self.knob_color)

    def set_value(self, value):
        self.value = bool(value)
        self._draw()

    def _click(self, _):
        self.value = not self.value
        self._draw()
        if self.command:
            self.command(self.value)


class PomodoroTimer:
    DESIGN_W = 320
    DESIGN_H = 462

    def __init__(self, root):
        global SCALE
        self.root = root
        SCALE = max(1.0, root.winfo_fpixels("1i") / 96.0)
        self.W = sp(self.DESIGN_W)
        self.H = sp(self.DESIGN_H)
        self.config = self.load_config()
        self.stats = self.load_stats()
        self.palette = THEMES.get(self.config.get("theme", "dark"), THEMES["dark"])
        self.theme_name = self.config.get("theme", "dark") if self.config.get("theme") in THEMES else "dark"

        # 计时状态
        self.work_duration = max(1, int(self.config["work_duration"])) * 60
        self.break_duration = max(1, int(self.config["break_duration"])) * 60
        self.long_break_duration = max(1, int(self.config["long_break_duration"])) * 60
        self.cycles_before_long_break = max(1, int(self.config["cycles_before_long_break"]))
        self.auto_start = bool(self.config["auto_start"])
        self.sound_on = bool(self.config["sound"])
        self.tray_available = pystray is not None and Image is not None and ImageDraw is not None
        self.tray_on = bool(self.config["tray"]) and self.tray_available
        self.countdown_mode = bool(self.config["countdown_mode"])
        self.task_name = self.config.get("task", "")
        self.cycle_completed = int(self.stats.get("cycle_completed", 0))

        self.current_duration = self.work_duration
        self.is_working = True
        self.in_long_break = False
        self.is_running = False
        self.start_time = 0
        self.elapsed_time = 0
        self.accent = self.palette["work"]

        # 拖动
        self._offset_x = 0
        self._offset_y = 0

        # 小球悬浮窗
        self.ball_window = None
        self.ball_canvas = None
        self.ball_ring = None
        self.ball_radius = sp(34)
        self.ball_x_offset = 0
        self.ball_y_offset = 0
        self.ball_time_label = None

        self.toast = None
        self.tray_icon = None

        self._setup_root()
        self.setup_ui()
        self.update_display()
        self.update_stats_label()
        self.restore_window_position()
        self._bind_shortcuts()
        self.start_tray()

    # ----------------------------- 持久化 -----------------------------
    @staticmethod
    def _read_json(path, default):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else default
        except (OSError, ValueError):
            return default

    @staticmethod
    def _write_json(path, data):
        try:
            os.makedirs(APP_DIR, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def load_config(self):
        cfg = dict(DEFAULT_CONFIG)
        cfg.update(self._read_json(CONFIG_PATH, {}))
        return cfg

    def load_stats(self):
        return self._read_json(STATS_PATH, {"daily": {}, "cycle_completed": 0})

    def save_config(self):
        self.config.update({
            "work_duration": self.work_duration // 60,
            "break_duration": self.break_duration // 60,
            "long_break_duration": self.long_break_duration // 60,
            "cycles_before_long_break": self.cycles_before_long_break,
            "auto_start": self.auto_start,
            "countdown_mode": self.countdown_mode,
            "theme": self.theme_name,
            "sound": self.sound_on,
            "tray": self.tray_on,
            "task": self.task_name,
        })
        self._write_json(CONFIG_PATH, self.config)

    def save_stats(self):
        self.stats["cycle_completed"] = self.cycle_completed
        self._write_json(STATS_PATH, self.stats)

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

    def _bind_shortcuts(self):
        self.root.bind_all("<space>", lambda e: self._hotkey(self.toggle_timer))
        self.root.bind_all("<KeyPress-r>", lambda e: self._hotkey(self.reset_timer))
        self.root.bind_all("<KeyPress-R>", lambda e: self._hotkey(self.reset_timer))
        self.root.bind_all("<Escape>", lambda e: self._hotkey(self.custom_iconify))
        self.root.bind_all("<KeyPress-s>", lambda e: self._hotkey(self.show_settings))
        self.root.bind_all("<KeyPress-S>", lambda e: self._hotkey(self.show_settings))

    def _hotkey(self, action):
        try:
            focused = self.root.focus_get()
        except (KeyError, tk.TclError):
            focused = None
        if isinstance(focused, (tk.Entry, tk.Text)):
            return None
        action()
        return "break"

    # ----------------------------- 主界面 -----------------------------
    def setup_ui(self):
        p = self.palette
        self.bg_canvas = tk.Canvas(self.root, width=self.W, height=self.H,
                                   bg=p["magic"], highlightthickness=0)
        self.bg_canvas.place(x=0, y=0)
        create_round_rect(self.bg_canvas, 0, 0, self.W, self.H, sp(24),
                          fill=p["card"], outline=p["card"])
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
        task_text = self.task_name.strip() or "＋ 点击设置任务"
        self.task_label = tk.Label(self.root, text=task_text, font=(FONT, 10),
                                   fg=p["text"] if self.task_name.strip() else p["muted"],
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
                                    fg=p["muted"], bg=p["card"])
        self.stats_label.place(relx=0.5, y=sp(310), anchor="n")

        # 模式切换
        self.mode_control = SegmentedControl(
            self.root, ["倒计时", "正计时"], self.on_mode_change,
            bg=p["card"], track_color=p["card2"], accent=self.palette["work"],
            text_color=p["text"], muted=p["muted"])
        if not self.countdown_mode:
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
        self.theme_name = name
        self.palette = THEMES[name]
        self.root.configure(bg=self.palette["magic"])
        try:
            self.root.wm_attributes("-transparentcolor", self.palette["magic"])
        except tk.TclError:
            pass
        for w in self.root.winfo_children():
            if isinstance(w, tk.Toplevel):
                continue
            w.destroy()
        self.setup_ui()
        self.update_display()
        self.update_stats_label()
        if self.ball_window:
            self._restyle_ball()
        self.save_config()

    def toggle_sound(self):
        self.sound_on = not self.sound_on
        self.sound_btn.config(text="♪" if self.sound_on else "♪̶")
        self.save_config()

    # ----------------------------- 逻辑 -----------------------------
    def on_mode_change(self, index):
        self.countdown_mode = (index == 0)
        self.save_config()
        self.reset_timer()

    def toggle_timer(self):
        if self.is_running:
            self.is_running = False
            self.start_pause_btn.set_text("继续")
            self.elapsed_time += time.time() - self.start_time
        else:
            self.is_running = True
            self.start_pause_btn.set_text("暂停")
            self.start_time = time.time()
            self.update()

    def update(self):
        if not self.is_running:
            return
        if self.countdown_mode:
            current = self.current_duration - (self.elapsed_time + (time.time() - self.start_time))
            if current <= 0:
                self.switch_phase()
                return
        else:
            current = self.elapsed_time + (time.time() - self.start_time)
            if current >= self.current_duration:
                self.switch_phase()
                return
        self.update_display(current)
        if self.ball_window:
            self.update_ball_display(current)
        self.root.after(200, self.update)

    def update_display(self, current=None):
        if current is None:
            current = (self.current_duration - self.elapsed_time) if self.countdown_mode else self.elapsed_time
        minutes = int(current // 60)
        seconds = int(current % 60)
        self.ring_canvas.itemconfig(self.time_item, text=f"{minutes:02d}:{seconds:02d}")
        fraction = current / self.current_duration if self.current_duration else 0
        fraction = max(0.0, min(1.0, fraction))
        self.ring_canvas.itemconfig(self.ring_arc, extent=-359.999 * fraction if fraction > 0 else 0)

        self.accent = self._phase_color()
        self.ring_canvas.itemconfig(self.ring_arc, outline=self.accent)
        self.start_pause_btn.set_colors(self.accent, blend(self.accent, "#FFFFFF", 0.25))
        self.mode_control.accent = self.accent
        self.mode_control._draw()
        self.title_label.config(fg=self.accent)
        self.status_label.config(text=self._phase_text(), fg=self.accent)

    def _phase_color(self):
        if self.is_working:
            return self.palette["work"]
        return self.palette["long"] if self.in_long_break else self.palette["break"]

    def _phase_text(self):
        if self.is_working:
            return "工作中"
        return "长休息中" if self.in_long_break else "休息中"

    def switch_phase(self):
        self.is_running = False
        self.start_pause_btn.set_text("开始")
        self.elapsed_time = 0
        if self.is_working:
            self.record_pomodoro()
            if self.cycle_completed % self.cycles_before_long_break == 0:
                self.in_long_break = True
                self.current_duration = self.long_break_duration
                title, message = "番茄完成 🍅", "进入长休息，好好放松一下"
            else:
                self.in_long_break = False
                self.current_duration = self.break_duration
                title, message = "番茄完成 🍅", "休息一下"
            self.is_working = False
        else:
            self.in_long_break = False
            self.is_working = True
            self.current_duration = self.work_duration
            title, message = "休息结束", "开始新的番茄"
        self.update_display()
        if self.ball_window:
            self.update_ball_display()
        self.notify(title, message)
        if self.auto_start:
            self.toggle_timer()

    def reset_timer(self):
        self.is_running = False
        self.start_pause_btn.set_text("开始")
        self.elapsed_time = 0
        self.is_working = True
        self.in_long_break = False
        self.current_duration = self.work_duration
        self.update_display()
        if self.ball_window:
            self.update_ball_display()

    # ----------------------------- 统计 -----------------------------
    def today_key(self):
        return time.strftime("%Y-%m-%d")

    def record_pomodoro(self):
        day = self.stats.setdefault("daily", {}).setdefault(
            self.today_key(), {"count": 0, "focus_seconds": 0, "tasks": {}})
        day["count"] = day.get("count", 0) + 1
        day["focus_seconds"] = day.get("focus_seconds", 0) + self.work_duration
        tasks = day.setdefault("tasks", {})
        name = self.task_name.strip() or "未命名"
        tasks[name] = tasks.get(name, 0) + 1
        self.cycle_completed += 1
        self.save_stats()
        self.update_stats_label()

    def update_stats_label(self):
        day = self.stats.get("daily", {}).get(self.today_key(), {})
        count = day.get("count", 0)
        minutes = day.get("focus_seconds", 0) // 60
        if hasattr(self, "stats_label"):
            self.stats_label.config(text=f"今日 {count} 个 · 专注 {minutes} 分钟")
        if self.ball_window:
            self.update_ball_display()

    # ----------------------------- 任务 -----------------------------
    def edit_task(self):
        p = self.palette
        dlg = tk.Toplevel(self.root)
        dlg.overrideredirect(True)
        dlg.wm_attributes("-topmost", 1)
        dlg.configure(bg=p["magic"])
        try:
            dlg.wm_attributes("-transparentcolor", p["magic"])
        except tk.TclError:
            pass
        W, H = sp(280), sp(156)
        x = self.root.winfo_x() + (self.W - W) // 2
        y = self.root.winfo_y() + sp(90)
        dlg.geometry(f"{W}x{H}+{max(0, x)}+{max(0, y)}")

        canvas = tk.Canvas(dlg, width=W, height=H, bg=p["magic"], highlightthickness=0)
        canvas.place(x=0, y=0)
        create_round_rect(canvas, 0, 0, W, H, sp(20), fill=p["card"], outline=p["card"])
        tk.Label(dlg, text="当前任务", font=(FONT, 12, "bold"), fg=p["text"],
                 bg=p["card"]).place(x=sp(24), y=sp(18))

        entry = tk.Entry(dlg, font=(FONT, 11), bg=p["card2"], fg=p["text"], relief="flat",
                         insertbackground=p["text"], highlightthickness=1,
                         highlightbackground=p["card3"], highlightcolor=self.accent)
        entry.insert(0, self.task_name)
        entry.place(x=sp(24), y=sp(52), width=W - sp(48), height=sp(34))
        entry.focus_set()
        entry.select_range(0, "end")

        def confirm(_=None):
            self.task_name = entry.get().strip()
            self.task_label.config(
                text=self.task_name or "＋ 点击设置任务",
                fg=p["text"] if self.task_name else p["muted"])
            self.save_config()
            dlg.destroy()

        entry.bind("<Return>", confirm)
        dlg.bind("<Escape>", lambda e: dlg.destroy())

        RoundedButton(dlg, "取消", dlg.destroy, width=90, height=36, radius=18,
                      fill=p["card2"], fill_hover=p["card3"], fg=p["text"],
                      font=(FONT, 10, "bold"), bg=p["card"]).place(x=sp(24), y=sp(102))
        RoundedButton(dlg, "确定", confirm, width=90, height=36, radius=18,
                      fill=self.accent, fill_hover=blend(self.accent, "#FFFFFF", 0.25),
                      fg="#FFFFFF", font=(FONT, 10, "bold"), bg=p["card"]).place(
            relx=1.0, x=sp(-24), y=sp(102), anchor="ne")

    # ----------------------------- 设置 -----------------------------
    def show_settings(self):
        p = self.palette
        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.wm_attributes("-topmost", 1)
        win.configure(bg=p["magic"])
        try:
            win.wm_attributes("-transparentcolor", p["magic"])
        except tk.TclError:
            pass
        W, H = sp(340), sp(400)
        x = self.root.winfo_x() + (self.W - W) // 2
        y = self.root.winfo_y() + sp(40)
        win.geometry(f"{W}x{H}+{max(0, x)}+{max(0, y)}")

        canvas = tk.Canvas(win, width=W, height=H, bg=p["magic"], highlightthickness=0)
        canvas.place(x=0, y=0)
        create_round_rect(canvas, 0, 0, W, H, sp(20), fill=p["card"], outline=p["card"])

        tk.Label(win, text="设置", font=(FONT, 13, "bold"), fg=p["text"],
                 bg=p["card"]).place(x=sp(24), y=sp(18))

        def close():
            win.destroy()

        close_btn = tk.Label(win, text="✕", font=(FONT, 12), fg=p["muted"], bg=p["card"],
                             cursor="hand2")
        close_btn.place(relx=1.0, x=sp(-20), y=sp(18), anchor="ne")
        close_btn.bind("<Button-1>", lambda e: close())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=p["work"]))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=p["muted"]))

        def add_field(label, value, x, y, width=140):
            x, y, width = sp(x), sp(y), sp(width)
            tk.Label(win, text=label, font=(FONT, 9), fg=p["muted"], bg=p["card"]).place(x=x, y=y)
            entry = tk.Entry(win, font=(FONT, 11), bg=p["card2"], fg=p["text"], relief="flat",
                             insertbackground=p["text"], justify="center",
                             highlightthickness=1, highlightbackground=p["card3"],
                             highlightcolor=self.accent)
            entry.insert(0, str(value))
            entry.place(x=x, y=y + sp(20), width=width, height=sp(32))
            return entry

        work_entry = add_field("工作时长（分钟）", self.work_duration // 60, 24, 56)
        break_entry = add_field("休息时长（分钟）", self.break_duration // 60, 176, 56)
        long_entry = add_field("长休息（分钟）", self.long_break_duration // 60, 24, 126)
        cycle_entry = add_field("长休息间隔（个）", self.cycles_before_long_break, 176, 126)

        # 主题
        tk.Label(win, text="主题", font=(FONT, 9), fg=p["muted"], bg=p["card"]).place(x=sp(24), y=sp(196))
        theme_control = SegmentedControl(win, ["深色", "浅色"], lambda i: None,
                                         width=100, height=30, radius=15, bg=p["card"],
                                         track_color=p["card2"], accent=self.accent,
                                         text_color=p["text"], muted=p["muted"])
        theme_control.select(THEME_ORDER.index(self.theme_name))
        theme_control.place(x=sp(176), y=sp(192))

        # 开关
        auto_toggle = Toggle(win, self.auto_start, bg=p["card"], on_color=self.accent,
                             off_color=p["card3"])
        sound_toggle = Toggle(win, self.sound_on, bg=p["card"], on_color=self.accent,
                              off_color=p["card3"])
        tray_toggle = Toggle(win, self.tray_on, bg=p["card"], on_color=self.accent,
                             off_color=p["card3"])
        if pystray is None:
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
                messagebox.showerror("输入错误", "请输入大于 0 的整数")
                return
            self.work_duration = work * 60
            self.break_duration = btime * 60
            self.long_break_duration = ltime * 60
            self.cycles_before_long_break = cycles
            self.auto_start = auto_toggle.value
            self.sound_on = sound_toggle.value
            new_theme = THEME_ORDER[theme_control.current]
            tray_requested = tray_toggle.value and pystray is not None
            self.reset_timer()
            self.save_config()
            if tray_requested != (self.tray_icon is not None):
                self.tray_on = tray_requested
                if tray_requested:
                    self.start_tray()
                else:
                    self.stop_tray()
            close()
            if new_theme != self.theme_name:
                self.set_theme(new_theme)
            else:
                self.sound_btn.config(text="♪" if self.sound_on else "♪̶")
                self.save_config()

        RoundedButton(win, "保存", save_settings, width=120, height=40, radius=20,
                      fill=self.accent, fill_hover=blend(self.accent, "#FFFFFF", 0.25),
                      fg="#FFFFFF", font=(FONT, 11, "bold"), bg=p["card"]).place(
            relx=0.5, y=sp(344), anchor="n")

        drag = {"x": 0, "y": 0}

        def start(e):
            drag["x"] = e.x_root - win.winfo_x()
            drag["y"] = e.y_root - win.winfo_y()

        def move(e):
            win.geometry(f"+{e.x_root - drag['x']}+{e.y_root - drag['y']}")

        for w in (canvas, win):
            w.bind("<Button-1>", start)
            w.bind("<B1-Motion>", move)

    # ----------------------------- 提示 -----------------------------
    def notify(self, title, message):
        if self.sound_on:
            self.play_sound()
        self.show_toast(title, message)

    def play_sound(self):
        if winsound is None:
            return
        try:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except RuntimeError:
            pass

    def show_toast(self, title, message):
        p = self.palette
        if self.toast is not None:
            try:
                self.toast.destroy()
            except tk.TclError:
                pass
        t = tk.Toplevel(self.root)
        self.toast = t
        t.overrideredirect(True)
        t.wm_attributes("-topmost", 1)
        t.configure(bg=p["magic"])
        try:
            t.wm_attributes("-transparentcolor", p["magic"])
        except tk.TclError:
            pass
        W, H = sp(260), sp(84)
        x = t.winfo_screenwidth() - W - sp(20)
        y = t.winfo_screenheight() - H - sp(60)
        t.geometry(f"{W}x{H}+{x}+{y}")

        canvas = tk.Canvas(t, width=W, height=H, bg=p["magic"], highlightthickness=0)
        canvas.pack()
        create_round_rect(canvas, 0, 0, W, H, sp(16), fill=p["card"], outline=p["card"])
        canvas.create_rectangle(0, 0, sp(5), H, fill=self.accent, outline=self.accent)
        canvas.create_text(sp(20), sp(26), text=title, anchor="w", fill=self.accent,
                           font=(FONT, 11, "bold"))
        canvas.create_text(sp(20), sp(52), text=message, anchor="w", fill=p["text"],
                           font=(FONT, 9))

        def dismiss(_=None):
            try:
                t.destroy()
            except tk.TclError:
                pass
            self.toast = None

        t.bind("<Button-1>", dismiss)
        t.after(4000, dismiss)

    # ----------------------------- 小球悬浮窗 -----------------------------
    def update_ball_display(self, current=None):
        if current is None:
            current = (self.current_duration - self.elapsed_time) if self.countdown_mode else self.elapsed_time
        minutes = int(current // 60)
        seconds = int(current % 60)
        if self.ball_time_label is not None:
            self.ball_time_label.config(text=f"{minutes:02d}:{seconds:02d}")
        if self.ball_canvas is not None and self.ball_ring is not None:
            self.ball_canvas.itemconfig(self.ball_ring, outline=self.accent)

    def _restyle_ball(self):
        if self.ball_canvas is None or self.ball_ring is None:
            return
        p = self.palette
        self.ball_canvas.configure(bg=p["magic"])
        self.ball_canvas.itemconfig(self.ball_ring, outline=self.accent, fill=p["card"])
        if self.ball_time_label is not None:
            self.ball_time_label.configure(bg=p["card"], fg=p["text"])

    def custom_iconify(self):
        self.root.withdraw()
        self.create_ball_window()

    def create_ball_window(self):
        if self.ball_window is not None:
            return
        p = self.palette
        d = self.ball_radius * 2
        ball = tk.Toplevel(self.root)
        self.ball_window = ball
        ball.overrideredirect(True)
        ball.wm_attributes("-topmost", 1)
        ball.configure(bg=p["magic"])
        try:
            ball.wm_attributes("-transparentcolor", p["magic"])
        except tk.TclError:
            pass

        x = ball.winfo_screenwidth() - d - sp(10)
        y = sp(10)
        ball.geometry(f"{d}x{d}+{x}+{y}")

        self.ball_canvas = tk.Canvas(ball, width=d, height=d, bg=p["magic"],
                                     highlightthickness=0)
        self.ball_canvas.pack()
        self.ball_ring = self.ball_canvas.create_oval(sp(4), sp(4), d - sp(4), d - sp(4),
                                                      outline=self.accent, width=sp(4),
                                                      fill=p["card"])
        self.ball_time_label = tk.Label(ball, font=(FONT, 11, "bold"), fg=p["text"], bg=p["card"])
        self.ball_time_label.place(relx=0.5, rely=0.5, anchor="center")
        self.update_ball_display()

        ball.bind("<Button-1>", self.on_ball_drag_start)
        ball.bind("<B1-Motion>", self.on_ball_drag_motion)
        ball.bind("<Double-Button-1>", self.restore_from_ball)

    def on_ball_drag_start(self, event):
        self.ball_x_offset = event.x
        self.ball_y_offset = event.y

    def on_ball_drag_motion(self, event):
        ball = self.ball_window
        if ball is None:
            return
        x = ball.winfo_x() + event.x - self.ball_x_offset
        y = ball.winfo_y() + event.y - self.ball_y_offset
        ball.geometry(f"+{x}+{y}")

    def restore_from_ball(self, event=None):
        if self.ball_window:
            self.ball_window.destroy()
            self.ball_window = None
        self.ball_canvas = None
        self.ball_ring = None
        self.ball_time_label = None
        self.root.deiconify()
        self.root.lift()

    def show_main(self):
        self.restore_from_ball()
        try:
            self.root.focus_force()
        except tk.TclError:
            pass

    # ----------------------------- 系统托盘 -----------------------------
    def _tray_image(self):
        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        color = self.palette["work"]
        draw.ellipse((6, 12, size - 6, size - 6), fill=color)
        draw.polygon([(size // 2 - 10, 14), (size // 2, 4), (size // 2 + 10, 14)],
                     fill=self.palette["break"])
        return img

    def start_tray(self):
        if not self.tray_available or self.tray_icon is not None:
            return
        menu = pystray.Menu(
            pystray.MenuItem("显示主界面", lambda i, it: self.root.after(0, self.show_main),
                             default=True),
            pystray.MenuItem("收起为小球", lambda i, it: self.root.after(0, self.custom_iconify)),
            pystray.MenuItem("退出", lambda i, it: self.root.after(0, self.quit_app)),
        )
        self.tray_icon = pystray.Icon("pomodoro", self._tray_image(), "番茄钟", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def stop_tray(self):
        if self.tray_icon is None:
            return
        try:
            self.tray_icon.stop()
        except Exception:
            pass
        self.tray_icon = None

    # ----------------------------- 退出 -----------------------------
    def quit_app(self):
        try:
            self.config["window_pos"] = [self.root.winfo_x(), self.root.winfo_y()]
        except tk.TclError:
            pass
        self.save_config()
        self.save_stats()
        self.stop_tray()
        try:
            self.root.destroy()
        except tk.TclError:
            pass


if __name__ == "__main__":
    setup_dpi_awareness()
    root = tk.Tk()
    app = PomodoroTimer(root)
    root.mainloop()
