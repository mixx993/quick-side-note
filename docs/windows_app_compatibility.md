# Quick Side Note Windows 应用兼容性检查

检查日期：2026-07-03

## 目标形态

Quick Side Note 需要从“解压后运行 exe”升级为常见 Windows 桌面软件形态：

- 用户双击 `QuickSideNote_Setup_v1.4.1.exe` 安装。
- 默认安装到当前用户目录，不要求管理员权限。
- 安装后创建开始菜单快捷方式，可选创建桌面快捷方式。
- 安装向导使用简体中文界面。
- 安装完成后可直接启动应用。
- 第一次运行应用时引导配置 DeepSeek API Key。
- 应用内设置界面可管理 API、开机启动、侧键选择和双击间隔。
- 程序启动后在 Windows 通知区域显示托盘图标，可从右键菜单显示/隐藏、打开设置或退出。
- 卸载入口出现在开始菜单和 Windows“已安装的应用”列表中。

## 当前兼容性结论

| 项目 | 结论 | 说明 |
| --- | --- | --- |
| Windows 10/11 | 可用 | 程序使用 Windows 全局鼠标钩子和 Windows OCR，目标平台应限定为 Windows。 |
| 64 位系统 | 可用 | 当前 PyInstaller 产物来自 64 位 Python，安装器已限制为 x64 compatible。 |
| 无 Python 环境的新电脑 | 可用 | PyInstaller one-file exe 已包含 Python 运行时和 Python 依赖。 |
| 无 Codex CLI 的新电脑 | 基本可用 | 主路径已经改为 Windows OCR + DeepSeek 文本翻译；Codex CLI 只作为 OCR 失败时的兜底。 |
| 无 DeepSeek API Key 的新电脑 | 可用 | 首次运行会弹出配置窗口，并写入当前 Windows 用户环境变量 `DEEPSEEK_API_KEY`。 |
| 无管理员权限 | 可安装 | Inno Setup 脚本使用 `PrivilegesRequired=lowest`，默认安装到 `%LOCALAPPDATA%`。 |
| 便签数据迁移 | 可用 | 每个便签页是独立 txt，数据在 `%USERPROFILE%\Documents\QuickSideNote`。 |

## 主要外部依赖

1. DeepSeek API Key  
   翻译依赖 `https://api.deepseek.com/chat/completions`。首次安装流程不应该在安装器里收集密钥，而是在应用首次运行时配置，便于后续用 `Ctrl+K` 修改。

2. Windows OCR 英文识别能力  
   程序优先使用 Windows OCR 识别英文。大多数 Windows 10/11 环境可用；如果系统缺少英文 OCR 语言能力，识别会失败。后续可以在应用内把错误提示优化为“请安装英语语言包/OCR 能力”。

3. 鼠标侧键  
   核心交互依赖鼠标侧键 1，也就是 Windows `XBUTTON1`。没有侧键的鼠标仍可打开便签窗口，但取词体验不完整。

4. 网络访问  
   DeepSeek 翻译需要联网。公司网络、代理或防火墙可能导致翻译失败。

## 安装器设计

已新增 Inno Setup 脚本：

```text
installer\QuickSideNote.iss
```

安装器中文语言文件随项目保存：

```text
installer\ChineseSimplified.isl
```

默认安装目录：

```text
%LOCALAPPDATA%\Programs\QuickSideNote
```

安装内容：

- `QuickSideNote.exe`
- `README_RUN.txt`
- `QuickSideNote_intro.html`
- `quick_note_ui_preview.png`

快捷方式：

- 开始菜单：Quick Side Note
- 开始菜单：使用说明
- 开始菜单：软件介绍
- 开始菜单：卸载 Quick Side Note
- 桌面快捷方式：可选

卸载策略：

- 卸载程序文件和安装目录内临时目录。
- 不主动删除 `%USERPROFILE%\Documents\QuickSideNote`，避免误删用户便签和生词本。

## 构建方式

已新增构建脚本：

```cmd
.\scripts\build_installer.cmd
```

如果只想用当前 release 目录里的 exe 生成安装器：

```cmd
.\scripts\build_installer.cmd -SkipAppBuild
```

如果代码有更新，需要先重新打包 exe 并生成安装器：

```cmd
.\scripts\build_installer.cmd
```

输出文件：

```text
release\QuickSideNote_Setup_v1.4.1.exe
```

## 建议的首次配置流程

1. 用户双击安装器。
2. 选择安装位置，决定是否创建桌面快捷方式。
3. 安装完成页勾选“启动 Quick Side Note 并进行首次配置”。
4. 应用启动后检测 `DEEPSEEK_API_KEY`。
5. 如果不存在，显示“首次运行设置”窗口。
6. 用户粘贴 DeepSeek API Key，点击保存。
7. 应用把密钥写入当前 Windows 用户环境变量并立即可用。

## 后续建议

- 增加代码签名，降低 Windows SmartScreen 和杀毒软件误报概率。
- 增加 OCR 不可用时的明确中文修复提示。
- 增加设置页，显示 API 状态、数据目录、日志入口和版本号。
- 增加可选开机启动任务，适合长期作为后台工具使用。
- 如果要支持 ARM64 原生运行，需要单独在 ARM64 Python 环境下打包。

