import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
import random
# 配置参数
excluded = {39, 50}
reroll_triggers = {46, 47, 49}
remaining_pool = []
def init_pool():
    """初始化/重置数字池（仅不放回模式使用）"""
    global remaining_pool
    remaining_pool = [x for x in range(1, 55) if x not in excluded]
    random.shuffle(remaining_pool)
def generate():
    """根据当前模式生成一个随机数"""
    mode = mode_var.get()
    
    if mode == "pseudo":  # 不放回（不重复）
        global remaining_pool
        if not remaining_pool:
            init_pool()
            result_var.set("本轮已全部抽完，以自动重置新一轮")
            update_remaining()
            return
        # 最多重抽10次：触发数字放回池中，直到抽到非触发数或达到上限
        max_rerolls = 10
        for attempt in range(max_rerolls + 1):
            idx = random.randrange(len(remaining_pool))
            num = remaining_pool[idx]
            if num not in reroll_triggers or attempt == max_rerolls:
                del remaining_pool[idx]
                result_var.set(f"输出结果: {num}")
                break
        update_remaining()
    else:  # 放回（每次独立，可重复）
        # 候选池：1~54 排除 39、50
        pool = [x for x in range(1, 55) if x not in excluded]
        # 无限重抽：抽到触发数就继续抽，直到抽到非触发数
        while True:
            num = random.choice(pool)
            if num not in reroll_triggers:
                result_var.set(f"输出结果: {num}")
                break
        # 放回模式不消耗数字，无需更新剩余池
def update_remaining():
    """更新剩余数字显示（仅不放回模式有效）"""
    if mode_var.get() == "pseudo":
        remaining_str.set(f"随机池剩余: {len(remaining_pool)}")
    else:
        remaining_str.set("放回模式不显示剩余数字")
def reset_pool():
    """手动重置数字池（不放回模式）"""
    global remaining_pool
    init_pool()
    result_var.set("数字池已重置")
    update_remaining()
def on_mode_change(*args):
    """模式切换时的处理：清空提示，重置不放回池"""
    if mode_var.get() == "pseudo":
        init_pool()
        result_var.set("点击下方按钮开始抽签（不放回）")
    else:
        result_var.set("点击下方按钮开始抽签（放回）")
    update_remaining()
def show_about():
    """显示关于页面"""
    about = tk.Toplevel(root)
    about.title("关于")
    about.geometry("360x200")
    about.resizable(False, False)
    about.transient(root)
    about.grab_set()
    info_font = (default_family, 11)
    link_font = (default_family, 11, "underline")
    ttk.Label(about, text="本软件遵循GUN自由软件基金会协议", font=info_font, justify="center").pack(pady=(30, 10))
    link_frame = ttk.Frame(about)
    link_frame.pack(pady=2)
    ttk.Label(link_frame, text="项目地址: ", font=info_font).pack(side="left")
    link_label = ttk.Label(link_frame, text="https://github.com/BFORIN/main", font=link_font, foreground="blue", cursor="hand2")
    link_label.pack(side="left")
    link_label.bind("<Button-1>", lambda e: open_link("https://github.com/BFORIN/main"))
    ttk.Button(about, text="确定", command=about.destroy).pack(pady=(20, 10))
def open_link(url):
    """在默认浏览器中打开链接"""
    import webbrowser
    webbrowser.open(url)
# === 主窗口 ===
root = tk.Tk()
root.title("随机抽签器 · 双模式")
root.geometry("420x280")
root.resizable(False, False)
# 菜单栏
menubar = tk.Menu(root)
help_menu = tk.Menu(menubar, tearoff=0)
help_menu.add_command(label="关于", command=show_about)
menubar.add_cascade(label="帮助", menu=help_menu)
root.config(menu=menubar)
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
# 剩余数字显示（仅不放回有效）
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
    mode_frame, text="不放回（伪随机）", variable=mode_var, value="pseudo"
).pack(side="left", padx=10)
ttk.Radiobutton(
    mode_frame, text="放回（真随机）", variable=mode_var, value="true_random"
).pack(side="left", padx=10)
# 操作按钮
btn_frame = ttk.Frame(root)
btn_frame.pack(pady=(10, 20))
btn_draw = ttk.Button(btn_frame, text="🎲 抽签", command=generate)
btn_draw.pack(side="left", padx=10, ipadx=10, ipady=4)
btn_reset = ttk.Button(btn_frame, text="🔄 重置", command=reset_pool)
btn_reset.pack(side="left", padx=10, ipadx=10, ipady=4)
# 初始化不放回池
init_pool()
update_remaining()
root.mainloop()
