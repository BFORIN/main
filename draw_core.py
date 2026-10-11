"""随机抽签器的抽签核心：配置解析与随机逻辑。

本模块不依赖 Tkinter，可单独导入和测试。
"""

import json
import os
import random
import sys

MODE_PSEUDO = "pseudo"
MODE_TRUE_RANDOM = "true_random"

DEFAULT_CONFIG = {
    "excluded": [37, 39, 50],
    "reroll_triggers": [46, 47, 49],
    "max_rerolls": 10,
    "pool_min": 1,
    "pool_max": 54,
}


def get_config_path():
    if getattr(sys, "frozen", False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, "config.json")


def _as_int_list(raw, fallback):
    """把配置里的数字列表转成 int 列表，任何非法输入都回落到默认值。"""
    try:
        return [int(x) for x in raw]
    except (TypeError, ValueError):
        return list(fallback)


def normalize_config(raw_cfg):
    """把任意来源的配置规整为一份合法配置，非法字段逐项回落到默认值。"""
    if not isinstance(raw_cfg, dict):
        raw_cfg = {}

    merged = {**DEFAULT_CONFIG, **raw_cfg}

    merged["excluded"] = _as_int_list(merged.get("excluded"), DEFAULT_CONFIG["excluded"])
    merged["reroll_triggers"] = _as_int_list(
        merged.get("reroll_triggers"), DEFAULT_CONFIG["reroll_triggers"]
    )

    try:
        merged["max_rerolls"] = max(0, int(merged.get("max_rerolls")))
    except (TypeError, ValueError):
        merged["max_rerolls"] = DEFAULT_CONFIG["max_rerolls"]

    try:
        pool_min = int(merged.get("pool_min"))
        pool_max = int(merged.get("pool_max"))
        if pool_min > pool_max:
            raise ValueError("pool_min 不能大于 pool_max")
        merged["pool_min"] = pool_min
        merged["pool_max"] = pool_max
    except (TypeError, ValueError):
        merged["pool_min"] = DEFAULT_CONFIG["pool_min"]
        merged["pool_max"] = DEFAULT_CONFIG["pool_max"]

    return merged


class DrawConfig:
    """一份已规整的配置，并按需生成候选数字池。"""

    def __init__(self, data=None):
        data = normalize_config(data)
        self.excluded = set(data["excluded"])
        self.reroll_triggers = set(data["reroll_triggers"])
        self.max_rerolls = data["max_rerolls"]
        self.pool_min = data["pool_min"]
        self.pool_max = data["pool_max"]
        self._data = data

    def candidates(self):
        """候选池：配置区间内、且不在禁用列表里的全部数字。"""
        return [x for x in range(self.pool_min, self.pool_max + 1) if x not in self.excluded]

    def as_dict(self):
        return dict(self._data)


class ConfigStore:
    """负责读写 config.json，并在文件变化时热加载。"""

    def __init__(self, path=None):
        self.path = path or get_config_path()

    def save(self, config):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(config.as_dict(), f, indent=4, ensure_ascii=False)

    def load(self):
        """读取配置；文件缺失时写出默认配置，缺字段或字段非法时自动修正后回写。"""
        if not os.path.exists(self.path):
            config = DrawConfig()
            self.save(config)
            return config

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except (OSError, ValueError):
            raw = {}

        config = DrawConfig(raw)
        original = raw if isinstance(raw, dict) else {}
        if set(DEFAULT_CONFIG) - set(original) or config.as_dict() != original:
            self.save(config)
        return config


class DrawEngine:
    """持有不放回模式的剩余数字池，并执行两种模式的抽签。"""

    def __init__(self, store=None):
        self.store = store or ConfigStore()
        self.config = self.store.load()
        self.remaining_pool = []
        self.last_error = ""

    def reload(self):
        """热加载配置文件，改完保存即可在下一次抽签生效。"""
        self.config = self.store.load()
        return self.config

    def reset_pool(self):
        """重建并打乱不放回模式的数字池。"""
        self.remaining_pool = self.config.candidates()
        random.shuffle(self.remaining_pool)

    def draw(self, mode):
        """按模式抽一个数字，抽不到时返回 None 并把原因写进 last_error。"""
        self.reload()
        self.last_error = ""

        if mode == MODE_PSEUDO:
            num = self._draw_without_replacement()
            if num is None:
                self.last_error = "数字池已抽完，请重置后再继续"
            return num

        num = self._draw_with_replacement()
        if num is None:
            self.last_error = "候选数字为空，请检查配置文件"
        return num

    def _draw_without_replacement(self):
        if not self.remaining_pool:
            return None

        # 命中重抽触发号就放回池中继续抽，直到抽到非触发号或达到重抽上限
        for attempt in range(self.config.max_rerolls + 1):
            idx = random.randrange(len(self.remaining_pool))
            num = self.remaining_pool[idx]
            if num not in self.config.reroll_triggers or attempt == self.config.max_rerolls:
                del self.remaining_pool[idx]
                return num

    def _draw_with_replacement(self):
        pool = self.config.candidates()
        if not pool:
            return None

        # 放回模式：抽到触发号就无限重抽，保证最终结果一定不是触发号
        while True:
            num = random.choice(pool)
            if num not in self.config.reroll_triggers:
                return num