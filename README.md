# 番茄钟 · Tomato Clock

[![Release](https://img.shields.io/github/v/release/wsj060618/tomato-clock?style=flat-square&label=release&color=FF6B6B)](https://github.com/wsj060618/tomato-clock/releases)
[![License](https://img.shields.io/github/license/wsj060618/tomato-clock?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078D6?style=flat-square)](https://github.com/wsj060618/tomato-clock/releases)
[![Python](https://img.shields.io/badge/python-3.8%2B-3776AB?style=flat-square)](https://www.python.org/)

> 基于 Python + Tkinter 的轻量番茄钟：倒计时 / 正计时、系统托盘、桌面悬浮球、深浅主题与本地统计。

## 简介

番茄钟是一个面向 Windows 的番茄工作法计时器。程序完全本地运行，不联网、不收集数据；配置与统计保存在用户目录下。界面使用 Tkinter 构建，圆角与图标由 Pillow 自绘，系统托盘由 pystray 提供。

## 特性

**计时**
- 倒计时 / 正计时两种模式，可随时切换
- 自定义工作时长、短休息、长休息时长与长休息间隔
- 自动循环 + 长休息，可选阶段结束后自动开始下一阶段

**界面**
- 无边框圆角卡片与环形进度
- 启动时窗口淡入、进度环扫过（可在设置中关闭）
- 深色 / 浅色主题一键切换
- 桌面悬浮球，最小化后可在任意位置查看剩余时间

**统计**
- 今日完成番茄数与专注时长
- 按天汇总的历史记录，含任务明细，支持单条删除与一键清空
- 任务标签，按任务归类统计，跨天自动重置

**系统集成**
- 系统托盘菜单（需 pystray）
- 阶段结束提示音与浮层通知
- 设置、窗口位置、任务等自动持久化

## 下载

前往 [Releases](https://github.com/wsj060618/tomato-clock/releases/latest) 下载最新版本：

| 类型 | 文件 | 说明 |
| --- | --- | --- |
| 安装版 | `TomatoClock-Setup-v<版本>.exe` | 双击安装，默认安装到 `%LOCALAPPDATA%\Programs\TomatoClock`，创建「番茄钟」开始菜单与桌面快捷方式，可从「应用和功能」卸载 |
| 便携版 | `TomatoClock-Portable-v<版本>.zip` | 解压后运行文件夹内的 `TomatoClock-v<版本>.exe`，无需安装 |

系统要求：Windows 10 / 11（64 位）。

> 程序未进行代码签名，首次运行时 Windows SmartScreen 可能提示“已保护你的电脑”。选择“更多信息 → 仍要运行”即可，之后不再提示。

## 快速开始

### 环境要求
- Python 3.8+
- Tkinter（Python 标准库自带）
- pystray、Pillow（系统托盘与自绘控件；未安装时应用可降级运行）

### 从源码运行

```bash
git clone https://github.com/wsj060618/tomato-clock.git
cd tomato-clock
pip install -r requirements.txt
python main.py
```

### 运行测试

```bash
python -m unittest discover -s tests -v
```

## 使用说明

### 主界面
- **开始 / 暂停**：点击“开始”启动计时，运行中可暂停或继续
- **重置**：将计时器恢复到初始状态
- **任务**：点击顶部任务文字编辑当前任务名称
- **历史记录**：点击统计行（“今日 … ›”）查看按天汇总，含完成数、专注时长与任务明细；每行“✕”删除该天，右上“清空”删除全部
- **模式切换**：点击“倒计时 / 正计时”切换计时模式
- **主题 / 提示音**：点击标题栏的“◐”“♪”切换
- **最小化 / 关闭**：点击“—”收起为悬浮球，点击“×”退出

### 键盘快捷键
| 按键 | 功能 |
| --- | --- |
| `空格` | 开始 / 暂停 |
| `R` | 重置 |
| `S` | 打开设置 |
| `H` | 查看历史记录 |
| `Esc` | 收起为悬浮球 |

### 悬浮球
- 拖动可移动位置，双击恢复主窗口

### 系统托盘
- 右键托盘图标可显示主界面、收起为小球或退出

## 配置

在设置窗口可调整工作时长、休息时长、长休息时长、长休息间隔、自动开始、提示音、系统托盘、启动动画与主题。

配置与统计数据保存在：

```
%USERPROFILE%\.pomodoro_timer\
├── config.json    # 配置
└── stats.json     # 统计
```

## 项目结构

```
tomato-clock/
├── main.py                     # 程序入口
├── 番茄钟.spec                  # PyInstaller 打包配置
├── version_info.txt            # exe 版本信息（由脚本生成）
├── CHANGELOG.md                # 版本历史
├── pomodoro/
│   ├── constants.py            # 常量、默认配置、主题配色
│   ├── theme.py                # 主题、颜色工具与 DPI 缩放
│   ├── storage.py              # 配置 / 统计持久化
│   ├── timer.py                # 计时状态机（纯逻辑，可测试）
│   ├── sound.py                # 提示音
│   ├── tray.py                 # 系统托盘
│   ├── resources.py            # 资源路径（兼容打包）
│   ├── widgets.py              # 自绘控件（Pillow 抗锯齿）
│   └── ui/                     # 界面层
│       ├── app.py              # 主窗口
│       ├── settings_dialog.py  # 设置窗
│       ├── task_dialog.py      # 任务窗
│       ├── history_dialog.py   # 历史记录
│       ├── toast.py            # 浮层通知
│       └── floating_ball.py    # 悬浮球
├── assets/
│   ├── tomato.png              # 托盘图标（与 exe 同源）
│   └── tomato.ico              # exe 图标
├── installer/
│   ├── TomatoClock.iss         # Inno Setup 安装脚本
│   └── ChineseSimplified.isl   # 安装向导中文翻译
├── tools/
│   ├── make_icon.py            # 自绘图标生成脚本
│   ├── make_version_info.py    # 生成 exe 版本信息
│   └── build_release.ps1       # 一键构建（打包 + 便携 zip + 安装包）
└── tests/                      # 单元测试
```

图标为程序自绘；运行 `python tools/make_icon.py` 可重新生成 `assets/tomato.png` / `assets/tomato.ico`，托盘与 exe 使用同一份。

## 开发

### 构建发布

发布产物包括安装包与便携 zip。一键构建：

```bash
pip install -r requirements.txt pyinstaller
winget install JRSoftware.InnoSetup      # 仅首次，用于编译安装包
powershell -ExecutionPolicy Bypass -File tools\build_release.ps1
```

脚本依次执行：读取 `__version__` → 生成版本信息 → PyInstaller 打包（onedir）→ 压缩便携 zip → 编译安装包。产物：

- `dist/TomatoClock-v<版本>/`：免安装文件夹
- `dist/installer/TomatoClock-Setup-v<版本>.exe`：安装包
- `dist/installer/TomatoClock-Portable-v<版本>.zip`：便携版

单独打包：

```bash
python tools/make_version_info.py
pyinstaller 番茄钟.spec
iscc /DAppVersion=<版本> installer/TomatoClock.iss
```

> 打包采用 **onedir（文件夹）**而非单文件：启动时无需解压到临时目录，启动更快。

### 版本管理

- 版本号唯一来源为 `pomodoro/__init__.py` 的 `__version__`
- 发布流程：更新 `__version__` → 运行 `python tools/make_version_info.py` → 更新 `CHANGELOG.md` → 打标签

```bash
git tag v2.3.0
git push origin main --tags
```

## 问题反馈

如遇到问题或有功能建议，欢迎通过 [Issues](https://github.com/wsj060618/tomato-clock/issues) 反馈。

## 许可证

本项目基于 [MIT License](LICENSE) 开源，Copyright (c) 2026 wsj060618。
