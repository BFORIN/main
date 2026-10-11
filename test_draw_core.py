"""draw_core 的单元测试：python -m unittest test_draw_core"""

import json
import os
import random
import tempfile
import unittest

from draw_core import ConfigStore, DrawConfig, DrawEngine, normalize_config


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
        cfg = normalize_config({"pool_min": None, "excluded": "x"})
        defaults = normalize_config({})
        self.assertEqual(cfg["pool_min"], defaults["pool_min"])
        self.assertEqual(cfg["excluded"], defaults["excluded"])

    def test_inverted_range_falls_back(self):
        cfg = normalize_config({"pool_min": 54, "pool_max": 1})
        defaults = normalize_config({})
        self.assertEqual((cfg["pool_min"], cfg["pool_max"]), (defaults["pool_min"], defaults["pool_max"]))

    def test_numeric_strings_accepted(self):
        cfg = normalize_config({"excluded": ["37", 39], "pool_min": "1", "pool_max": "10"})
        self.assertEqual(cfg["excluded"], [37, 39])
        self.assertEqual((cfg["pool_min"], cfg["pool_max"]), (1, 10))

    def test_deprecated_reroll_keys_are_dropped(self):
        """已废弃的重抽配置不再生效，也不会写回配置文件。"""
        cfg = normalize_config({"reroll_triggers": [46, 47], "max_rerolls": 10})
        self.assertNotIn("reroll_triggers", cfg)
        self.assertNotIn("max_rerolls", cfg)

    def test_unknown_keys_are_dropped(self):
        self.assertEqual(
            set(normalize_config({"excluded": [], "pool_min": 1, "pool_max": 5, "wtf": 1})),
            {"excluded", "pool_min", "pool_max"},
        )


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

    def test_legacy_reroll_keys_removed_from_file(self):
        """旧配置文件里的重抽字段应被清除，避免留下已失效的开关。"""
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "config.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"excluded": [1], "reroll_triggers": [46], "max_rerolls": 10,
                       "pool_min": 1, "pool_max": 54}, f)

        ConfigStore(path).load()
        with open(path, "r", encoding="utf-8") as f:
            written = json.load(f)

        self.assertEqual(set(written), {"excluded", "pool_min", "pool_max"})
        self.assertEqual(written["excluded"], [1])


class TestDrawEngine(unittest.TestCase):
    CFG = {"pool_min": 1, "pool_max": 20, "excluded": [20]}

    def test_consumes_exactly_one_per_draw(self):
        engine = make_engine(**self.CFG)
        engine.reset_pool()
        expected = len(DrawConfig(self.CFG).candidates())
        for _ in range(expected):
            self.assertIsNotNone(engine.draw())
            expected -= 1
            self.assertEqual(len(engine.remaining_pool), expected)

    def test_drains_then_reports(self):
        engine = make_engine(**self.CFG)
        engine.reset_pool()
        for _ in range(len(DrawConfig(self.CFG).candidates())):
            engine.draw()
        self.assertIsNone(engine.draw())
        self.assertIn("抽完", engine.last_error)

    def test_only_returns_candidates(self):
        engine = make_engine(**self.CFG)
        candidates = set(DrawConfig(self.CFG).candidates())
        engine.reset_pool()
        for _ in range(len(candidates)):
            self.assertIn(engine.draw(), candidates)

    def test_full_cycle_yields_every_number_exactly_once(self):
        engine = make_engine(**self.CFG)
        engine.reset_pool()
        drawn = sorted(engine.draw() for _ in range(len(DrawConfig(self.CFG).candidates())))
        self.assertEqual(drawn, sorted(DrawConfig(self.CFG).candidates()))

    def test_distribution_is_uniform(self):
        """没有任何加权或排除机制，各号码出现频次应当接近。"""
        pool_size, rounds = 54, 400
        engine = make_engine(pool_min=1, pool_max=pool_size, excluded=[])
        random.seed(20240101)
        counts = [0] * (pool_size + 1)
        for _ in range(rounds):
            engine.reset_pool()
            for _ in range(pool_size):
                counts[engine.draw()] += 1

        expected = rounds * pool_size / pool_size
        deviations = [abs(counts[i] - expected) for i in range(1, pool_size + 1)]
        # 400 轮 × 54 次 = 21600 次抽样，单号标准差约 20，3σ ≈ 60
        self.assertLess(max(deviations), 60, f"分布偏离均匀：{counts}")

    def test_excluded_numbers_never_drawn(self):
        engine = make_engine(pool_min=1, pool_max=30, excluded=[5, 6, 7])
        engine.reset_pool()
        drawn = {engine.draw() for _ in range(1000) if engine.remaining_pool}
        engine.reset_pool()
        drawn |= {engine.draw() for _ in range(1000)}
        self.assertFalse(drawn & {5, 6, 7})

    def test_empty_pool_reports_instead_of_crashing(self):
        engine = make_engine(pool_min=1, pool_max=5, excluded=[1, 2, 3, 4, 5])
        engine.reset_pool()
        self.assertIsNone(engine.draw())
        self.assertIn("抽完", engine.last_error)

    def test_reload_picks_up_config_changes(self):
        engine = make_engine(**self.CFG)
        engine.reset_pool()
        old_pool = sorted(engine.remaining_pool)
        with open(engine.store.path, "w", encoding="utf-8") as f:
            json.dump({"pool_min": 1, "pool_max": 5, "excluded": []}, f)

        engine.reload()

        # reload 只换配置、不动已在用的池子；下一次 reset_pool 才按新配置重建
        self.assertEqual(sorted(engine.remaining_pool), old_pool)
        engine.reset_pool()
        self.assertEqual(sorted(engine.remaining_pool), [1, 2, 3, 4, 5])


if __name__ == "__main__":
    unittest.main()