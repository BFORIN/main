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
    """最多重抽一次：第一次抽到触发数就放回重抽，第二次结果直接输出"""
    global remaining_pool

    # 池子空了，重置新一轮
    if not remaining_pool:
        init_pool()
        result_var.set("本轮已全部抽完，自动重置新一轮\n点击按钮继续抽签")
        return

    # 第一次抽取
    idx = random.randrange(len(remaining_pool))
    first = remaining_pool[idx]

    if first not in reroll_triggers:
        # 第一次就是普通数字，直接输出
        del remaining_pool[idx]
        result_var.set(f"结果: {first}")
    else:
        # 第一次是触发数，放回（不删除），重抽一次
        idx2 = random.randrange(len(remaining_pool))
        second = remaining_pool[idx2]
        del remaining_pool[idx2]
        result_var.set(f"结果: {second}")

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
