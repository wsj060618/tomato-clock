"""配置与统计的本地持久化（JSON 文件）。"""

import json
import os
import time

from .constants import APP_DIR, CONFIG_PATH, STATS_PATH, DEFAULT_CONFIG


def today_key():
    """返回今天的日期字符串，用作统计的分组键。"""
    return time.strftime("%Y-%m-%d")


def _read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else default
    except (OSError, ValueError):
        return default


def _write_json(path, data):
    try:
        os.makedirs(APP_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def load_config():
    """读取配置，缺失项用默认值补齐。"""
    config = dict(DEFAULT_CONFIG)
    config.update(_read_json(CONFIG_PATH, {}))
    return config


def save_config(config):
    _write_json(CONFIG_PATH, config)


def load_stats():
    """读取统计数据。"""
    return _read_json(STATS_PATH, {"daily": {}, "cycle_completed": 0})


def save_stats(stats):
    _write_json(STATS_PATH, stats)
