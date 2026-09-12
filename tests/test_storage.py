import os
import tempfile
import unittest

from pomodoro import storage


class StorageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pomodoro_test_")
        self._dir = storage.APP_DIR
        self._cfg = storage.CONFIG_PATH
        self._stats = storage.STATS_PATH
        storage.APP_DIR = self.tmp
        storage.CONFIG_PATH = os.path.join(self.tmp, "config.json")
        storage.STATS_PATH = os.path.join(self.tmp, "stats.json")

    def tearDown(self):
        storage.APP_DIR = self._dir
        storage.CONFIG_PATH = self._cfg
        storage.STATS_PATH = self._stats

    def test_load_config_uses_defaults_when_missing(self):
        cfg = storage.load_config()
        self.assertEqual(cfg["work_duration"], 25)
        self.assertEqual(cfg["break_duration"], 5)
        self.assertTrue(cfg["countdown_mode"])

    def test_config_roundtrip_merges_defaults(self):
        storage.save_config({"work_duration": 30})
        cfg = storage.load_config()
        self.assertEqual(cfg["work_duration"], 30)
        self.assertEqual(cfg["break_duration"], 5)

    def test_stats_default(self):
        self.assertEqual(storage.load_stats(), {"daily": {}, "cycle_completed": 0})

    def test_stats_roundtrip(self):
        storage.save_stats({"daily": {"2026-01-01": {"count": 2}}, "cycle_completed": 2})
        self.assertEqual(storage.load_stats()["cycle_completed"], 2)

    def test_today_key_format(self):
        self.assertRegex(storage.today_key(), r"^\d{4}-\d{2}-\d{2}$")


if __name__ == "__main__":
    unittest.main()
