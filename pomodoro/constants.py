"""常量、默认配置、主题调色板与本地路径。"""

import os

# 全局字体
FONT = "Segoe UI"

# 主窗口设计尺寸（逻辑像素，会按 DPI 缩放）
DESIGN_W = 320
DESIGN_H = 462

# 数据目录与文件
APP_DIR = os.path.join(os.path.expanduser("~"), ".pomodoro_timer")
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
STATS_PATH = os.path.join(APP_DIR, "stats.json")

# 默认配置（时长单位：分钟）
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
    "task_date": "",
    "window_pos": None,
}

# 主题调色板
THEMES = {
    "dark": {
        "magic": "#1A1828",
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
        "magic": "#FEFFFF",
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
