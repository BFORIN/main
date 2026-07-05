import tkinter as tk
from tkinter import ttk
import random

# 配置参数
excluded = {39, 50}
reroll_triggers = {46, 47, 49}
remaining_pool = []

def init_pool():
    """初始化新一轮数字池，打乱顺序"""
    global remaining_pool
    remaining_pool = [x for x in range(1, 55) if x not in excluded]
    random.shuffle(remaining_pool)

def generate():
    """不放回抽签，触发重抽时直接输出最终结果，不显示重抽过程"""
    global remaining_pool

    # 池子为空，自动开启新一轮
    if not remaining_pool:
        init_pool()
        result_var.set("本轮已全部抽完，自动重置新一轮\n点击按钮继续抽签")
        return

    first = remaining_pool.pop()

    if first in reroll_triggers:
        # 触发重抽，直接取第二个作为最终结果，不输出重抽过程
        if not remaining_pool:
            # 极端情况：最后一个数字刚好触发重抽
            init_pool()
            result_var.set("本轮已全部抽完，自动重置新一轮\n点击按钮继续抽签")
            return
        second = remaining_pool.pop()
        result_var.set(f"结果: {second}")
    else:
        result_var.set(f"结果: {first}")

# === 主窗口 ===
root = tk.Tk()
root.title("不重复随机抽签器")
root.geometry("360x220")
root.resizable(False, False)

# 样式
style = ttk.Style(root)
try:
    style.theme_use("clam")
except tk.TclError:
    pass

# 结果显示
result_var = tk.StringVar(value="点击下方按钮开始抽签")
result_label = ttk.Label(
    root,
    textvariable=result_var,
    font=("Microsoft YaHei", 16, "bold"),
    justify="center",
)
result_label.pack(expand=True, fill="both", padx=20, pady=20)

# 生成按钮
btn = ttk.Button(root, text="抽签", command=generate)
btn.pack(pady=(0, 30), ipadx=20, ipady=6)

# 启动时初始化第一轮
init_pool()
root.mainloop()
