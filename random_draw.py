import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
import tkinter.messagebox as messagebox
import random
import json
import sys
import os
import webbrowser

DEFAULT_CONFIG = {
    "excluded": [37,39, 50],
    "reroll_triggers": [46, 47, 49],
    "max_rerolls": 10,
    "pool_min": 1,
    "pool_max": 54,
}


def get_config_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, "config.json")


def normalize_config(raw_cfg):
    if not isinstance(raw_cfg, dict):
        raw_cfg = {}

    merged = {**DEFAULT_CONFIG, **raw_cfg}

    try:
        merged["excluded"] = [int(x) for x in merged.get("excluded", DEFAULT_CONFIG["excluded"])]
    except Exception:
        merged["excluded"] = DEFAULT_CONFIG["excluded"]

    try:
        merged["reroll_triggers"] = [int(x) for x in merged.get("reroll_triggers", DEFAULT_CONFIG["reroll_triggers"])]
    except Exception:
        merged["reroll_triggers"] = DEFAULT_CONFIG["reroll_triggers"]

    try:
        merged["max_rerolls"] = max(0, int(merged.get("max_rerolls", DEFAULT_CONFIG["max_rerolls"])))
    except Exception:
        merged["max_rerolls"] = DEFAULT_CONFIG["max_rerolls"]

    try:
        pool_min = int(merged.get("pool_min", DEFAULT_CONFIG["pool_min"]))
        pool_max = int(merged.get("pool_max", DEFAULT_CONFIG["pool_max"]))
        if pool_min > pool_max:
            pool_min, pool_max = DEFAULT_CONFIG["pool_min"], DEFAULT_CONFIG["pool_max"]
        merged["pool_min"] = pool_min
        merged["pool_max"] = pool_max
    except Exception:
        merged["pool_min"] = DEFAULT_CONFIG["pool_min"]
        merged["pool_max"] = DEFAULT_CONFIG["pool_max"]

    return merged


def ensure_config_file():
    config_path = get_config_path()
    if not os.path.exists(config_path):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            user_cfg = json.load(f)
    except Exception:
        user_cfg = {}

    normalized = normalize_config(user_cfg)
    existing_keys = set(user_cfg.keys()) if isinstance(user_cfg, dict) else set()
    missing_keys = [key for key in DEFAULT_CONFIG if key not in existing_keys]
    if missing_keys or normalized != user_cfg:
        save_config(normalized)
    return normalized


def load_config():
    return ensure_config_file()


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
        messagebox.showinfo("提示", "配置文件已打开，修改后会自动热加载，保存即可生效")
    except Exception as e:
        messagebox.showerror("错误", f"无法打开配置文件：{str(e)}")


def reload_config():
    """从配置文件热加载禁用数字、重抽触发数字、重抽次数和随机池范围"""
    global _cfg, excluded, reroll_triggers, max_rerolls, pool_min, pool_max
    _cfg = load_config()
    excluded = set(_cfg["excluded"])
    reroll_triggers = set(_cfg["reroll_triggers"])
    max_rerolls = int(_cfg.get("max_rerolls", 10))

    pool_min = int(_cfg.get("pool_min", DEFAULT_CONFIG["pool_min"]))
    pool_max = int(_cfg.get("pool_max", DEFAULT_CONFIG["pool_max"]))
    if pool_min > pool_max:
        pool_min, pool_max = DEFAULT_CONFIG["pool_min"], DEFAULT_CONFIG["pool_max"]


def get_autostart_path():
    if not sys.platform.startswith("win"):
        return None
    startup_dir = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
    os.makedirs(startup_dir, exist_ok=True)
    return os.path.join(startup_dir, "random_draw.bat")


def is_autostart_enabled():
    if not sys.platform.startswith("win"):
        return False
    autostart_path = get_autostart_path()
    return bool(autostart_path and os.path.exists(autostart_path))


def set_autostart(enabled):
    if not sys.platform.startswith("win"):
        return False
    autostart_path = get_autostart_path()
    if not autostart_path:
        return False
    if enabled:
        script_path = os.path.abspath(__file__)
        python_exe = sys.executable
        batch_content = (
            "@echo off\n"
            f'"{python_exe}" "{script_path}"\n'
        )
        with open(autostart_path, "w", encoding="utf-8") as f:
            f.write(batch_content)
        return True
    if os.path.exists(autostart_path):
        os.remove(autostart_path)
    return True


# 加载配置，替换原硬编码常量
reload_config()
remaining_pool = []


def init_pool():
    """初始化/重置数字池（仅不放回模式使用），并按配置范围计算"""
    reload_config()
    global remaining_pool
    remaining_pool = [x for x in range(pool_min, pool_max + 1) if x not in excluded]
    random.shuffle(remaining_pool)


def animate_result(final_num, steps=10, delay_ms=20):
    """让结果在极短时间内快速滚动后停在最终值"""
    if getattr(root, "_draw_animation", None):
        root.after_cancel(root._draw_animation)
        root._draw_animation = None

    seq = [random.randint(1, 54) for _ in range(steps)]
    seq.append(final_num)

    def tick(index):
        if index >= len(seq):
            result_var.set(f"输出结果: {final_num}")
            root._draw_animation = None
            return
        result_var.set(f"输出结果: {seq[index]}")
        root._draw_animation = root.after(delay_ms, tick, index + 1)

    tick(0)


def generate():
    """根据当前模式生成一个随机数"""
    reload_config()
    mode = mode_var.get()

    if mode == "pseudo":  # 不放回（不重复）
        global remaining_pool
        if not remaining_pool:
            result_var.set("数字池已抽完，请重置后再继续")
            update_remaining()
            return
        # 热加载配置中的重抽次数：触发数字放回池中，直到抽到非触发数或达到上限
        for attempt in range(max_rerolls + 1):
            idx = random.randrange(len(remaining_pool))
            num = remaining_pool[idx]
            if num not in reroll_triggers or attempt == max_rerolls:
                del remaining_pool[idx]
                animate_result(num)
                break
        update_remaining()
    else:  # 放回（每次独立，可重复）
        # 候选池：按配置区间计算，排除配置内 excluded
        pool = [x for x in range(pool_min, pool_max + 1) if x not in excluded]
        # 无限重抽：抽到触发数就继续抽，直到抽到非触发数
        while True:
            num = random.choice(pool)
            if num not in reroll_triggers:
                animate_result(num)
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
    reload_config()
    global remaining_pool
    init_pool()
    result_var.set("数字池已重置")
    update_remaining()


def on_mode_change(*args):
    """模式切换时的处理：清空提示，重置不放回池"""
    reload_config()
    if mode_var.get() == "pseudo":
        init_pool()
        result_var.set("点击下方按钮开始抽签（不放回）")
    else:
        result_var.set("点击下方按钮开始抽签（放回）")
    update_remaining()


def minimize_to_floating():
    """最小化到悬浮窗，不退出程序"""
    if floating_window is not None and floating_window.winfo_exists():
        floating_window.deiconify()
    else:
        show_floating_window()
    root.withdraw()


def restore_main_window():
    """从悬浮窗恢复主窗口"""
    if floating_window is not None and floating_window.winfo_exists():
        floating_window.withdraw()
    root.deiconify()
    root.lift()
    root.attributes("-topmost", True)
    root.focus_force()


def start_drag(event):
    """记录悬浮窗拖拽起点"""
    if floating_window is None or not floating_window.winfo_exists():
        return
    floating_window._drag_start_x = event.x_root - floating_window.winfo_x()
    floating_window._drag_start_y = event.y_root - floating_window.winfo_y()


def drag_window(event):
    """拖拽悬浮窗"""
    if floating_window is None or not floating_window.winfo_exists():
        return
    new_x = event.x_root - floating_window._drag_start_x
    new_y = event.y_root - floating_window._drag_start_y
    floating_window.geometry(f"+{new_x}+{new_y}")


def show_floating_window():
    """显示一个圆形悬浮小窗，支持拖动和双击恢复主窗口，并随分辨率自适应"""
    global floating_window
    if floating_window is not None and floating_window.winfo_exists():
        floating_window.deiconify()
        return

    floating_window = tk.Toplevel(root)
    floating_window.title("随机抽签器")

    screen_min = min(root.winfo_screenwidth(), root.winfo_screenheight())
    float_size = max(72, min(110, int(screen_min * 0.072)))
    floating_window.geometry(f"{float_size}x{float_size}")
    floating_window.overrideredirect(True)
    floating_window.attributes("-topmost", True)

    transparent_color = "#eef2f7"
    floating_window.configure(bg=transparent_color)
    if sys.platform.startswith("win"):
        floating_window.attributes("-transparentcolor", transparent_color)

    pos_x = root.winfo_x() + root.winfo_width() - float_size - 18
    pos_y = root.winfo_y() + root.winfo_height() - float_size - 18
    floating_window.geometry(f"+{pos_x}+{pos_y}")

    circle = tk.Canvas(
        floating_window,
        width=float_size,
        height=float_size,
        bg=transparent_color,
        highlightthickness=0,
        bd=0,
    )
    circle.pack()
    circle.create_oval(5, 5, float_size - 5, float_size - 5, fill="#ffffff", outline="#dfe7f0", width=2)
    circle.create_oval(int(float_size * 0.24), int(float_size * 0.24), int(float_size * 0.76), int(float_size * 0.76), fill="#f2f7ff", outline="#dbeaff", width=1)
    circle.create_text(
        float_size / 2,
        float_size / 2,
        text="抽",
        fill="#4b5563",
        font=(default_family, max(11, int(float_size * 0.18)), "bold"),
    )

    def on_drag_press(event):
        start_drag(event)
        floating_window._dragging = True

    def on_drag_motion(event):
        if getattr(floating_window, "_dragging", False):
            drag_window(event)

    def on_drag_release(event):
        floating_window._dragging = False

    circle.bind("<ButtonPress-1>", on_drag_press)
    circle.bind("<B1-Motion>", on_drag_motion)
    circle.bind("<ButtonRelease-1>", on_drag_release)
    circle.bind("<Double-Button-1>", lambda e: restore_main_window())
    floating_window.protocol("WM_DELETE_WINDOW", lambda: root.destroy())


def toggle_autostart():
    set_autostart(autostart_var.get())


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


def create_round_button(parent, text, command, width=130, height=38, bg="#edf4ff", fg="#1d4ed8", active_bg="#dfeeff"):
    """创建一个稳定可用的白板风格按钮，保留清晰点击功能"""
    button = tk.Button(
        parent,
        text=text,
        command=command,
        width=width // 8,
        height=2,
        bg=bg,
        fg=fg,
        activebackground=active_bg,
        activeforeground=fg,
        borderwidth=0,
        highlightthickness=0,
        relief="flat",
        padx=18,
        pady=8,
        cursor="hand2",
        font=(default_family, 10, "bold"),
    )
    button.pack(side="left", padx=10)
    return button


# === 主窗口 ===
root = tk.Tk()
root.title("随机抽签器 · 双模式")
root.configure(bg="#eef2f7")

screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()
window_w = min(max(420, int(screen_w * 0.32)), 560)
window_h = min(max(300, int(screen_h * 0.42)), 420)
root.geometry(f"{window_w}x{window_h}")
root.minsize(int(window_w * 0.8), int(window_h * 0.7))
root.resizable(True, True)
root.attributes("-topmost", True)
root.update_idletasks()
root.attributes("-alpha", 0.98)

# 菜单栏
menubar = tk.Menu(root, bg="#ffffff", fg="#1f2937")
help_menu = tk.Menu(menubar, tearoff=0, bg="#ffffff", fg="#1f2937")
help_menu.add_command(label="编辑配置文件", command=open_config_file)
help_menu.add_command(label="关于", command=show_about)
help_menu.add_command(label="免责声明", command=show_disclaimer)
help_menu.add_separator()
autostart_var = tk.BooleanVar(value=is_autostart_enabled())
help_menu.add_checkbutton(label="开机自启", variable=autostart_var, command=toggle_autostart)
help_menu.add_command(label="恢复主窗口", command=restore_main_window)
menubar.add_cascade(label="帮助", menu=help_menu)
root.config(menu=menubar)

floating_window = None
root.protocol("WM_DELETE_WINDOW", minimize_to_floating)

# 使用系统默认字体（避免跨平台字体缺失）
default_family = tkfont.nametofont("TkDefaultFont").actual("family")
big_font = (default_family, 17, "bold")
small_font = (default_family, 10)

style = ttk.Style(root)
style.theme_use("clam")
style.configure("WhiteBoard.TFrame", background="#ffffff")
style.configure("WhiteBoard.TLabel", background="#ffffff", foreground="#374151")
style.configure("WhiteBoard.TRadiobutton", background="#eef2f7", foreground="#374151", focuscolor="#eef2f7")
style.map("WhiteBoard.TRadiobutton", background=[("active", "#eef2f7")])

panel = tk.Frame(
    root,
    bg="#ffffff",
    highlightbackground="#dde7f2",
    highlightthickness=1,
    padx=18,
    pady=18,
)
panel.pack(fill="both", expand=True, padx=18, pady=(12, 10))

root.update_idletasks()
root.overrideredirect(False)

for widget in [root, panel]:
    widget.configure(bd=0)

root.bind("<Configure>", lambda event: None)

# 结果显示区域
result_var = tk.StringVar(value="点击下方按钮开始抽签")
result_label = tk.Label(
    panel,
    textvariable=result_var,
    bg="#ffffff",
    fg="#1f2937",
    font=big_font,
    justify="center",
    wraplength=max(260, window_w - 100),
)
result_label.pack(fill="x", pady=(0, 12))

# 剩余数字显示（仅不放回有效）
remaining_str = tk.StringVar()
remaining_label = tk.Label(
    panel,
    textvariable=remaining_str,
    bg="#ffffff",
    fg="#6b7280",
    font=small_font,
    wraplength=max(260, window_w - 120),
    justify="center",
)
remaining_label.pack(fill="x")

# 模式选择框架
mode_frame = tk.Frame(root, bg="#eef2f7")
mode_frame.pack(pady=(0, 8))
mode_var = tk.StringVar(value="pseudo")
mode_var.trace_add("write", on_mode_change)

radio_style = {"bg": "#eef2f7", "fg": "#374151", "activebackground": "#eef2f7", "activeforeground": "#111827", "selectcolor": "#eef2f7", "font": (default_family, 10)}
tk.Radiobutton(mode_frame, text="不放回（伪随机）", variable=mode_var, value="pseudo", width=16, **radio_style).pack(side="left", padx=8)
tk.Radiobutton(mode_frame, text="放回（真随机）", variable=mode_var, value="true_random", width=16, **radio_style).pack(side="left", padx=8)

# 操作按钮
btn_frame = tk.Frame(root, bg="#eef2f7")
btn_frame.pack(pady=(0, 18))
btn_draw = create_round_button(btn_frame, "🎲 抽签", generate, width=120)
btn_reset = create_round_button(btn_frame, "🔄 重置", reset_pool, width=120)

# 初始化不放回池
init_pool()
update_remaining()

if __name__ == "__main__":
    root.mainloop()