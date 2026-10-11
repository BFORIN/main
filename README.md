# 随机抽签器

一款基于 Python + Tkinter 开发的**可视化随机抽签小工具**，界面简洁、逻辑严谨，适用于日常随机抽签、随机点名、随机分配场景。

## ✨ 项目特点

- **等概率不放回抽取**：每个号码出现的概率完全相同，一轮抽完不会重复

- 内置黑名单：自动跳过指定禁用号码

- 可视化剩余数量提示，实时展示抽取状态

- 一键重置数字池，操作简单

- 配置热加载：改完 `config.json` 保存即生效，无需重启

- 内置关于页面，展示开源协议与项目地址

- 原生 GUI 界面，跨平台可用、无广告、纯轻量

## ⚙️ 配置文件

程序目录下会自动生成 `config.json`，可在「帮助 → 编辑配置文件」中直接修改：

| 字段 | 说明 | 默认值 |
| --- | --- | --- |
| `pool_min` | 号码下界 | `1` |
| `pool_max` | 号码上界 | `54` |
| `excluded` | 黑名单，这些号码不会被抽到 | `[37, 39, 50]` |

抽签为**不放回**模式：抽中的号码离开号码池，直到抽完或点击重置。
除黑名单外，没有任何加权或屏蔽逻辑——每个候选号码等概率出现。

## 🛠 运行环境

- Python 3.8+

- 内置 Tkinter（Python 自带，无需额外安装依赖）

## 🚀 使用方法

### 1. 源码运行

```bash
python random_draw.py
```

### 2. 运行测试

```bash
python -m unittest test_draw_core
```

### 3. Windows 打包方式（推荐无报毒方案）

#### 使用 Nuitka 编译为原生 EXE（大幅降低误报）

```bash
pip install nuitka
python -m nuitka --onefile --windows-disable-console random_draw.py
```

#### PyInstaller 普通打包

```bash
pyinstaller -w random_draw.py
```

## 📂 项目结构

```Plain Text
.
├── random_draw.py               # 界面层（Tkinter）
├── draw_core.py                 # 配置解析与抽签核心，不依赖 Tkinter
├── test_draw_core.py            # 抽签核心单元测试
├── README.md                    # 项目说明文档
└── LICENSE                      # 开源协议文件
```

## 📄 开源协议

本项目采用 **GNU General Public License v3.0 (GPL‑3.0)** 开源。
详见仓库根目录下的 LICENSE 文件。

## 📝 更新日志

### v1.1

- 移除放回 / 不放回双模式，统一为单模式不放回抽取
- 移除重抽触发机制（`reroll_triggers` / `max_rerolls`），抽签恢复为完全等概率
- 旧配置文件中的重抽字段会在下次加载时自动清除
- 拆分界面层与抽签核心，消除全局变量
- 新增抽签核心单元测试，含分布均匀性检验

### v1.0

- 实现放回 / 不放回双随机模式

- 完善智能重抽机制

- 添加剩余数量实时显示、一键重置功能

- 新增关于页面、开源协议与项目链接

- 优化界面文字，更贴合用户理解逻辑