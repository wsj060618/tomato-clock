# 番茄钟

当前版本：**2.1.0**（版本历史见 [CHANGELOG.md](CHANGELOG.md)）

## 简介
本项目是一个基于Python的番茄钟计时器应用，使用Tkinter库构建图形用户界面。番茄钟工作法是一种时间管理方法，将工作时间划分为25分钟的工作时段和5分钟的休息时段。该应用支持倒计时和正计时两种模式，还具备小球悬浮窗功能。

## 功能特性
- **现代化界面**：圆角卡片、环形进度动画、分段式模式切换，支持深色/浅色主题。
- **计时模式切换**：支持倒计时和正计时两种模式。
- **自定义设置**：可以自定义工作时长、休息时长、长休息时长与长休息间隔。
- **自动循环 + 长休息**：每完成设定数量的番茄自动进入长休息；可选择结束后自动开始下一阶段。
- **番茄统计**：界面显示今日完成番茄数与专注时长，数据本地持久化。
- **历史记录**：点统计行或按 `H` 查看按天汇总的完成数与专注时长，含任务明细；可单条删除或一键清空。
- **任务标签**：为当前番茄命名，完成后按任务计入统计。
- **提示音与轻提示**：阶段结束时播放提示音并弹出轻量浮层通知。
- **设置持久化**：工作时长、主题、窗口位置等配置自动保存，重启恢复。
- **键盘快捷键**：空格开始/暂停、R 重置、S 设置、Esc 收起为小球。
- **悬浮窗功能**：支持最小化到小球悬浮窗，方便在桌面任何位置查看时间。
- **系统托盘**：支持最小化到系统托盘（需 pystray）。
- **窗口拖动**：主窗口、设置、任务、历史与悬浮球均支持拖动。

## 安装与运行
### 环境要求
- Python 3.x
- Tkinter（Python标准库，通常无需额外安装）
- pystray、Pillow（用于系统托盘；未安装时其余功能仍可正常使用）

```bash
pip install -r requirements.txt
```

### 项目结构
```
番茄钟/
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
├── tools/
│   └── make_icon.py            # 自绘图标生成脚本
└── tests/                      # 单元测试
```

图标为程序自绘（`python tools/make_icon.py` 可重新生成 `assets/tomato.png` / `assets/tomato.ico`），托盘与 exe 使用同一份。

### 运行步骤(脚本)
1. 确保你已经安装了 Python 3.x。
2. 下载或克隆本项目到本地。
3. 打开命令行终端，导航到项目目录：
```bash
cd D:\coding\番茄钟
```
4. 运行：
```bash
python main.py
```

### 运行测试
```bash
python -m unittest discover -s tests -v
```

### 打包为 exe
```bash
pip install -r requirements.txt pyinstaller
python tools/make_version_info.py   # 依据 __version__ 生成版本信息
pyinstaller 番茄钟.spec
```
生成物在 `dist/番茄钟.exe`，其文件属性中会写入版本号（如 `2.1.0`）。图标与托盘图标同源：
- exe 图标：`assets/tomato.ico`
- 托盘图标：`assets/tomato.png`（打包时通过 `datas` 一并带入）

### 版本管理
- 版本号唯一来源：`pomodoro/__init__.py` 的 `__version__`
- 每次发布：更新 `__version__` → 运行 `python tools/make_version_info.py` → 更新 `CHANGELOG.md` → 打标签
```bash
git tag v2.1.0
git push origin master --tags
```

### 运行步骤(可执行文件)
1. 下载可执行文件
2. 双击运行exe文件
3. 若报错，可能是缺少依赖库，可自行安装依赖库

## 使用方法
### 主界面操作
- **开始/暂停**：点击“开始”按钮启动计时器，运行中可点击“暂停”按钮暂停计时。
- **重置**：点击“重置”按钮将计时器重置为初始状态。
- **设置**：点击“设置”按钮可自定义时间、主题、提示音与系统托盘等选项。
- **任务**：点击顶部任务文字可编辑当前任务名称。
- **历史记录**：点击统计行（“今日 … ›”）查看按天汇总的历史，含每日番茄数、专注时长与任务明细；每行“✕”删除该天，右上“清空”删除全部。
- **计时模式切换**：点击“倒计时/正计时”可在两种模式间切换。
- **主题**：点击标题栏的“◐”在深色/浅色主题间切换。
- **提示音**：点击标题栏的“♪”开关提示音。
- **最小化**：点击“—”按钮可将主窗口最小化到小球悬浮窗。
- **关闭**：点击“×”按钮关闭应用。

### 键盘快捷键
- `空格`：开始 / 暂停
- `R`：重置
- `S`：打开设置
- `H`：查看历史记录
- `Esc`：收起为小球悬浮窗

### 悬浮窗操作
- **拖动**：点击并拖动小球悬浮窗可移动其位置。
- **恢复**：双击小球悬浮窗可恢复主窗口。

## 配置说明
在主界面点击“设置”按钮，可打开设置窗口，自定义工作时长、休息时长、长休息时长、长休息间隔、主题、自动开始、提示音与系统托盘，点击“保存”按钮应用设置。

配置与统计数据保存在用户目录下的 `.pomodoro_timer` 文件夹中（`config.json` 与 `stats.json`）。

## 贡献指南
如果你想为这个项目做出贡献，可以按照以下步骤操作：
1. Fork本项目到你的GitHub账户。
2. 创建一个新的分支：`git checkout -b feature/your-feature-name`。
3. 提交你的更改：`git commit -m "Add some feature"`。
4. 推送分支到你的远程仓库：`git push origin feature/your-feature-name`。
5. 在GitHub上创建一个Pull Request。

