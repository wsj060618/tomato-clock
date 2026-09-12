import os
import tempfile
import unittest

from pomodoro import storage
from pomodoro.timer import TimerCore


def make_config(**overrides):
    cfg = {
        "work_duration": 25,
        "break_duration": 5,
        "long_break_duration": 15,
        "cycles_before_long_break": 4,
        "auto_start": False,
        "countdown_mode": True,
        "task": "",
        "task_date": storage.today_key(),
    }
    cfg.update(overrides)
    return cfg


class TimerCoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pomodoro_test_")
        self._dir = storage.APP_DIR
        self._stats = storage.STATS_PATH
        storage.APP_DIR = self.tmp
        storage.STATS_PATH = os.path.join(self.tmp, "stats.json")

    def tearDown(self):
        storage.APP_DIR = self._dir
        storage.STATS_PATH = self._stats

    def make_core(self, stats=None, **overrides):
        stats = stats if stats is not None else {"daily": {}, "cycle_completed": 0}
        return TimerCore(make_config(**overrides), stats)

    def test_phase_key_and_text(self):
        core = self.make_core()
        self.assertEqual(core.phase_key(), "work")
        self.assertEqual(core.phase_text(), "工作中")
        core.is_working = False
        self.assertEqual(core.phase_key(), "break")
        core.in_long_break = True
        self.assertEqual(core.phase_key(), "long")
        self.assertEqual(core.phase_text(), "长休息中")

    def test_toggle_start_pause(self):
        core = self.make_core()
        self.assertTrue(core.toggle())
        self.assertTrue(core.is_running)
        self.assertFalse(core.toggle())
        self.assertFalse(core.is_running)

    def test_progress_clamped(self):
        core = self.make_core()
        self.assertEqual(core.progress(0), 0.0)
        self.assertEqual(core.progress(core.current_duration * 2), 1.0)

    def test_finish_work_records_and_switches_to_break(self):
        core = self.make_core(work_duration=1)
        core.is_running = True
        core.start_time = 0
        core.elapsed_time = core.current_duration + 1
        current, switched = core.tick()
        self.assertTrue(switched)
        self.assertFalse(core.is_working)
        self.assertFalse(core.in_long_break)
        self.assertEqual(core.current_duration, core.break_duration)
        self.assertEqual(core.today_stats()[0], 1)

    def test_finish_countup(self):
        core = self.make_core(work_duration=1, countdown_mode=False)
        core.is_running = True
        core.start_time = 0
        core.elapsed_time = core.current_duration + 1
        _, switched = core.tick()
        self.assertTrue(switched)
        self.assertFalse(core.is_working)

    def test_long_break_every_n(self):
        core = self.make_core(work_duration=1, cycles_before_long_break=1)
        core.is_running = True
        core.start_time = 0
        core.elapsed_time = core.current_duration + 1
        core.tick()
        self.assertTrue(core.in_long_break)
        self.assertEqual(core.current_duration, core.long_break_duration)

    def test_break_returns_to_work(self):
        core = self.make_core()
        core.is_working = False
        core.is_running = True
        core.start_time = 0
        core.elapsed_time = core.current_duration + 1
        core.tick()
        self.assertTrue(core.is_working)
        self.assertEqual(core.current_duration, core.work_duration)

    def test_record_pomodoro_counts_by_task(self):
        core = self.make_core(work_duration=25)
        core.set_task("写报告")
        core.record_pomodoro()
        count, minutes = core.today_stats()
        self.assertEqual(count, 1)
        self.assertEqual(minutes, 25)
        day = core.stats["daily"][storage.today_key()]
        self.assertEqual(day["tasks"]["写报告"], 1)

    def test_day_rollover_running_keeps_task(self):
        core = self.make_core()
        core.set_task("任务A")
        core.current_day = "2000-01-01"
        core.is_running = True
        self.assertFalse(core.check_day_rollover())
        self.assertEqual(core.task_name, "任务A")

    def test_day_rollover_paused_keeps_task(self):
        core = self.make_core()
        core.set_task("任务A")
        core.current_day = "2000-01-01"
        core.elapsed_time = 30
        self.assertFalse(core.check_day_rollover())
        self.assertEqual(core.task_name, "任务A")

    def test_day_rollover_idle_clears_task(self):
        core = self.make_core()
        core.set_task("任务A")
        core.current_day = "2000-01-01"
        self.assertTrue(core.check_day_rollover())
        self.assertEqual(core.task_name, "")

    def test_apply_settings(self):
        core = self.make_core()
        core.apply_settings(50, 10, 20, 3, True)
        self.assertEqual(core.work_duration, 50 * 60)
        self.assertEqual(core.break_duration, 10 * 60)
        self.assertEqual(core.long_break_duration, 20 * 60)
        self.assertEqual(core.cycles_before_long_break, 3)
        self.assertTrue(core.auto_start)
        self.assertFalse(core.is_running)

    def test_sync_config(self):
        core = self.make_core()
        core.set_task("T")
        core.sync_config()
        self.assertEqual(core.config["task"], "T")
        self.assertEqual(core.config["work_duration"], 25)


if __name__ == "__main__":
    unittest.main()
