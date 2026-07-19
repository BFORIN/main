import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
import random

# 配置参数
excluded = {39, 50}
reroll_triggers = {46, 47, 49}
remaining_pool = []

def init_pool():
    """初始化/重置数字池（仅伪随机模式使用）"""
    global remaining_pool
    remaining_pool = [x for x in range(1, 55) if x not in excluded]
    random.shuffle(remaining_pool)

def generate():
    """根据当前模式生成一个随机数"""
    mode = mode_var.get()
    
    if mode == "pseudo":  # 伪随机（不重复）
        global remaining_pool
        if not remaining_pool:
            init_pool()
            result_var.set("本轮已全部抽完，自动重置新一轮\n点击按钮继续抽签")
            update_remaining()
            return

        idx = random.randrange(len(remaining_pool))
        first = remaining_pool[idx]

        if first not in reroll_triggers:
            del remaining_pool[idx]
            result_var.set(f"结果: {first}")
        else:
            # 触发重抽：第一次的数字放回（不删除），重抽一次
            idx2 = random.randrange(len(remaining_pool))
            second = remaining_pool[idx2]
            del remaining_pool[idx2]
            result_var.set(f"结果: {second}")
        update_remaining()

    else:  # 真随机（每次独立，可重复）
        # 候选池：1~54 排除 39、50
        pool = [x for x in range(1, 55) if x not in excluded]
        first = random.choice(pool)
        if first not in reroll_triggers:
            result_var.set(f"结果: {first}")
        else:
            # 重抽一次，仍从完整池抽取
            second = random.choice(pool)
            result_var.set(f"结果: {second}")
        # 真随机模式不消耗数字，无需更新剩余池

def update_remaining():
    """更新剩余数字显示（仅伪随机模式有效）"""
    if mode_var.get() == "pseudo":
        remaining_str.set(f"剩余: {len(remaining_pool)}")
    else:
        remaining_str.set("真随机模式，数字无限")

def reset_pool():
    """手动重置数字池（伪随机模式）"""
    global remaining_pool
    init_pool()
    result_var.set("数字池已手动重置，请继续抽签")
    update_remaining()

def on_mode_change(*args):
    """模式切换时的处理：清空提示，重置伪随机池"""
    if mode_var.get() == "pseudo":
        init_pool()
        result_var.set("点击下方按钮开始抽签（不重复）")
    else:
        result_var.set("点击下方按钮开始抽签（真随机）")
    update_remaining()

# === 主窗口 ===
root = tk.Tk()
root.title("随机抽签器 · 双模式")
root.geometry("420x280")
root.resizable(False, False)

# 使用系统默认字体（避免跨平台字体缺失）
default_family = tkfont.nametofont("TkDefaultFont").actual("family")
big_font = (default_family, 16, "bold")
small_font = (default_family, 10)

# 结果显示区域
result_var = tk.StringVar(value="点击下方按钮开始抽签")
result_label = ttk.Label(
    root,
    textvariable=result_var,
    font=big_font,
    justify="center",
    wraplength=380,
)
result_label.pack(expand=True, fill="both", padx=20, pady=(20, 5))

# 剩余数字显示（仅伪随机有效）
remaining_str = tk.StringVar()
remaining_label = ttk.Label(
    root,
    textvariable=remaining_str,
    font=small_font,
    foreground="gray",
)
remaining_label.pack(pady=(0, 10))

# 模式选择框架
mode_frame = ttk.Frame(root)
mode_frame.pack(pady=5)

mode_var = tk.StringVar(value="pseudo")
mode_var.trace_add("write", on_mode_change)

ttk.Radiobutton(
    mode_frame, text="伪随机（不重复）", variable=mode_var, value="pseudo"
).pack(side="left", padx=10)
ttk.Radiobutton(
    mode_frame, text="真随机（可重复）", variable=mode_var, value="true_random"
).pack(side="left", padx=10)

# 操作按钮
btn_frame = ttk.Frame(root)
btn_frame.pack(pady=(10, 20))

btn_draw = ttk.Button(btn_frame, text="🎲 抽签", command=generate)
btn_draw.pack(side="left", padx=10, ipadx=10, ipady=4)

btn_reset = ttk.Button(btn_frame, text="🔄 重置", command=reset_pool)
btn_reset.pack(side="left", padx=10, ipadx=10, ipady=4)

# 初始化伪随机池
init_pool()
update_remaining()

root.mainloop()