"""draw_core 的单元测试：python -m unittest test_draw_core"""

import json
import os
import tempfile
import unittest

from draw_core import (
    MODE_PSEUDO,
    MODE_TRUE_RANDOM,
    ConfigStore,
    DrawConfig,
    DrawEngine,
    normalize_config,
)


def make_engine(**cfg):
    """在临时目录里建一个引擎，配置写入 config.json。"""
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "config.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False)
    return DrawEngine(ConfigStore(path))


class TestNormalizeConfig(unittest.TestCase):
    def test_non_dict_falls_back_to_defaults(self):
        for bad in (None, [], "abc", 42):
            self.assertEqual(normalize_config(bad), normalize_config({}))

    def test_illegal_fields_fall_back_individually(self):
        cfg = normalize_config({"max_rerolls": "abc", "pool_min": None, "excluded": "x"})
        defaults = normalize_config({})
        self.assertEqual(cfg["max_rerolls"], defaults["max_rerolls"])
        self.assertEqual(cfg["pool_min"], defaults["pool_min"])
        self.assertEqual(cfg["excluded"], defaults["excluded"])

    def test_negative_rerolls_clamped_to_zero(self):
        self.assertEqual(normalize_config({"max_rerolls": -5})["max_rerolls"], 0)

    def test_inverted_range_falls_back(self):
        cfg = normalize_config({"pool_min": 54, "pool_max": 1})
        defaults = normalize_config({})
        self.assertEqual((cfg["pool_min"], cfg["pool_max"]), (defaults["pool_min"], defaults["pool_max"]))

    def test_numeric_strings_accepted(self):
        cfg = normalize_config({"excluded": ["37", 39], "pool_min": "1", "pool_max": "10"})
        self.assertEqual(cfg["excluded"], [37, 39])
        self.assertEqual((cfg["pool_min"], cfg["pool_max"]), (1, 10))


class TestDrawConfig(unittest.TestCase):
    def test_candidates_exclude_configured_numbers(self):
        cfg = DrawConfig({"pool_min": 1, "pool_max": 10, "excluded": [3, 7]})
        self.assertEqual(cfg.candidates(), [1, 2, 4, 5, 6, 8, 9, 10])

    def test_empty_candidates_when_everything_excluded(self):
        cfg = DrawConfig({"pool_min": 1, "pool_max": 5, "excluded": [1, 2, 3, 4, 5]})
        self.assertEqual(cfg.candidates(), [])


class TestConfigStore(unittest.TestCase):
    def test_creates_default_file_when_missing(self):
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "config.json")
        store = ConfigStore(path)
        self.assertFalse(os.path.exists(path))
        config = store.load()
        self.assertTrue(os.path.exists(path))
        self.assertEqual(config.as_dict(), DrawConfig().as_dict())

    def test_repairs_incomplete_file(self):
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "config.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"pool_min": 3}, f)

        config = ConfigStore(path).load()
        with open(path, "r", encoding="utf-8") as f:
            written = json.load(f)

        self.assertEqual(set(written), set(config.as_dict()))
        self.assertEqual(written["pool_min"], 3)
        self.assertEqual(written["pool_max"], DrawConfig().pool_max)

    def test_corrupted_file_falls_back_to_defaults(self):
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "config.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write("{ not json")
        self.assertEqual(ConfigStore(path).load().as_dict(), DrawConfig().as_dict())


class TestDrawEngine(unittest.TestCase):
    CFG = {"pool_min": 1, "pool_max": 20, "excluded": [20], "reroll_triggers": [7, 8, 9]}

    def test_pseudo_mode_consumes_exactly_one_per_draw(self):
        engine = make_engine(**self.CFG)
        engine.reset_pool()
        expected = len(DrawConfig(self.CFG).candidates())
        for _ in range(expected):
            self.assertIsNotNone(engine.draw(MODE_PSEUDO))
            expected -= 1
            self.assertEqual(len(engine.remaining_pool), expected)

    def test_pseudo_mode_drains_then_reports(self):
        engine = make_engine(**self.CFG)
        engine.reset_pool()
        for _ in range(len(DrawConfig(self.CFG).candidates())):
            engine.draw(MODE_PSEUDO)
        self.assertIsNone(engine.draw(MODE_PSEUDO))
        self.assertIn("抽完", engine.last_error)

    def test_pseudo_mode_only_returns_candidates(self):
        engine = make_engine(**self.CFG)
        candidates = set(DrawConfig(self.CFG).candidates())
        engine.reset_pool()
        for _ in range(len(candidates)):
            self.assertIn(engine.draw(MODE_PSEUDO), candidates)

    def test_true_mode_never_returns_trigger(self):
        engine = make_engine(**self.CFG)
        triggers = set(DrawConfig(self.CFG).reroll_triggers)
        for _ in range(300):
            self.assertNotIn(engine.draw(MODE_TRUE_RANDOM), triggers)

    def test_true_mode_does_not_consume_pool(self):
        engine = make_engine(**self.CFG)
        engine.reset_pool()
        size = len(engine.remaining_pool)
        for _ in range(50):
            engine.draw(MODE_TRUE_RANDOM)
        self.assertEqual(len(engine.remaining_pool), size)

    def test_zero_rerolls_lets_triggers_through(self):
        cfg = {**self.CFG, "max_rerolls": 0}
        engine = make_engine(**cfg)
        triggers = set(DrawConfig(cfg).reroll_triggers)
        engine.reset_pool()
        drawn = [engine.draw(MODE_PSEUDO) for _ in range(300)]
        self.assertTrue(set(drawn) & triggers, "max_rerolls=0 时触发号应当能被抽到")

    def test_empty_pool_reports_instead_of_crashing(self):
        engine = make_engine(pool_min=1, pool_max=5, excluded=[1, 2, 3, 4, 5])
        engine.reset_pool()
        self.assertIsNone(engine.draw(MODE_TRUE_RANDOM))
        self.assertIn("候选数字为空", engine.last_error)

    def test_reload_picks_up_config_changes(self):
        engine = make_engine(**self.CFG)
        engine.reset_pool()
        old_pool = sorted(engine.remaining_pool)
        with open(engine.store.path, "w", encoding="utf-8") as f:
            json.dump({"pool_min": 1, "pool_max": 5, "excluded": [], "reroll_triggers": [], "max_rerolls": 10}, f)

        engine.reload()

        # reload 只换配置、不动已在用的池子；下一次 reset_pool 才按新配置重建
        self.assertEqual(sorted(engine.remaining_pool), old_pool)
        engine.reset_pool()
        self.assertEqual(sorted(engine.remaining_pool), [1, 2, 3, 4, 5])


if __name__ == "__main__":
    unittest.main()