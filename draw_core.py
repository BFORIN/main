"""随机抽签器的抽签核心：配置解析与随机逻辑。

本模块不依赖 Tkinter，可单独导入和测试。
"""

import json
import os
import random
import sys

DEFAULT_CONFIG = {
    "excluded": [37, 39, 50],
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
    """把任意来源的配置规整为一份合法配置。

    只保留 DEFAULT_CONFIG 里声明的字段，非法字段逐项回落到默认值；
    未声明的字段（如已废弃的 reroll_triggers / max_rerolls）直接丢弃，
    下次保存时便不会再写回配置文件。
    """
    if not isinstance(raw_cfg, dict):
        raw_cfg = {}

    merged = {**DEFAULT_CONFIG, **{k: v for k, v in raw_cfg.items() if k in DEFAULT_CONFIG}}

    merged["excluded"] = _as_int_list(merged.get("excluded"), DEFAULT_CONFIG["excluded"])

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
    """持有剩余数字池，并执行抽签。"""

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
        """重建并打乱数字池。"""
        self.remaining_pool = self.config.candidates()
        random.shuffle(self.remaining_pool)

    def draw(self):
        """从剩余池中等概率抽一个数字并将其移出池，池空时返回 None。"""
        self.reload()
        self.last_error = ""

        if not self.remaining_pool:
            self.last_error = "数字池已抽完，请重置后再继续"
            return None

        idx = random.randrange(len(self.remaining_pool))
        num = self.remaining_pool[idx]
        del self.remaining_pool[idx]
        return num