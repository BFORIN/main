import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
import random
import json
import sys
import os
import webbrowser


def get_config_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, "config.json")


def load_config():
    config_path = get_config_path()
    default_config = {
        "excluded": [39, 50],
        "reroll_triggers": [46, 47, 49]
    }
    if not os.path.exists(config_path):
        save_config(default_config)
        return default_config
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            user_cfg = json.load(f)
        return {**default_config, **user_cfg}
    except Exception:
        return default_config


def save_config(cfg):
    config_path = get_config_path()
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)


def open_config_file():
    cfg_path = get_config_path()
    if not os.path.exists(cfg_path):
        save_config(load_config())
    try:
        if sys.platform.startswith("win"):
            os.startfile(cfg_path)
        elif sys.platform.startswith("linux"):
            import subprocess
            subprocess.run(["xdg-open", cfg_path], check=True)
        elif sys.platform.startswith("darwin"):
            import subprocess
            subprocess.run(["open", cfg_path], check=True)
        tk.messagebox.showinfo("提示", "配置文件已打开，修改保存后重启程序生效")
    except Exception as e:
        tk.messagebox.showerror("错误", f"无法打开配置文件：{str(e)}")


# 加载配置，替换原硬编码常量
_cfg = load_config()
excluded = set(_cfg["excluded"])
reroll_triggers = set(_cfg["reroll_triggers"])

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
        # 候选池：1~54 排除配置内 excluded
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
    about.geometry("420x220")
    about.minsize(360, 200)
    about.resizable(True, False)
    about.transient(root)
    about.grab_set()
    info_font = (default_family, 11)
    link_font = (default_family, 11, "underline")
    ttk.Label(
        about,
        text="本软件遵循 GNU General Public License v3.0 (GPL‑3.0) 开源协议",
        font=info_font,
        justify="center",
        wraplength=340,
    ).pack(pady=(24, 10))
    link_frame = ttk.Frame(about)
    link_frame.pack(pady=2, fill="x", padx=18)
    ttk.Label(link_frame, text="项目地址: ", font=info_font).pack(side="left")
    link_label = ttk.Label(
        link_frame,
        text="https://github.com/BFORIN/main",
        font=link_font,
        foreground="blue",
        cursor="hand2",
        wraplength=250,
        justify="left",
    )
    link_label.pack(side="left", fill="x", expand=True)
    link_label.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/BFORIN/main"))
    ttk.Button(about, text="确定", command=about.destroy).pack(pady=(20, 10))


def show_disclaimer():
    """显示免责声明对话框"""
    disclaimer = tk.Toplevel(root)
    disclaimer.title("免责声明")
    disclaimer.geometry("500x260")
    disclaimer.minsize(420, 220)
    disclaimer.resizable(True, False)
    disclaimer.transient(root)
    disclaimer.grab_set()
    text = (
        "        本软件仅用于随机结果展示，不构成任何投资、决策、或法律依据。使用者应自行承担由本软件产生的全部风险和后果。\n"
        "        开发者不对因使用本软件造成的任何直接或间接损失负责。\n"
        "        最终解释权归开发者所有。"
    )
    ttk.Label(
        disclaimer,
        text=text,
        font=(default_family, 11),
        justify="left",
        wraplength=440,
    ).pack(padx=20, pady=(20, 10), fill="x")
    ttk.Button(disclaimer, text="确定", command=disclaimer.destroy).pack(pady=(0, 15))


def toggle_topmost():
    """切换窗口是否始终显示在最前层，用于覆盖独占全屏窗口"""
    is_topmost = root.attributes("-topmost")
    root.attributes("-topmost", not is_topmost)
    btn_topmost.configure(text="📌 取消置顶" if not is_topmost else "📌 置顶显示")


# === 主窗口 ===
root = tk.Tk()
root.title("随机抽签器 · 双模式")
root.geometry("460x320")
root.minsize(400, 260)
root.resizable(True, True)

# 菜单栏
menubar = tk.Menu(root)
# 帮助菜单
help_menu = tk.Menu(menubar, tearoff=0)
help_menu.add_command(label="编辑配置文件", command=open_config_file)
help_menu.add_command(label="关于", command=show_about)
help_menu.add_command(label="免责声明", command=show_disclaimer)
menubar.add_cascade(label="帮助", menu=help_menu)
root.config(menu=menubar)

# 顶部工具栏：放在“帮助”旁边，不放在下拉菜单中
toolbar = ttk.Frame(root)
toolbar.pack(fill="x", padx=8, pady=(6, 0))
btn_topmost = ttk.Button(toolbar, text="📌 置顶显示", command=toggle_topmost)
btn_topmost.pack(anchor="e")

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
    wraplength=420,
)
result_label.pack(expand=True, fill="both", padx=20, pady=(20, 5))

# 剩余数字显示（仅不放回有效）
remaining_str = tk.StringVar()
remaining_label = ttk.Label(
    root,
    textvariable=remaining_str,
    font=small_font,
    foreground="gray",
    wraplength=360,
    justify="center",
)
remaining_label.pack(pady=(0, 10), padx=20)

# 模式选择框架
mode_frame = ttk.Frame(root)
mode_frame.pack(pady=5)
mode_var = tk.StringVar(value="pseudo")
mode_var.trace_add("write", on_mode_change)
ttk.Radiobutton(
    mode_frame,
    text="不放回（伪随机）",
    variable=mode_var,
    value="pseudo",
    width=16,
).pack(side="left", padx=8)
ttk.Radiobutton(
    mode_frame,
    text="放回（真随机）",
    variable=mode_var,
    value="true_random",
    width=16,
).pack(side="left", padx=8)

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