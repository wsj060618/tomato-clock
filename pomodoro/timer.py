"""计时状态机（与界面无关，可单独测试）。"""

import time

from . import storage


class TimerCore:
    """番茄钟的阶段、计时与统计逻辑。

    只维护状态与数据，不涉及任何 Tk 控件；界面通过 tick() 推进并读取状态。
    """

    def __init__(self, config, stats):
        self.config = config
        self.stats = stats

        self.work_duration = max(1, int(config["work_duration"])) * 60
        self.break_duration = max(1, int(config["break_duration"])) * 60
        self.long_break_duration = max(1, int(config["long_break_duration"])) * 60
        self.cycles_before_long_break = max(1, int(config["cycles_before_long_break"]))
        self.auto_start = bool(config["auto_start"])
        self.countdown_mode = bool(config["countdown_mode"])

        self.current_day = storage.today_key()
        self.task_name = ""
        config["task"] = ""
        config["task_date"] = self.current_day

        self.cycle_completed = int(stats.get("cycle_completed", 0))
        self.cycles_in_set = 0

        self.current_duration = self.work_duration
        self.is_working = True
        self.in_long_break = False
        self.is_running = False
        self.start_time = 0.0
        self.elapsed_time = 0.0
        self.last_event = ("", "")

    # ----------------------------- 阶段 -----------------------------
    def phase_key(self):
        if self.is_working:
            return "work"
        return "long" if self.in_long_break else "break"

    def phase_text(self):
        return {"work": "工作中", "break": "休息中", "long": "长休息中"}[self.phase_key()]

    def phase_color(self, palette):
        return palette[self.phase_key()]

    # ----------------------------- 计时 -----------------------------
    def start(self):
        self.is_running = True
        self.start_time = time.time()

    def pause(self):
        if self.is_running:
            self.elapsed_time += time.time() - self.start_time
        self.is_running = False

    def toggle(self):
        """开始/暂停，返回切换后的运行状态。"""
        if self.is_running:
            self.pause()
        else:
            self.start()
        return self.is_running

    def reset(self):
        self.is_running = False
        self.elapsed_time = 0.0
        self.is_working = True
        self.in_long_break = False
        self.cycles_in_set = 0
        self.current_duration = self.work_duration

    def _current(self, now):
        delta = (now - self.start_time) if self.is_running else 0.0
        if self.countdown_mode:
            return self.current_duration - (self.elapsed_time + delta)
        return self.elapsed_time + delta

    def display_value(self):
        """未运行时用于显示的秒数。"""
        return self._current(time.time())

    def progress(self, current):
        if not self.current_duration:
            return 0.0
        return max(0.0, min(1.0, current / self.current_duration))

    def tick(self):
        """推进计时，返回 (当前秒数, 是否切换了阶段)。"""
        if not self.is_running:
            return self.display_value(), False
        current = self._current(time.time())
        finished = current <= 0 if self.countdown_mode else current >= self.current_duration
        if finished:
            self._advance_phase()
            return 0.0, True
        return current, False

    def _advance_phase(self):
        self.is_running = False
        self.elapsed_time = 0.0
        if self.is_working:
            self.record_pomodoro()
            self.cycles_in_set += 1
            if self.cycles_in_set >= self.cycles_before_long_break:
                self.cycles_in_set = 0
                self.in_long_break = True
                self.current_duration = self.long_break_duration
                event = ("番茄完成 🍅", "进入长休息，好好放松一下")
            else:
                self.in_long_break = False
                self.current_duration = self.break_duration
                event = ("番茄完成 🍅", "休息一下")
            self.is_working = False
        else:
            self.in_long_break = False
            self.is_working = True
            self.current_duration = self.work_duration
            event = ("休息结束", "开始新的番茄")
        self.last_event = event

    # ----------------------------- 统计 -----------------------------
    def record_pomodoro(self):
        day = self.stats.setdefault("daily", {}).setdefault(
            storage.today_key(), {"count": 0, "focus_seconds": 0, "tasks": {}})
        day["count"] = day.get("count", 0) + 1
        day["focus_seconds"] = day.get("focus_seconds", 0) + self.work_duration
        tasks = day.setdefault("tasks", {})
        name = self.task_name.strip() or "未命名"
        tasks[name] = tasks.get(name, 0) + 1
        self.cycle_completed += 1
        storage.save_stats(self.stats)

    def today_stats(self):
        """返回 (今日完成数, 今日专注分钟数)。"""
        day = self.stats.get("daily", {}).get(storage.today_key(), {})
        return day.get("count", 0), day.get("focus_seconds", 0) // 60

    # ----------------------------- 配置 -----------------------------
    def set_task(self, name):
        self.task_name = (name or "").strip()
        self.current_day = storage.today_key()
        self.config["task"] = self.task_name
        self.config["task_date"] = self.current_day

    def check_day_rollover(self):
        """跨天且当前无进行中的计时时清空任务，返回是否发生变化。"""
        today = storage.today_key()
        if today != self.current_day and not self.is_running and self.elapsed_time == 0:
            self.current_day = today
            if self.task_name:
                self.set_task("")
            return True
        return False

    def apply_settings(self, work, break_time, long_break, cycles, auto_start):
        """应用设置窗口的时长/间隔/自动开始，单位分钟。"""
        self.work_duration = work * 60
        self.break_duration = break_time * 60
        self.long_break_duration = long_break * 60
        self.cycles_before_long_break = cycles
        self.auto_start = auto_start
        self.reset()

    def sync_config(self):
        """把运行时状态写回配置字典（供保存）。"""
        c = self.config
        c["work_duration"] = self.work_duration // 60
        c["break_duration"] = self.break_duration // 60
        c["long_break_duration"] = self.long_break_duration // 60
        c["cycles_before_long_break"] = self.cycles_before_long_break
        c["auto_start"] = self.auto_start
        c["countdown_mode"] = self.countdown_mode
        c["task"] = self.task_name
        c["task_date"] = self.current_day
