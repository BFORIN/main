"""随机抽签器 · 双模式随机工具（Tkinter 界面层）。

抽签规则与配置解析全部位于 draw_core.py，本文件只负责界面与交互。
"""

import os
import random
import sys
import webbrowser
import subprocess

import tkinter as tk
import tkinter.font as tkfont
import tkinter.messagebox as messagebox
from tkinter import ttk

from draw_core import DrawEngine, MODE_PSEUDO, MODE_TRUE_RANDOM

APP_TITLE = "随机抽签器 · 双模式"
BG = "#eef2f7"
CARD_BG = "#ffffff"
ACCENT = "#1d4ed8"
TEXT = "#1f2937"
MUTED = "#6b7280"
BORDER = "#dde7f2"


# === 开机自启 ===

def get_autostart_path():
    """开机自启脚本路径；仅 Windows 支持，其他平台返回 None。"""
    if not sys.platform.startswith("win"):
        return None
    startup_dir = os.path.join(
        os.path.expanduser("~"),
        "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs", "Startup",
    )
    os.makedirs(startup_dir, exist_ok=True)
    return os.path.join(startup_dir, "random_draw.bat")


def is_autostart_enabled():
    autostart_path = get_autostart_path()
    return bool(autostart_path and os.path.exists(autostart_path))


def set_autostart(enabled):
    """写入/删除开机自启脚本，返回是否设置成功。"""
    autostart_path = get_autostart_path()
    if not autostart_path:
        return False
    if enabled:
        batch_content = (
            "@echo off\n"
            f'"{sys.executable}" "{os.path.abspath(__file__)}"\n'
        )
        with open(autostart_path, "w", encoding="utf-8") as f:
            f.write(batch_content)
        return True
    if os.path.exists(autostart_path):
        os.remove(autostart_path)
    return True


def open_file_externally(path):
    """用系统默认程序打开文件。"""
    if sys.platform.startswith("win"):
        os.startfile(path)
    elif sys.platform.startswith("linux"):
        subprocess.run(["xdg-open", path], check=True)
    elif sys.platform.startswith("darwin"):
        subprocess.run(["open", path], check=True)


class DrawApp:
    """主窗口与悬浮窗的持有者，集中管理界面状态与交互。"""

    def __init__(self):
        self.engine = DrawEngine()
        self.floating_window = None
        self._animation_id = None

        self.root = tk.Tk()
        self.root.title(APP_TITLE)

        self._build_window()
        self._build_menu()
        self._build_result_panel()
        self._build_controls()

        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_floating)
        self.engine.reset_pool()
        self.update_remaining()

    def run(self):
        self.root.mainloop()

    # ---------- 界面搭建 ----------

    def _build_window(self):
        root = self.root
        root.configure(bg=BG)

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

        self.window_w = window_w

        # 使用系统默认字体，避免跨平台字体缺失
        self.default_family = tkfont.nametofont("TkDefaultFont").actual("family")

        # 关于/免责声明等窗口沿用 clam 主题
        ttk.Style(root).theme_use("clam")

    def _build_menu(self):
        menubar = tk.Menu(self.root, bg=CARD_BG, fg=TEXT)
        help_menu = tk.Menu(menubar, tearoff=0, bg=CARD_BG, fg=TEXT)
        help_menu.add_command(label="编辑配置文件", command=self.open_config_file)
        help_menu.add_command(label="关于", command=self.show_about)
        help_menu.add_command(label="免责声明", command=self.show_disclaimer)
        help_menu.add_separator()
        self.autostart_var = tk.BooleanVar(value=is_autostart_enabled())
        help_menu.add_checkbutton(label="开机自启", variable=self.autostart_var, command=self.toggle_autostart)
        help_menu.add_command(label="恢复主窗口", command=self.restore_main_window)
        menubar.add_cascade(label="帮助", menu=help_menu)
        self.root.config(menu=menubar)

    def _build_result_panel(self):
        panel = tk.Frame(
            self.root,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=18,
            pady=18,
            bd=0,
        )
        panel.pack(fill="both", expand=True, padx=18, pady=(12, 10))

        self.result_var = tk.StringVar(value="点击下方按钮开始抽签")
        tk.Label(
            panel,
            textvariable=self.result_var,
            bg=CARD_BG,
            fg=TEXT,
            font=(self.default_family, 17, "bold"),
            justify="center",
            wraplength=max(260, self.window_w - 100),
            bd=0,
        ).pack(fill="x", pady=(0, 12))

        # 剩余数字显示（仅不放回有效）
        self.remaining_str = tk.StringVar()
        tk.Label(
            panel,
            textvariable=self.remaining_str,
            bg=CARD_BG,
            fg=MUTED,
            font=(self.default_family, 10),
            wraplength=max(260, self.window_w - 120),
            justify="center",
            bd=0,
        ).pack(fill="x")

    def _build_controls(self):
        self.mode_var = tk.StringVar(value=MODE_PSEUDO)
        self.mode_var.trace_add("write", self.on_mode_change)

        mode_frame = tk.Frame(self.root, bg=BG, bd=0)
        mode_frame.pack(pady=(0, 8))
        radio_style = {
            "bg": BG,
            "fg": "#374151",
            "activebackground": BG,
            "activeforeground": "#111827",
            "selectcolor": BG,
            "font": (self.default_family, 10),
        }
        tk.Radiobutton(
            mode_frame, text="不放回（伪随机）", variable=self.mode_var,
            value=MODE_PSEUDO, width=16, **radio_style
        ).pack(side="left", padx=8)
        tk.Radiobutton(
            mode_frame, text="放回（真随机）", variable=self.mode_var,
            value=MODE_TRUE_RANDOM, width=16, **radio_style
        ).pack(side="left", padx=8)

        btn_frame = tk.Frame(self.root, bg=BG, bd=0)
        btn_frame.pack(pady=(0, 18))
        self._make_button(btn_frame, "🎲 抽签", self.generate)
        self._make_button(btn_frame, "🔄 重置", self.reset_pool)

    def _make_button(self, parent, text, command, bg="#edf4ff", active_bg="#dfeeff"):
        """创建一个白板风格的扁平按钮。"""
        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=ACCENT,
            activebackground=active_bg,
            activeforeground=ACCENT,
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
            padx=18,
            pady=8,
            width=15,
            height=2,
            cursor="hand2",
            font=(self.default_family, 10, "bold"),
        )
        button.pack(side="left", padx=10)
        return button

    # ---------- 抽签交互 ----------

    def generate(self):
        """按当前模式抽签并播放滚动动画。"""
        num = self.engine.draw(self.mode_var.get())
        if num is None:
            self.result_var.set(self.engine.last_error)
        else:
            self.animate_result(num)
        self.update_remaining()

    def reset_pool(self):
        """手动重置不放回模式的数字池。"""
        self.engine.reload()
        self.engine.reset_pool()
        self.result_var.set("数字池已重置")
        self.update_remaining()

    def on_mode_change(self, *_args):
        """模式切换时清空提示并重置不放回模式的数字池。"""
        self.engine.reload()
        if self.mode_var.get() == MODE_PSEUDO:
            self.engine.reset_pool()
            self.result_var.set("点击下方按钮开始抽签（不放回）")
        else:
            self.result_var.set("点击下方按钮开始抽签（放回）")
        self.update_remaining()

    def update_remaining(self):
        """更新剩余数字显示（仅不放回模式有效）。"""
        if self.mode_var.get() == MODE_PSEUDO:
            self.remaining_str.set(f"随机池剩余: {len(self.engine.remaining_pool)}")
        else:
            self.remaining_str.set("放回模式不显示剩余数字")

    def animate_result(self, final_num, steps=10, delay_ms=20):
        """让结果在极短时间内快速滚动后停在最终值。

        滚动值取自候选池，与最终结果无关，仅为视觉效果。
        """
        if self._animation_id is not None:
            self.root.after_cancel(self._animation_id)
            self._animation_id = None

        candidates = self.engine.config.candidates() or [final_num]
        seq = [random.choice(candidates) for _ in range(steps)]
        seq.append(final_num)

        def tick(index):
            if index >= len(seq):
                self.result_var.set(f"输出结果: {final_num}")
                self._animation_id = None
                return
            self.result_var.set(f"输出结果: {seq[index]}")
            self._animation_id = self.root.after(delay_ms, tick, index + 1)

        tick(0)

    # ---------- 窗口与菜单 ----------

    def minimize_to_floating(self):
        """最小化到悬浮窗，不退出程序。"""
        if self.floating_window is not None and self.floating_window.winfo_exists():
            self.floating_window.deiconify()
        else:
            self.show_floating_window()
        self.root.withdraw()

    def restore_main_window(self):
        """从悬浮窗恢复主窗口。"""
        if self.floating_window is not None and self.floating_window.winfo_exists():
            self.floating_window.withdraw()
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.focus_force()

    def show_floating_window(self):
        """显示圆形悬浮小窗，支持拖动与双击恢复主窗口，并随分辨率自适应。"""
        if self.floating_window is not None and self.floating_window.winfo_exists():
            self.floating_window.deiconify()
            return

        win = tk.Toplevel(self.root)
        win.title(APP_TITLE)
        self.floating_window = win

        screen_min = min(self.root.winfo_screenwidth(), self.root.winfo_screenheight())
        float_size = max(72, min(110, int(screen_min * 0.072)))
        win.geometry(f"{float_size}x{float_size}")
        win.overrideredirect(True)
        win.attributes("-topmost", True)

        transparent_color = BG
        win.configure(bg=transparent_color)
        if sys.platform.startswith("win"):
            win.attributes("-transparentcolor", transparent_color)

        pos_x = self.root.winfo_x() + self.root.winfo_width() - float_size - 18
        pos_y = self.root.winfo_y() + self.root.winfo_height() - float_size - 18
        win.geometry(f"+{pos_x}+{pos_y}")

        circle = tk.Canvas(
            win,
            width=float_size,
            height=float_size,
            bg=transparent_color,
            highlightthickness=0,
            bd=0,
        )
        circle.pack()
        circle.create_oval(5, 5, float_size - 5, float_size - 5, fill=CARD_BG, outline="#dfe7f0", width=2)
        circle.create_oval(
            int(float_size * 0.24), int(float_size * 0.24),
            int(float_size * 0.76), int(float_size * 0.76),
            fill="#f2f7ff", outline="#dbeaff", width=1,
        )
        circle.create_text(
            float_size / 2, float_size / 2, text="抽",
            fill="#4b5563",
            font=(self.default_family, max(11, int(float_size * 0.18)), "bold"),
        )

        def on_press(event):
            win._drag_start = (event.x_root - win.winfo_x(), event.y_root - win.winfo_y())

        def on_motion(event):
            start = getattr(win, "_drag_start", None)
            if start:
                win.geometry(f"+{event.x_root - start[0]}+{event.y_root - start[1]}")

        def on_release(_event):
            win._drag_start = None

        circle.bind("<ButtonPress-1>", on_press)
        circle.bind("<B1-Motion>", on_motion)
        circle.bind("<ButtonRelease-1>", on_release)
        circle.bind("<Double-Button-1>", lambda _e: self.restore_main_window())
        win.protocol("WM_DELETE_WINDOW", lambda: self.root.destroy())

    def toggle_autostart(self):
        set_autostart(self.autostart_var.get())

    def open_config_file(self):
        """用系统默认程序打开 config.json，供用户直接编辑。"""
        cfg_path = self.engine.store.path
        if not os.path.exists(cfg_path):
            self.engine.store.save(self.engine.config)
        try:
            open_file_externally(cfg_path)
            messagebox.showinfo("提示", "配置文件已打开，修改后会自动热加载，保存即可生效")
        except Exception as e:
            messagebox.showerror("错误", f"无法打开配置文件：{str(e)}")

    def show_about(self):
        """显示关于页面。"""
        about = tk.Toplevel(self.root)
        about.title("关于")
        about.geometry("420x220")
        about.minsize(360, 200)
        about.resizable(True, False)
        about.transient(self.root)
        about.grab_set()

        info_font = (self.default_family, 11)
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
            font=(self.default_family, 11, "underline"),
            foreground="blue",
            cursor="hand2",
            wraplength=250,
            justify="left",
        )
        link_label.pack(side="left", fill="x", expand=True)
        link_label.bind("<Button-1>", lambda _e: webbrowser.open("https://github.com/BFORIN/main"))
        ttk.Button(about, text="确定", command=about.destroy).pack(pady=(20, 10))

    def show_disclaimer(self):
        """显示免责声明对话框。"""
        disclaimer = tk.Toplevel(self.root)
        disclaimer.title("免责声明")
        disclaimer.geometry("500x260")
        disclaimer.minsize(420, 220)
        disclaimer.resizable(True, False)
        disclaimer.transient(self.root)
        disclaimer.grab_set()

        lines = (
            "本软件仅用于随机结果展示，不构成任何投资、决策、或法律依据。使用者应自行承担由本软件产生的全部风险和后果。",
            "开发者不对因使用本软件造成的任何直接或间接损失负责。",
            "最终解释权归开发者所有。",
        )
        text = "\n".join(f"        {line}" for line in lines)
        ttk.Label(
            disclaimer,
            text=text,
            font=(self.default_family, 11),
            justify="left",
            wraplength=440,
        ).pack(padx=20, pady=(20, 10), fill="x")
        ttk.Button(disclaimer, text="确定", command=disclaimer.destroy).pack(pady=(0, 15))


if __name__ == "__main__":
    DrawApp().run()