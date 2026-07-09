Quick Side Note 侧键便签

安装方式：
  双击 QuickSideNote_Setup_v1.5.2.exe，根据安装向导完成安装。
  默认安装到当前 Windows 用户目录，不需要管理员权限。
  安装完成后，可以从开始菜单启动 Quick Side Note。

便携运行方式：
  如果拿到的是 QuickSideNote_App 文件夹，也可以直接双击 QuickSideNote.exe 启动。

首次安装配置：
  第一次在新电脑运行时，如果没有检测到 DEEPSEEK_API_KEY，程序会弹出“首次运行设置”窗口。
  请粘贴 DeepSeek API Key，然后点击“保存”。
  保存后，程序会把 API Key 写入当前 Windows 用户环境变量 DEEPSEEK_API_KEY，并立即用于翻译。
  以后如果要更换 API Key，可以在便签窗口中按 Ctrl+K 重新打开配置窗口。

主要操作：
  鼠标侧键 1 单击：进入屏幕文字框选，识别并翻译英文
  鼠标侧键 1 双击：显示或隐藏便签窗口
  如果在设置中选择“即时框选”：单击侧键立即框选，使用托盘或 Ctrl+Alt+N 切换窗口
  框选或翻译中：按 Esc，或再次按鼠标侧键 1，可取消当前任务
  Ctrl+K：打开 API 设置
  Ctrl+,：打开完整设置界面
  Ctrl+S：保存当前便签
  Esc：保存并隐藏便签窗口
  Ctrl+L：清空当前便签页，可在 8 秒内撤销
  Ctrl+Q：退出程序
  Alt + 鼠标左键拖动：移动便签窗口
  右下角通知区域托盘图标：双击显示/隐藏便签；右键菜单可打开设置或退出程序

设置界面：
  点击便签窗口右上角“设置”，或按 Ctrl+, 打开。
  设置界面采用左侧导航：API、输入、开机启动、关于。
  API 页可以配置、测试、显示或清除 DeepSeek API Key。
  输入页可以选择鼠标侧键 1 或侧键 2，调整浏览器键拦截、响应模式和双击判定间隔。
  开机启动页可以开启或关闭 Windows 登录后自动启动。

v1.5.2 UI 与交互更新：
  底部操作栏在默认与最小窗口尺寸下始终可见。
  所有设置页支持滚动，窗口会自动适应当前显示器工作区。
  框选、识别、翻译阶段会显示状态面板；失败可重新框选或返回便签。
  清空当前页后可在 8 秒内撤销。

数据保存位置：
  %USERPROFILE%\Documents\QuickSideNote\note.txt
  %USERPROFILE%\Documents\QuickSideNote\note-2.txt
  %USERPROFILE%\Documents\QuickSideNote\vocabulary.jsonl
  %USERPROFILE%\Documents\QuickSideNote\state.json
  %USERPROFILE%\Documents\QuickSideNote\quick_note.log

说明：
  每个便签页是一个独立的 txt 文件。
  程序默认使用 Windows OCR 在本地识别文字，再用 DeepSeek 翻译。
  本地 OCR 失败时默认不会上传截图；可在 API 设置页明确开启图片兜底。
  卸载程序会清理本应用的开机启动项，但不会主动删除 Documents\QuickSideNote 里的便签和生词数据。

