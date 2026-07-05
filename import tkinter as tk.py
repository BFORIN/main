import tkinter as tk
from tkinter import ttk
import random


def generate():
    """生成随机数:范围 1~54，排除 39/50，46/47/49 时重抽一次，最终结果直接输出"""
    excluded = {39, 50}
    reroll_triggers = {46, 47, 49}

    # 构建有效数字池（范围 1~54，排除 39 和 50）
    pool = [x for x in range(1, 55) if x not in excluded]

    # 第一次抽取
    first = random.choice(pool)

    if first in reroll_triggers:
        # 触发重抽，第二次结果直接输出（不再判断是否重抽）
        second = random.choice(pool)
        result_var.set(f"第一次: {first}  →  触发重抽\n最终结果: {second}")
    else:
        result_var.set(f"结果: {first}")


# === 主窗口 ===
root = tk.Tk()
root.title("随机数生成器")
root.geometry("360x220")
root.resizable(False, False)

# 样式
style = ttk.Style(root)
try:
    style.theme_use("clam")
except tk.TclError:
    pass

# 结果显示
result_var = tk.StringVar(value="点击下方按钮生成随机数")
result_label = ttk.Label(
    root,
    textvariable=result_var,
    font=("Microsoft YaHei", 16, "bold"),
    justify="center",
)
result_label.pack(expand=True, fill="both", padx=20, pady=20)

# 生成按钮
btn = ttk.Button(root, text="生成随机数", command=generate)
btn.pack(pady=(0, 30), ipadx=20, ipady=6)

root.mainloop()
