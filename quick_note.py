import asyncio
import ctypes
import html
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import tempfile
import urllib.error
import urllib.request
from ctypes import wintypes
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, simpledialog, font as tkfont
from PIL import Image, ImageGrab, ImageOps


APP_NAME = "Quick Side Note"
APP_VERSION = "1.6.0"
NOTE_DIR = Path.home() / "Documents" / "QuickSideNote"
NOTE_FILE = NOTE_DIR / "note.txt"
DEFAULT_NOTE_PAGES = (
    {"id": 1, "name": "1"},
    {"id": 2, "name": "2"},
    {"id": 3, "name": "3"},
)
VOCABULARY_FILE = NOTE_DIR / "vocabulary.jsonl"
STATE_FILE = NOTE_DIR / "state.json"
LOG_FILE = NOTE_DIR / "quick_note.log"
TMP_DIR = NOTE_DIR / "tmp"
STUDIO_DIR = NOTE_DIR / "studio"
ICON_FILE = Path(__file__).with_name("assets") / "quick_note_icon.ico"
SETTINGS_STATE_KEY = "settings"
XBUTTON1 = 0x0001
XBUTTON2 = 0x0002
BUTTON_TO_USE = XBUTTON1
BLOCKED_BROWSER_KEYS = {0xA6}
STARTUP_RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
STARTUP_RUN_VALUE_NAME = "QuickSideNote"
WM_XBUTTONDOWN = 0x020B
WM_XBUTTONUP = 0x020C
WH_MOUSE_LL = 14
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104
WM_KEYUP = 0x0101
WM_SYSKEYUP = 0x0105
WM_CLOSE = 0x0010
WM_DESTROY = 0x0002
WM_QUIT = 0x0012
ERROR_ALREADY_EXISTS = 183
VK_BROWSER_BACK = 0xA6
VK_BROWSER_FORWARD = 0xA7
VK_ESCAPE = 0x1B
SW_SHOWNORMAL = 1
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
HWND_BROADCAST = 0xFFFF
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_SHOWWINDOW = 0x0040
WM_SETTINGCHANGE = 0x001A
SMTO_ABORTIFHUNG = 0x0002
WM_APP = 0x8000
WM_LBUTTONDBLCLK = 0x0203
WM_RBUTTONUP = 0x0205
WM_CONTEXTMENU = 0x007B
WM_TRAYICON = WM_APP + 21
IMAGE_ICON = 1
LR_LOADFROMFILE = 0x0010
LR_DEFAULTSIZE = 0x0040
NIM_ADD = 0x00000000
NIM_DELETE = 0x00000002
NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004
TRAY_ICON_ID = 1
SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79
POPUP_OFFSET = 10
WINDOW_WIDTH = 440
WINDOW_HEIGHT = 340
MIN_WINDOW_WIDTH = 380
MIN_WINDOW_HEIGHT = 300
DEFAULT_WINDOW_X = 760
DEFAULT_WINDOW_Y = 260
MAX_PAGE_NAME_CHARS = 12
PAGE_RAIL_MIN_WIDTH = 64
PAGE_RAIL_MAX_WIDTH = 140
PAGE_LABEL_PADDING_X = 10
PAGE_LABEL_FONT = ("Microsoft YaHei UI", 9)
PAGE_ADD_FONT = ("Microsoft YaHei UI", 11)
RESIZE_GRIP_SIZE = 18
PLACEHOLDER_TEXT = "随手记点什么..."
UI_BORDER = "#cfd8e6"
UI_SHELL_BG = "#eef3f8"
UI_HEADER_BG = "#ffffff"
UI_HEADER_TEXT = "#182230"
UI_PAPER_BG = "#ffffff"
UI_PAPER_BORDER = "#dfe7f1"
UI_TEXT = "#182230"
UI_MUTED_TEXT = "#667085"
UI_SELECTION_BG = "#dbeafe"
UI_SELECTION_FG = "#10223a"
UI_INSERT = "#2563eb"
UI_RESIZE_GRIP = "#9aa8b8"
UI_ACCENT = "#2563eb"
UI_ACCENT_SOFT = "#e8f1ff"
UI_ACCENT_SOFTER = "#f3f7ff"
UI_ACCENT_HOVER = "#dbeafe"
UI_ACCENT_ACTIVE = "#1d4ed8"
UI_CHROME_BG = "#eef3f8"
UI_WINDOW_ALT = "#f8fbff"
UI_PAGE_HOVER_BG = "#f1f5f9"
UI_ACTIVE_PAGE_BG = UI_ACCENT_SOFT
UI_ACTIVE_PAGE_FG = UI_ACCENT
UI_INACTIVE_PAGE_BG = UI_SHELL_BG
UI_INACTIVE_PAGE_FG = "#526173"
UI_TOAST_BG = "#17202a"
UI_TOAST_FG = "#f8fafc"
UI_HUD_BG = "#172536"
UI_HUD_PANEL = "#243447"
UI_HUD_TEXT = "#f8fafc"
UI_HUD_MUTED = "#c6d3e1"
UI_DIALOG_BG = "#f8fafc"
UI_CARD_BG = "#ffffff"
UI_DIVIDER = "#e2e8f0"
UI_FIELD_BG = "#fbfdff"
UI_SUCCESS = "#0f8f6f"
UI_OCR = "#0f9f8f"
UI_OCR_SOFT = "#e6f7f4"
UI_WARNING = "#d97706"
UI_WARNING_SOFT = "#fff4df"
UI_DANGER = "#b42318"
UI_DANGER_SOFT = "#fee4e2"
UI_DISABLED_BG = "#eef2f7"
UI_HEADER_BUTTON_HOVER = "#eef2f7"
UI_CLOSE_HOVER_BG = "#fee2e2"
UI_CLOSE_HOVER_FG = "#b42318"
UI_NAV_BG = "#f1f5f9"
UI_NAV_ACTIVE_BG = "#ffffff"
UI_NAV_HOVER_BG = "#e8eef7"
UI_SETTINGS_PANEL_BG = "#ffffff"

# --- 暖色纸张质感色板(便签窗口专用,不影响设置窗口) ---
NOTE_BORDER = "#e6dcc8"
NOTE_SHELL_BG = "#f3ece0"
NOTE_HEADER_BG = "#faf6ee"
NOTE_HEADER_TEXT = "#3a2f24"
NOTE_PAPER_BG = "#faf6ee"
NOTE_PAPER_BORDER = "#e8dec9"
NOTE_TEXT = "#3a2f24"
NOTE_MUTED_TEXT = "#6f604e"
NOTE_ACCENT = "#9b4f16"
NOTE_ACCENT_SOFT = "#f7e8d6"
NOTE_ACCENT_SOFTER = "#fbf2e6"
NOTE_ACCENT_HOVER = "#eed9bf"
NOTE_ACCENT_ACTIVE = "#a85f20"
NOTE_INSERT = NOTE_ACCENT
NOTE_SELECTION_BG = "#f0e2c8"
NOTE_SELECTION_FG = "#3a2f24"
NOTE_RESIZE_GRIP = "#b8a98f"
NOTE_PAGE_HOVER_BG = "#ede3d3"
NOTE_ACTIVE_PAGE_BG = NOTE_ACCENT_SOFT
NOTE_ACTIVE_PAGE_FG = NOTE_ACCENT
NOTE_INACTIVE_PAGE_BG = NOTE_SHELL_BG
NOTE_INACTIVE_PAGE_FG = NOTE_MUTED_TEXT
NOTE_HEADER_BUTTON_HOVER = "#ede3d3"
NOTE_CLOSE_HOVER_BG = "#f7e2cf"
NOTE_CLOSE_HOVER_FG = "#a85f20"
NOTE_OCR = "#8a6d3b"
NOTE_OCR_SOFT = "#f3ead8"
NOTE_WARNING = "#b5730a"
NOTE_WARNING_SOFT = "#f7e8cf"
NOTE_AUTOSAVE_BG = NOTE_ACCENT_SOFTER
NOTE_AUTOSAVE_FG = NOTE_MUTED_TEXT
NOTE_FOOTER_BG = NOTE_PAPER_BG
NOTE_FOOTER_HINT = "#6b5b49"
NOTE_SRC_TAG = NOTE_MUTED_TEXT
NOTE_DST_TAG = NOTE_ACCENT
NOTE_TOAST_BG = "#2a2118"
NOTE_TOAST_FG = "#faf6ee"

# --- 设置窗口暖色(沿用便签暖调) ---
NOTE_DIALOG_BG = "#f5efe4"
NOTE_NAV_BG = "#efe6d6"
NOTE_NAV_ACTIVE_BG = "#faf6ee"
NOTE_NAV_HOVER_BG = "#e8dcc8"
NOTE_SETTINGS_PANEL_BG = "#faf6ee"
NOTE_FIELD_BG = "#fdfaf3"
NOTE_DIVIDER = "#e2d6c2"
NOTE_DANGER = "#a8442a"
NOTE_DANGER_SOFT = "#f5e2d8"
NOTE_SUCCESS = "#35662f"
NOTE_WARNING_NOTE = "#b5730a"
NOTE_DISABLED_BG = "#e8e0d2"
NOTE_HEADER_TEXT = "#3a2f24"
NOTE_CARD_BG = "#faf6ee"
NOTE_DANGER_SOFT = "#f5e2d8"

EVENT_DEBOUNCE_SECONDS = 0.05
DOUBLE_CLICK_SECONDS = 0.3
AUTOSAVE_DELAY_MS = 600
TRANSLATION_TASK_TIMEOUT_SECONDS = 30
CLEAR_UNDO_WINDOW_MS = 8000
SETTINGS_WORK_AREA_FRACTION = 0.9
HOOK_RETRY_MAX_SECONDS = 30
HOOK_RETRY_MAX_FAILURES = 6
MAX_LOG_BYTES = 1_048_576
MAX_LOG_FILES = 3
CODEX_TIMEOUT_SECONDS = 25
CODEX_MODEL = "gpt-5.4-mini"
CODEX_REASONING_EFFORT = "low"
DEEPSEEK_TEXT_MODEL = "deepseek-chat"
DEEPSEEK_CHAT_COMPLETIONS_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_TIMEOUT_SECONDS = 8
VOCABULARY_GENERATION_TIMEOUT_SECONDS = 60
VOCABULARY_RECENT_LIMIT = 30
VOCABULARY_MAX_ENTRIES = 150
DEFAULT_APP_SETTINGS = {
    "side_button": "xbutton1",
    "block_browser_key": True,
    "double_click_ms": 300,
    "side_response_mode": "compatibility",
    "allow_image_fallback": False,
}
SIDE_RESPONSE_MODES = {
    "compatibility": "兼容模式",
    "immediate": "即时框选",
}
SIDE_BUTTON_OPTIONS = {
    "xbutton1": {
        "label": "鼠标侧键 1",
        "detail": "常见为浏览器后退键",
        "button": XBUTTON1,
        "browser_key": VK_BROWSER_BACK,
    },
    "xbutton2": {
        "label": "鼠标侧键 2",
        "detail": "常见为浏览器前进键",
        "button": XBUTTON2,
        "browser_key": VK_BROWSER_FORWARD,
    },
}
MIN_DOUBLE_CLICK_MS = 150
MAX_DOUBLE_CLICK_MS = 900
CODEX_UNSUPPORTED_MODEL_PATTERNS = (
    "model is not supported",
    "unsupported model",
    "Unknown model",
)
MIN_CAPTURE_SIZE = 8
OVERLAY_ALPHA = 0.25
CAPTURE_AFTER_OVERLAY_DELAY_MS = 120
CODEX_PROMPT = """Recognize the English word or short phrase in this screenshot and translate it into concise Simplified Chinese.
The image is the user's selected crop. Read only the visible English text inside that crop; ignore borders, overlays, cursor artifacts, and surrounding UI.
Return strict JSON only, with this exact shape:
{"source_text":"recognized English text","translation":"Chinese translation"}
Do not use Markdown. Do not include explanations."""
TEXT_TRANSLATION_SYSTEM_PROMPT = (
    "You are a precise English to Simplified Chinese dictionary. "
    "Return strict JSON only. If a word is ambiguous, include the most common "
    "Chinese meanings separated by Chinese semicolons."
)
VOCABULARY_STUDY_SYSTEM_PROMPT = (
    "你是一名英语词汇学习教练。请只围绕用户提供的单词和短语，"
    "把零散记录整理成简洁、准确、可复习的中文学习材料。"
    "输出 Markdown，不要解释生成过程。"
)


user32 = ctypes.windll.user32
shell32 = ctypes.windll.shell32
kernel32 = ctypes.windll.kernel32
ULONG_PTR = wintypes.WPARAM
LRESULT = wintypes.LPARAM
INSTANCE_MUTEX = None
DPI_AWARENESS_CONFIGURED = False
LOG_LOCK = threading.Lock()
WINDOW_GEOMETRY_RE = re.compile(r"^(?:(\d+)x(\d+))?([+-]\d+)([+-]\d+)$")
HICON = getattr(wintypes, "HICON", wintypes.HANDLE)
HMENU = getattr(wintypes, "HMENU", wintypes.HANDLE)
HCURSOR = getattr(wintypes, "HCURSOR", wintypes.HANDLE)
HBRUSH = getattr(wintypes, "HBRUSH", wintypes.HANDLE)


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
    ]


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", POINT),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


LowLevelMouseProc = ctypes.WINFUNCTYPE(
    LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
)


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


LowLevelKeyboardProc = ctypes.WINFUNCTYPE(
    LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
)


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", HICON),
        ("szTip", wintypes.WCHAR * 128),
        ("dwState", wintypes.DWORD),
        ("dwStateMask", wintypes.DWORD),
        ("szInfo", wintypes.WCHAR * 256),
        ("uTimeoutOrVersion", wintypes.UINT),
        ("szInfoTitle", wintypes.WCHAR * 64),
        ("dwInfoFlags", wintypes.DWORD),
        ("guidItem", ctypes.c_byte * 16),
        ("hBalloonIcon", HICON),
    ]


WindowProc = ctypes.WINFUNCTYPE(
    LRESULT,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)


class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("style", wintypes.UINT),
        ("lpfnWndProc", WindowProc),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", HICON),
        ("hCursor", HCURSOR),
        ("hbrBackground", HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
        ("hIconSm", HICON),
    ]


user32.SetWindowsHookExW.argtypes = (
    ctypes.c_int,
    ctypes.c_void_p,
    wintypes.HINSTANCE,
    wintypes.DWORD,
)
user32.SetWindowsHookExW.restype = wintypes.HHOOK
user32.CallNextHookEx.argtypes = (
    wintypes.HHOOK,
    ctypes.c_int,
    wintypes.WPARAM,
    wintypes.LPARAM,
)
user32.CallNextHookEx.restype = LRESULT
user32.UnhookWindowsHookEx.argtypes = (wintypes.HHOOK,)
user32.UnhookWindowsHookEx.restype = wintypes.BOOL
user32.PostThreadMessageW.argtypes = (
    wintypes.DWORD,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)
user32.PostThreadMessageW.restype = wintypes.BOOL
user32.GetSystemMetrics.argtypes = (ctypes.c_int,)
user32.GetSystemMetrics.restype = ctypes.c_int
user32.GetCursorPos.argtypes = (ctypes.POINTER(POINT),)
user32.GetCursorPos.restype = wintypes.BOOL
user32.MonitorFromPoint.argtypes = (POINT, wintypes.DWORD)
user32.MonitorFromPoint.restype = wintypes.HANDLE
user32.GetMonitorInfoW.argtypes = (wintypes.HANDLE, ctypes.POINTER(MONITORINFO))
user32.GetMonitorInfoW.restype = wintypes.BOOL
user32.ShowWindow.argtypes = (wintypes.HWND, ctypes.c_int)
user32.ShowWindow.restype = wintypes.BOOL
user32.SetForegroundWindow.argtypes = (wintypes.HWND,)
user32.SetForegroundWindow.restype = wintypes.BOOL
user32.SetActiveWindow.argtypes = (wintypes.HWND,)
user32.SetActiveWindow.restype = wintypes.HWND
user32.GetForegroundWindow.argtypes = ()
user32.GetForegroundWindow.restype = wintypes.HWND
user32.SetWindowPos.argtypes = (
    wintypes.HWND,
    wintypes.HWND,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.UINT,
)
user32.SetWindowPos.restype = wintypes.BOOL
user32.LoadImageW.argtypes = (
    wintypes.HINSTANCE,
    wintypes.LPCWSTR,
    wintypes.UINT,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.UINT,
)
user32.LoadImageW.restype = HICON
user32.DestroyIcon.argtypes = (HICON,)
user32.DestroyIcon.restype = wintypes.BOOL
user32.RegisterWindowMessageW.argtypes = (wintypes.LPCWSTR,)
user32.RegisterWindowMessageW.restype = wintypes.UINT
user32.PostMessageW.argtypes = (
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)
user32.PostMessageW.restype = wintypes.BOOL
user32.RegisterClassExW.argtypes = (ctypes.POINTER(WNDCLASSEXW),)
user32.RegisterClassExW.restype = wintypes.ATOM
user32.CreateWindowExW.argtypes = (
    wintypes.DWORD,
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    wintypes.DWORD,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.HWND,
    HMENU,
    wintypes.HINSTANCE,
    wintypes.LPVOID,
)
user32.CreateWindowExW.restype = wintypes.HWND
user32.DefWindowProcW.argtypes = (
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)
user32.DefWindowProcW.restype = LRESULT
user32.DestroyWindow.argtypes = (wintypes.HWND,)
user32.DestroyWindow.restype = wintypes.BOOL
user32.PostQuitMessage.argtypes = (ctypes.c_int,)
user32.PostQuitMessage.restype = None
user32.GetMessageW.argtypes = (
    ctypes.POINTER(wintypes.MSG),
    wintypes.HWND,
    wintypes.UINT,
    wintypes.UINT,
)
user32.GetMessageW.restype = ctypes.c_int
user32.TranslateMessage.argtypes = (ctypes.POINTER(wintypes.MSG),)
user32.TranslateMessage.restype = wintypes.BOOL
user32.DispatchMessageW.argtypes = (ctypes.POINTER(wintypes.MSG),)
user32.DispatchMessageW.restype = LRESULT
shell32.Shell_NotifyIconW.argtypes = (wintypes.DWORD, ctypes.POINTER(NOTIFYICONDATAW))
shell32.Shell_NotifyIconW.restype = wintypes.BOOL
kernel32.GetCurrentThreadId.restype = wintypes.DWORD
kernel32.GetLastError.restype = wintypes.DWORD
kernel32.GetModuleHandleW.argtypes = (wintypes.LPCWSTR,)
kernel32.GetModuleHandleW.restype = wintypes.HMODULE
kernel32.CreateMutexW.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR)
kernel32.CreateMutexW.restype = wintypes.HANDLE


def configure_dpi_awareness():
    global DPI_AWARENESS_CONFIGURED
    if DPI_AWARENESS_CONFIGURED or sys.platform != "win32":
        return

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            user32.SetProcessDPIAware()
        except Exception as exc:
            log(f"dpi awareness setup failed: {exc}")
            return

    DPI_AWARENESS_CONFIGURED = True


def log(message):
    try:
        with LOG_LOCK:
            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            _rotate_log_if_needed()
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            with LOG_FILE.open("a", encoding="utf-8") as file:
                file.write(f"{timestamp} {str(message)[:500]}\n")
    except OSError:
        pass


def _rotate_log_if_needed():
    if not LOG_FILE.exists() or LOG_FILE.stat().st_size < MAX_LOG_BYTES:
        return

    oldest = LOG_FILE.with_name(f"{LOG_FILE.name}.{MAX_LOG_FILES}")
    oldest.unlink(missing_ok=True)
    for index in range(MAX_LOG_FILES - 1, 0, -1):
        source = LOG_FILE.with_name(f"{LOG_FILE.name}.{index}")
        if source.exists():
            source.replace(LOG_FILE.with_name(f"{LOG_FILE.name}.{index + 1}"))
    LOG_FILE.replace(LOG_FILE.with_name(f"{LOG_FILE.name}.1"))


def backup_file_for(path):
    path = Path(path)
    return path.with_name(f"{path.name}.bak")


def atomic_write_text(path, content, encoding="utf-8"):
    """Write a text file without exposing a partially written target file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        descriptor, temp_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            text=True,
        )
        temp_path = Path(temp_name)
        with os.fdopen(descriptor, "w", encoding=encoding, newline="") as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        if path.exists():
            shutil.copy2(path, backup_file_for(path))
        os.replace(temp_path, path)
    except Exception:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise


def read_text_with_fallback(path):
    path = Path(path)
    last_error = None
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    return path.read_text(encoding="utf-8")


def read_text_with_backup(path):
    path = Path(path)
    errors = []
    for candidate, recovered in ((path, False), (backup_file_for(path), True)):
        if not candidate.exists():
            continue
        try:
            return read_text_with_fallback(candidate), recovered
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(exc)
    if errors:
        raise errors[-1]
    raise FileNotFoundError(path)


def discover_note_pages():
    pages = list(DEFAULT_NOTE_PAGES)
    if not NOTE_DIR.exists():
        return pages

    page_ids = {page["id"] for page in pages}
    for note_path in NOTE_DIR.glob("note-*.txt"):
        match = re.fullmatch(r"note-(\d+)\.txt", note_path.name)
        if not match:
            continue
        page_id = int(match.group(1))
        if page_id > 0 and page_id not in page_ids:
            pages.append({"id": page_id, "name": str(page_id)})
            page_ids.add(page_id)
    return normalize_note_pages(pages)


def monitor_work_area_for_point(x, y, fallback_width, fallback_height):
    """Return the target monitor work area, with a primary-screen fallback."""
    try:
        monitor = user32.MonitorFromPoint(POINT(x, y), 2)
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        if monitor and user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
            return (
                info.rcWork.left,
                info.rcWork.top,
                info.rcWork.right,
                info.rcWork.bottom,
            )
    except Exception:
        pass
    return 0, 0, fallback_width, fallback_height


def clamp_dialog_to_work_area(
    requested_width,
    requested_height,
    work_area,
    fraction=SETTINGS_WORK_AREA_FRACTION,
):
    """Fit a settings dialog inside the target monitor's usable work area."""
    left, top, right, bottom = work_area
    available_width = max(1, int(right) - int(left))
    available_height = max(1, int(bottom) - int(top))
    maximum_width = max(320, int(available_width * fraction))
    maximum_height = max(260, int(available_height * fraction))
    width = min(max(320, int(requested_width)), maximum_width, available_width)
    height = min(max(260, int(requested_height)), maximum_height, available_height)
    x = int(left) + max(0, (available_width - width) // 2)
    y = int(top) + max(0, (available_height - height) // 2)
    return width, height, x, y


def opposite_corner_position(
    container_width,
    container_height,
    item_width,
    item_height,
    pointer_x,
    pointer_y,
    margin=28,
):
    """Place an overlay item in the corner opposite the pointer."""
    container_width = max(1, int(container_width))
    container_height = max(1, int(container_height))
    item_width = min(max(1, int(item_width)), container_width)
    item_height = min(max(1, int(item_height)), container_height)
    margin = max(0, int(margin))
    left = min(margin, max(0, container_width - item_width))
    top = min(margin, max(0, container_height - item_height))
    right = max(0, container_width - item_width - margin)
    bottom = max(0, container_height - item_height - margin)
    x = right if float(pointer_x) < container_width / 2 else left
    y = bottom if float(pointer_y) < container_height / 2 else top
    return x, y


@dataclass(frozen=True)
class TranslationResult:
    source_text: str
    translation: str


@dataclass
class TranslationTask:
    task_id: int
    image_path: Path
    cancelled: threading.Event = field(default_factory=threading.Event)
    started_at: float = field(default_factory=time.monotonic)
    timeout_after_id: object = None


@dataclass(frozen=True)
class VocabularyEntry:
    term: str
    translation: str = ""
    created_at: str = ""
    source: str = ""


@dataclass(frozen=True)
class StudioOutput:
    mode: str
    title: str
    extension: str
    content: str


def format_window_geometry(width, height, x, y):
    width = max(int(width), MIN_WINDOW_WIDTH)
    height = max(int(height), MIN_WINDOW_HEIGHT)
    return f"{width}x{height}{int(x):+d}{int(y):+d}"


def normalize_window_geometry(geometry):
    match = WINDOW_GEOMETRY_RE.fullmatch(str(geometry or "").strip())
    if not match:
        return format_window_geometry(
            WINDOW_WIDTH, WINDOW_HEIGHT, DEFAULT_WINDOW_X, DEFAULT_WINDOW_Y
        )

    width = int(match.group(1) or WINDOW_WIDTH)
    height = int(match.group(2) or WINDOW_HEIGHT)
    x = int(match.group(3))
    y = int(match.group(4))
    return format_window_geometry(width, height, x, y)


def parse_window_size(geometry):
    match = WINDOW_GEOMETRY_RE.fullmatch(str(geometry or "").strip())
    if not match:
        return WINDOW_WIDTH, WINDOW_HEIGHT

    width = max(int(match.group(1) or WINDOW_WIDTH), MIN_WINDOW_WIDTH)
    height = max(int(match.group(2) or WINDOW_HEIGHT), MIN_WINDOW_HEIGHT)
    return width, height


def clamp_page_rail_width(content_width):
    desired_width = int(content_width) + PAGE_LABEL_PADDING_X * 2
    return max(PAGE_RAIL_MIN_WIDTH, min(PAGE_RAIL_MAX_WIDTH, desired_width))


def page_label_anchor(name):
    return "center" if re.fullmatch(r"\d+", str(name).strip()) else "w"


def normalize_page_name(name, fallback):
    name = str(name or "").strip()
    if not name:
        name = str(fallback)
    return name[:MAX_PAGE_NAME_CHARS]


def page_file_for_id(page_id):
    page_id = normalized_note_page(page_id)
    if page_id == 1:
        return NOTE_FILE
    return NOTE_DIR / f"note-{page_id}.txt"


def normalize_note_pages(pages):
    normalized_pages = []
    seen_ids = set()
    default_ids = {int(page["id"]) for page in DEFAULT_NOTE_PAGES}

    for page in DEFAULT_NOTE_PAGES:
        page_id = int(page["id"])
        normalized_pages.append({"id": page_id, "name": page["name"]})
        seen_ids.add(page_id)

    if not isinstance(pages, list):
        return normalized_pages

    for page in pages:
        if not isinstance(page, dict):
            continue
        try:
            page_id = int(page.get("id"))
        except (TypeError, ValueError):
            continue
        if page_id <= 0:
            continue
        if page_id in default_ids:
            for item in normalized_pages:
                if item["id"] == page_id:
                    item["name"] = normalize_page_name(page.get("name"), page_id)
                    break
            continue
        if page_id in seen_ids:
            continue

        normalized_pages.append(
            {"id": page_id, "name": normalize_page_name(page.get("name"), page_id)}
        )
        seen_ids.add(page_id)

    return normalized_pages


def normalized_note_page(page, pages=None):
    try:
        page = int(page)
    except (TypeError, ValueError):
        page = 1
    page = max(1, page)
    if not pages:
        return page

    page_ids = [int(item["id"]) for item in pages]
    if page in page_ids:
        return page
    return page_ids[0] if page_ids else 1


def note_file_for_page(page):
    return page_file_for_id(page)


def normalize_vocabulary_term(value):
    term = re.sub(r"\s+", " ", str(value or "")).strip()
    term = re.sub(r"^(?:[-*•]|\d+[.)、])\s*", "", term)
    return term.strip(" \t\r\n\"'“”‘’.,;:!?，。；：！？()[]{}")


def is_vocabulary_term(value):
    term = normalize_vocabulary_term(value)
    if not term or len(term) > 80 or len(term.split()) > 6:
        return False
    return bool(
        re.fullmatch(r"[A-Za-z][A-Za-z0-9'’\-]*(?:\s+[A-Za-z0-9'’\-]+){0,5}", term)
    )


def normalize_vocabulary_translation(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def extract_vocabulary_entries_from_text(text, source="note"):
    entries = []
    lines = str(text or "").splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        source_match = re.match(r"^原文\s*[:：]\s*(.+)$", line)
        if source_match:
            term = normalize_vocabulary_term(source_match.group(1))
            translation = ""
            if index + 1 < len(lines):
                translation_match = re.match(
                    r"^译文\s*[:：]\s*(.*)$", lines[index + 1].strip()
                )
                if translation_match:
                    translation = normalize_vocabulary_translation(
                        translation_match.group(1)
                    )
                    index += 1
            if is_vocabulary_term(term):
                entries.append(
                    VocabularyEntry(term=term, translation=translation, source=source)
                )
        elif is_vocabulary_term(line):
            entries.append(
                VocabularyEntry(
                    term=normalize_vocabulary_term(line),
                    source=source,
                )
            )
        index += 1
    return entries


def read_vocabulary_jsonl(path):
    path = Path(path)
    if not path.exists():
        return []

    entries = []
    try:
        lines = read_text_with_fallback(path).splitlines()
    except (OSError, UnicodeDecodeError):
        return entries

    for line in lines:
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        term = normalize_vocabulary_term(row.get("source_text"))
        if not is_vocabulary_term(term):
            continue
        entries.append(
            VocabularyEntry(
                term=term,
                translation=normalize_vocabulary_translation(row.get("translation")),
                created_at=str(row.get("created_at") or ""),
                source=path.name,
            )
        )
    return entries


def merge_vocabulary_entries(entries):
    order = []
    merged = {}
    for entry in entries:
        term = normalize_vocabulary_term(entry.term)
        if not is_vocabulary_term(term):
            continue
        key = term.casefold()
        previous = merged.get(key)
        if previous is not None:
            order.remove(key)
        merged[key] = VocabularyEntry(
            term=term,
            translation=(
                normalize_vocabulary_translation(entry.translation)
                or (previous.translation if previous is not None else "")
            ),
            created_at=entry.created_at or (previous.created_at if previous else ""),
            source=entry.source or (previous.source if previous else ""),
        )
        order.append(key)
    return [merged[key] for key in order]


def collect_vocabulary_entries(note_paths=None, vocabulary_path=VOCABULARY_FILE):
    entries = read_vocabulary_jsonl(vocabulary_path)
    for note_path in note_paths or (NOTE_FILE,):
        note_path = Path(note_path)
        if not note_path.exists():
            continue
        try:
            content = read_text_with_fallback(note_path)
        except (OSError, UnicodeDecodeError):
            continue
        entries.extend(
            extract_vocabulary_entries_from_text(content, source=note_path.name)
        )
    return merge_vocabulary_entries(entries)


def build_vocabulary_learning_prompt(entries):
    selected = list(entries)[-VOCABULARY_MAX_ENTRIES:]
    vocabulary_lines = []
    for entry in selected:
        translation = entry.translation or "（未记录释义）"
        vocabulary_lines.append(f"- {entry.term} — {translation}")
    vocabulary = "\n".join(vocabulary_lines)
    return (
        f"请把以下 {len(selected)} 个单词和短语整理成一份中文词汇学习包。\n\n"
        "严格使用下面的结构：\n"
        "# 词汇学习包\n"
        "## 主题分组\n"
        "按含义或使用场景分组，每个输入词都要出现，并保留英文和简明中文释义。\n"
        "## 易混词与常用搭配\n"
        "只选择确实容易混淆或有常见搭配的词，不要硬凑。\n"
        "## 例句\n"
        "选择最值得掌握的词写自然、简短的英文例句，并附中文翻译。\n"
        "## 记忆路线\n"
        "给出一条简短的分组复习顺序。\n"
        "## 复习小测\n"
        "生成 8 道填空或释义题，最后单独列出答案。\n\n"
        "不要增加新的目标词，不要编造词义。输入词表如下：\n"
        f"{vocabulary}"
    )


def strip_markdown_fence(text):
    content = str(text or "").strip()
    match = re.fullmatch(r"```(?:markdown|md)?\s*(.*?)\s*```", content, re.DOTALL)
    return match.group(1).strip() if match else content


def save_studio_output(output, directory=STUDIO_DIR, now=None):
    directory = Path(directory)
    timestamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
    path = directory / f"vocabulary-study-pack-{timestamp}.{output.extension}"
    counter = 2
    while path.exists():
        path = directory / (
            f"vocabulary-study-pack-{timestamp}-{counter}.{output.extension}"
        )
        counter += 1
    atomic_write_text(path, output.content.rstrip() + "\n")
    return path


def read_state_data():
    if not STATE_FILE.exists() and not backup_file_for(STATE_FILE).exists():
        return {}
    for candidate, recovered in ((STATE_FILE, False), (backup_file_for(STATE_FILE), True)):
        if not candidate.exists():
            continue
        try:
            data = json.loads(read_text_with_fallback(candidate))
            if not isinstance(data, dict):
                raise json.JSONDecodeError("state is not an object", "", 0)
            if recovered:
                log("state recovered from backup")
            return data
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
    log("state could not be read; using recoverable defaults")
    return {}


def normalize_bool(value, default=False):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    if value is None:
        return default
    return bool(value)


def clamp_int(value, minimum, maximum, default):
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


def normalize_app_settings(settings):
    if not isinstance(settings, dict):
        settings = {}

    side_button = str(settings.get("side_button", DEFAULT_APP_SETTINGS["side_button"]))
    side_button = side_button.strip().lower()
    if side_button not in SIDE_BUTTON_OPTIONS:
        side_button = DEFAULT_APP_SETTINGS["side_button"]

    side_response_mode = str(
        settings.get(
            "side_response_mode",
            DEFAULT_APP_SETTINGS["side_response_mode"],
        )
    ).strip().lower()
    if side_response_mode not in SIDE_RESPONSE_MODES:
        side_response_mode = DEFAULT_APP_SETTINGS["side_response_mode"]

    return {
        "side_button": side_button,
        "block_browser_key": normalize_bool(
            settings.get("block_browser_key"),
            DEFAULT_APP_SETTINGS["block_browser_key"],
        ),
        "double_click_ms": clamp_int(
            settings.get("double_click_ms"),
            MIN_DOUBLE_CLICK_MS,
            MAX_DOUBLE_CLICK_MS,
            DEFAULT_APP_SETTINGS["double_click_ms"],
        ),
        "side_response_mode": side_response_mode,
        "allow_image_fallback": normalize_bool(
            settings.get("allow_image_fallback"),
            DEFAULT_APP_SETTINGS["allow_image_fallback"],
        ),
    }


def side_button_value(settings):
    settings = normalize_app_settings(settings)
    return SIDE_BUTTON_OPTIONS[settings["side_button"]]["button"]


def blocked_browser_keys_for_settings(settings):
    settings = normalize_app_settings(settings)
    if not settings["block_browser_key"]:
        return set()
    return {SIDE_BUTTON_OPTIONS[settings["side_button"]]["browser_key"]}


def update_ocr_status_if_available(app, active=False):
    status_updater = getattr(app, "_set_ocr_status", None)
    if callable(status_updater):
        status_updater(active)


def quote_windows_argument(value):
    text = str(value).replace('"', "")
    return f'"{text}"'


def build_app_launch_command(executable_path=None, script_path=None, frozen=None):
    if frozen is None:
        frozen = bool(getattr(sys, "frozen", False))

    if executable_path is None:
        executable = Path(sys.executable)
        if not frozen:
            pythonw = executable.with_name("pythonw.exe")
            if pythonw.exists():
                executable = pythonw
    else:
        executable = Path(executable_path)

    if frozen:
        return quote_windows_argument(executable)

    script = Path(script_path) if script_path is not None else Path(__file__).resolve()
    return f"{quote_windows_argument(executable)} {quote_windows_argument(script)}"


def get_startup_registry_value():
    if sys.platform != "win32":
        return ""
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_RUN_KEY_PATH) as key:
            value, _value_type = winreg.QueryValueEx(key, STARTUP_RUN_VALUE_NAME)
            return str(value or "").strip()
    except OSError:
        return ""


def is_startup_enabled():
    return bool(get_startup_registry_value())


def set_startup_enabled(enabled):
    if sys.platform != "win32":
        raise RuntimeError("开机启动只支持 Windows")

    import winreg

    with winreg.CreateKeyEx(
        winreg.HKEY_CURRENT_USER, STARTUP_RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE
    ) as key:
        if enabled:
            winreg.SetValueEx(
                key,
                STARTUP_RUN_VALUE_NAME,
                0,
                winreg.REG_SZ,
                build_app_launch_command(),
            )
        else:
            try:
                winreg.DeleteValue(key, STARTUP_RUN_VALUE_NAME)
            except FileNotFoundError:
                pass


def parse_codex_translation_output(output):
    cleaned = output.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    decoder = json.JSONDecoder()
    data = None
    for match in re.finditer(r"\{", cleaned):
        try:
            data, _end = decoder.raw_decode(cleaned[match.start() :])
            break
        except json.JSONDecodeError:
            continue
    if data is None:
        raise ValueError("Codex output did not contain JSON")

    source_text = str(data.get("source_text", "")).strip()
    translation = str(data.get("translation", "")).strip()
    if not source_text:
        raise ValueError("Codex output missing source_text")
    if not translation:
        raise ValueError("Codex output missing translation")
    return TranslationResult(source_text=source_text, translation=translation)


def extract_codex_error_message(output):
    text = str(output or "").strip()
    if not text:
        return "Codex CLI failed"

    json_errors = re.findall(r"ERROR:\s*(\{.*?\})(?=\r?\n|$)", text)
    for json_error in reversed(json_errors):
        try:
            data = json.loads(json_error)
        except json.JSONDecodeError:
            continue

        message = data.get("error", {}).get("message")
        if message:
            return str(message).strip()

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("ERROR:"):
            return stripped.removeprefix("ERROR:").strip()

    meaningful_lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
        and not line.lstrip().startswith(("20", "OpenAI Codex", "--------", "warning:"))
    ]
    message = meaningful_lines[0] if meaningful_lines else text
    if len(message) > 220:
        message = message[:217] + "..."
    return message


def is_unsupported_codex_model_error(message):
    lowered = str(message).lower()
    return any(pattern.lower() in lowered for pattern in CODEX_UNSUPPORTED_MODEL_PATTERNS)


class NoteStore:
    def __init__(self, note_file, vocabulary_file):
        self.note_file = Path(note_file)
        self.vocabulary_file = Path(vocabulary_file)

    def append_vocabulary(self, result):
        self.vocabulary_file.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "source_text": result.source_text,
            "translation": result.translation,
        }
        with self.vocabulary_file.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
            file.flush()
            os.fsync(file.fileno())

    def format_note_record(self, result):
        return f"原文：{result.source_text}\n译文：{result.translation}\n"


def get_user_environment_value(name):
    value = os.environ.get(name)
    if value:
        return value.strip()

    if sys.platform == "win32":
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
                value, _value_type = winreg.QueryValueEx(key, name)
                if value:
                    return str(value).strip()
        except OSError:
            pass

    return ""


def normalize_api_key(value):
    return str(value or "").strip()


def is_plausible_api_key(value):
    value = normalize_api_key(value)
    return len(value) >= 20 and not any(char.isspace() for char in value)


def broadcast_environment_change():
    if sys.platform != "win32":
        return

    result = wintypes.DWORD()
    try:
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST,
            WM_SETTINGCHANGE,
            0,
            "Environment",
            SMTO_ABORTIFHUNG,
            5000,
            ctypes.byref(result),
        )
    except Exception as exc:
        log(f"environment change broadcast failed: {exc}")


def set_user_environment_value(name, value):
    value = normalize_api_key(value)
    if not value:
        raise ValueError(f"{name} is empty")

    os.environ[name] = value
    if sys.platform == "win32":
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
        broadcast_environment_change()


def delete_user_environment_value(name):
    os.environ.pop(name, None)
    if sys.platform == "win32":
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE
        ) as key:
            try:
                winreg.DeleteValue(key, name)
            except FileNotFoundError:
                pass
        broadcast_environment_change()


def is_deepseek_api_configured():
    return bool(get_user_environment_value("DEEPSEEK_API_KEY"))


def verify_deepseek_api_key(api_key):
    """Validate an entered key without saving it or exposing it in logs."""
    api_key = normalize_api_key(api_key)
    if not is_plausible_api_key(api_key):
        return False, "API Key 看起来不完整。"

    body = {
        "model": DEEPSEEK_TEXT_MODEL,
        "messages": [{"role": "user", "content": "Reply with OK."}],
        "max_tokens": 4,
        "temperature": 0,
    }
    request = urllib.request.Request(
        DEEPSEEK_CHAT_COMPLETIONS_URL,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=DEEPSEEK_TIMEOUT_SECONDS):
            pass
    except urllib.error.HTTPError as exc:
        if exc.code in {401, 403}:
            return False, "验证失败：API Key 无效或没有权限。"
        return False, f"验证失败：服务返回 HTTP {exc.code}。"
    except OSError:
        return False, "验证失败：无法连接 DeepSeek 服务。"
    except Exception:
        return False, "验证失败：响应格式异常。"
    return True, "连接正常，API Key 可用。"


def normalize_ocr_text(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


class WindowsOcrBackend:
    def __init__(self, tmp_dir=TMP_DIR):
        self.tmp_dir = Path(tmp_dir)

    def recognize_text(self, image_path):
        prepared_image = self._prepare_image(image_path)
        try:
            return asyncio.run(self._recognize_text_async(prepared_image.resolve()))
        finally:
            if prepared_image != Path(image_path):
                try:
                    prepared_image.unlink(missing_ok=True)
                except OSError as exc:
                    log(f"failed to delete OCR temp image: {exc}")

    def _prepare_image(self, image_path):
        image_path = Path(image_path)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        prepared_path = self.tmp_dir / f"ocr-{int(time.time() * 1000)}.png"

        with Image.open(image_path) as image:
            grayscale = ImageOps.autocontrast(image.convert("L"))
            width, height = grayscale.size
            scale = 2 if max(width, height) < 1400 else 1
            if scale > 1:
                grayscale = grayscale.resize(
                    (width * scale, height * scale),
                    Image.Resampling.LANCZOS,
                )
            grayscale.save(prepared_path)

        return prepared_path

    async def _recognize_text_async(self, image_path):
        try:
            from winsdk.windows.globalization import Language
            from winsdk.windows.graphics.imaging import BitmapDecoder
            from winsdk.windows.media.ocr import OcrEngine
            from winsdk.windows.storage import FileAccessMode, StorageFile
        except ImportError as exc:
            raise RuntimeError("Windows OCR dependency winsdk is not installed") from exc

        storage_file = await StorageFile.get_file_from_path_async(str(image_path))
        stream = await storage_file.open_async(FileAccessMode.READ)
        try:
            decoder = await BitmapDecoder.create_async(stream)
            bitmap = await decoder.get_software_bitmap_async()
            engine = OcrEngine.try_create_from_language(Language("en"))
            if engine is None:
                engine = OcrEngine.try_create_from_user_profile_languages()
            if engine is None:
                raise RuntimeError("Windows OCR engine is unavailable")

            result = await engine.recognize_async(bitmap)
        finally:
            try:
                stream.close()
            except AttributeError:
                pass

        return normalize_ocr_text(result.text)


class DeepSeekTextBackend:
    def __init__(self, timeout_seconds=DEEPSEEK_TIMEOUT_SECONDS):
        self.timeout_seconds = timeout_seconds

    def translate_text(self, source_text):
        source_text = normalize_ocr_text(source_text)
        if not source_text:
            raise RuntimeError("OCR recognized no text")

        api_key = get_user_environment_value("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is not set")

        body = {
            "model": DEEPSEEK_TEXT_MODEL,
            "messages": [
                {"role": "system", "content": TEXT_TRANSLATION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Translate this English word or short phrase into concise "
                        "Simplified Chinese:\n"
                        f"{source_text}\n"
                        "Return JSON with this exact shape: "
                        '{"source_text":"...","translation":"..."}'
                    ),
                },
            ],
            "temperature": 0,
            "max_tokens": 120,
            "response_format": {"type": "json_object"},
        }
        request = urllib.request.Request(
            DEEPSEEK_CHAT_COMPLETIONS_URL,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                response_text = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"DeepSeek text translation failed (HTTP {exc.code})"
            ) from exc
        except OSError as exc:
            raise RuntimeError("DeepSeek text translation failed due to a network error") from exc

        data = json.loads(response_text)
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("DeepSeek response missing translation content") from exc

        result = parse_codex_translation_output(content)
        return TranslationResult(source_text=source_text, translation=result.translation)


class VocabularyOrganizerBackend:
    def __init__(self, timeout_seconds=VOCABULARY_GENERATION_TIMEOUT_SECONDS):
        self.timeout_seconds = timeout_seconds

    def generate(self, entries):
        selected = list(entries)[-VOCABULARY_MAX_ENTRIES:]
        if not selected:
            raise RuntimeError("单词本中没有可整理的英文单词。")

        api_key = get_user_environment_value("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("请先在设置中配置 DeepSeek API Key。")

        body = {
            "model": DEEPSEEK_TEXT_MODEL,
            "messages": [
                {"role": "system", "content": VOCABULARY_STUDY_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": build_vocabulary_learning_prompt(selected),
                },
            ],
            "temperature": 0.25,
            "max_tokens": 3000,
        }
        request = urllib.request.Request(
            DEEPSEEK_CHAT_COMPLETIONS_URL,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                response_text = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            if exc.code in {401, 403}:
                raise RuntimeError("API Key 无效或没有权限，请在设置中重新配置。") from exc
            raise RuntimeError(f"单词整理失败：服务返回 HTTP {exc.code}。") from exc
        except OSError as exc:
            raise RuntimeError("单词整理失败：无法连接 DeepSeek 服务。") from exc

        try:
            data = json.loads(response_text)
            content = strip_markdown_fence(data["choices"][0]["message"]["content"])
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("单词整理失败：服务响应格式异常。") from exc
        if not content:
            raise RuntimeError("单词整理失败：服务没有返回内容。")

        first_line = next(
            (line.strip() for line in content.splitlines() if line.strip()),
            "",
        )
        if not re.fullmatch(r"#\s*词汇学习包", first_line):
            content = f"# 词汇学习包\n\n{content}"
        return StudioOutput(
            mode="vocabulary_pack",
            title=f"词汇学习包 · {datetime.now():%Y-%m-%d}",
            extension="md",
            content=content,
        )


class FastTranslationBackend:
    def __init__(self, fallback_backend, image_fallback_enabled=False):
        self.ocr_backend = WindowsOcrBackend()
        self.text_backend = DeepSeekTextBackend()
        self.fallback_backend = fallback_backend
        self.image_fallback_enabled = image_fallback_enabled

    def _image_fallback_is_enabled(self):
        if callable(self.image_fallback_enabled):
            return bool(self.image_fallback_enabled())
        return bool(self.image_fallback_enabled)

    def translate_image(self, image_path, progress_callback=None):
        started = time.perf_counter()
        try:
            if progress_callback:
                progress_callback("recognizing")
            ocr_started = time.perf_counter()
            source_text = normalize_ocr_text(self.ocr_backend.recognize_text(image_path))
            log(
                "windows OCR completed "
                f"text_length={len(source_text)} elapsed={time.perf_counter() - ocr_started:.2f}s"
            )
        except Exception as exc:
            log(f"windows OCR failed: {type(exc).__name__}")
            if not self._image_fallback_is_enabled():
                raise RuntimeError(
                    "本地 OCR 无法识别。请检查 Windows 英语 OCR 语言包，"
                    "或在设置中明确开启图片兜底。"
                ) from exc
            fallback_started = time.perf_counter()
            result = self.fallback_backend.translate_image(image_path)
            log(f"image fallback completed in {time.perf_counter() - fallback_started:.2f}s")
            return result

        try:
            if progress_callback:
                progress_callback("translating")
            result = self.text_backend.translate_text(source_text)
        except Exception as exc:
            log(f"text translation failed: {type(exc).__name__}")
            raise

        log(f"fast translation completed in {time.perf_counter() - started:.2f}s")
        return result


class CodexCliBackend:
    def __init__(self, timeout_seconds=CODEX_TIMEOUT_SECONDS):
        self.timeout_seconds = timeout_seconds

    def translate_image(self, image_path):
        codex_command = shutil.which("codex.cmd") or shutil.which("codex")
        if codex_command is None:
            raise RuntimeError("Codex CLI not found")

        preferred_model = CODEX_MODEL or None
        model_attempts = [preferred_model]
        if preferred_model:
            model_attempts.append(None)

        last_error = None
        for model in model_attempts:
            command = self._build_command(codex_command, image_path, model)
            completed = self._run_codex(command)
            if completed.returncode == 0:
                return parse_codex_translation_output(completed.stdout)

            message = extract_codex_error_message(
                completed.stderr or completed.stdout or "Codex CLI failed"
            )
            last_error = message
            if model and is_unsupported_codex_model_error(message):
                log(f"Codex model {model} unsupported, retrying with default model")
                continue

            raise RuntimeError(message)

        raise RuntimeError(last_error or "Codex CLI failed")

    @staticmethod
    def _build_command(codex_command, image_path, model):
        command = [codex_command, "exec"]
        if model:
            command.extend(["--model", model])
        if CODEX_REASONING_EFFORT:
            command.extend(["-c", f'model_reasoning_effort="{CODEX_REASONING_EFFORT}"'])
        command.extend(["--image", str(image_path), "-"])
        return command

    def _run_codex(self, command):
        try:
            return subprocess.run(
                command,
                input=CODEX_PROMPT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_seconds,
                **hidden_subprocess_kwargs(),
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("Codex CLI timed out") from exc


def hidden_subprocess_kwargs():
    if sys.platform != "win32":
        return {}

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    return {
        "startupinfo": startupinfo,
        "creationflags": subprocess.CREATE_NO_WINDOW,
    }


class _WindowsHookBase:
    def __init__(self, hook_type, callback, name):
        self.hook_type = hook_type
        self._callback = callback
        self.name = name
        self.hook_id = None
        self.thread_id = None
        self.thread = None
        self._ready = threading.Event()
        self._lock = threading.Lock()
        self._stopping = False
        self.failure_count = 0
        self.next_retry_at = 0.0

    def start(self):
        with self._lock:
            if self._stopping:
                return False
            if self.thread is not None and self.thread.is_alive():
                return bool(self.hook_id)
            if time.monotonic() < self.next_retry_at:
                return False
            self._ready.clear()
            self.thread = threading.Thread(target=self._run, daemon=True, name=f"QuickSideNote-{self.name}")
            self.thread.start()
        self._ready.wait(timeout=2)
        return self.is_alive()

    def stop(self):
        with self._lock:
            self._stopping = True
            thread_id = self.thread_id
        if thread_id:
            user32.PostThreadMessageW(thread_id, WM_QUIT, 0, 0)

    def join(self, timeout=2):
        thread = self.thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=timeout)

    def is_alive(self):
        with self._lock:
            return bool(self.thread and self.thread.is_alive() and self.hook_id)

    def _record_install_failure(self):
        with self._lock:
            self.failure_count += 1
            delay = min(2 ** (self.failure_count - 1), HOOK_RETRY_MAX_SECONDS)
            if self.failure_count >= HOOK_RETRY_MAX_FAILURES:
                delay = HOOK_RETRY_MAX_SECONDS
            self.next_retry_at = time.monotonic() + delay
        log(f"{self.name} hook install failed; retry_after={delay}s")

    def _run(self):
        current_thread_id = kernel32.GetCurrentThreadId()
        with self._lock:
            self.thread_id = current_thread_id

        hook_id = user32.SetWindowsHookExW(
            self.hook_type,
            ctypes.cast(self._callback, ctypes.c_void_p),
            kernel32.GetModuleHandleW(None),
            0,
        )
        if not hook_id:
            self._record_install_failure()
            with self._lock:
                if self.thread_id == current_thread_id:
                    self.thread_id = None
            self._ready.set()
            return

        with self._lock:
            self.hook_id = hook_id
            self.failure_count = 0
            self.next_retry_at = 0.0
        self._ready.set()

        try:
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            user32.UnhookWindowsHookEx(hook_id)
            with self._lock:
                if self.hook_id == hook_id:
                    self.hook_id = None
                if self.thread_id == current_thread_id:
                    self.thread_id = None

    def _call_next(self, n_code, w_param, l_param):
        with self._lock:
            hook_id = self.hook_id
        return user32.CallNextHookEx(hook_id, n_code, w_param, l_param)


class MouseSideButtonHook(_WindowsHookBase):
    def __init__(self, event_queue, settings_provider=None):
        self.event_queue = event_queue
        self.settings_provider = settings_provider or (lambda: DEFAULT_APP_SETTINGS)
        super().__init__(WH_MOUSE_LL, LowLevelMouseProc(self._handle_mouse), "mouse")

    def _handle_mouse(self, n_code, w_param, l_param):
        if n_code >= 0 and w_param in (WM_XBUTTONDOWN, WM_XBUTTONUP):
            info = ctypes.cast(l_param, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
            button = (info.mouseData >> 16) & 0xFFFF
            target_button = side_button_value(self.settings_provider())
            if w_param == WM_XBUTTONDOWN and button == target_button:
                self.event_queue.put(("toggle", info.pt.x, info.pt.y))
            if button == target_button:
                return 1

        return self._call_next(n_code, w_param, l_param)


class BrowserKeyHook(_WindowsHookBase):
    def __init__(self, event_queue, settings_provider=None, task_active_provider=None):
        self.event_queue = event_queue
        self.settings_provider = settings_provider or (lambda: DEFAULT_APP_SETTINGS)
        self.task_active_provider = task_active_provider or (lambda: False)
        super().__init__(WH_KEYBOARD_LL, LowLevelKeyboardProc(self._handle_keyboard), "keyboard")

    def _handle_keyboard(self, n_code, w_param, l_param):
        if n_code >= 0 and w_param in (WM_KEYDOWN, WM_SYSKEYDOWN, WM_KEYUP, WM_SYSKEYUP):
            info = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            if info.vkCode == VK_ESCAPE and self.task_active_provider():
                if w_param in (WM_KEYDOWN, WM_SYSKEYDOWN):
                    self.event_queue.put(("cancel_task",))
                return 1
            if info.vkCode in blocked_browser_keys_for_settings(self.settings_provider()):
                if w_param in (WM_KEYDOWN, WM_SYSKEYDOWN):
                    point = POINT()
                    user32.GetCursorPos(ctypes.byref(point))
                    self.event_queue.put(("toggle", point.x, point.y))
                return 1

        return self._call_next(n_code, w_param, l_param)


class TaskProgressHud:
    """A compact task surface that stays visible while the note window is hidden."""

    def __init__(self, root, cancel_callback):
        self.root = root
        self.cancel_callback = cancel_callback
        self.window = tk.Toplevel(root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.configure(bg=NOTE_TOAST_BG)
        self.window.bind("<Escape>", lambda _event: self.cancel_callback())

        frame = tk.Frame(
            self.window,
            bg=NOTE_TOAST_BG,
            highlightthickness=1,
            highlightbackground=NOTE_ACCENT,
            padx=14,
            pady=10,
        )
        frame.pack(fill="both", expand=True)
        frame.grid_columnconfigure(0, weight=1)

        self.title_var = tk.StringVar(value="")
        self.detail_var = tk.StringVar(value="")
        tk.Label(
            frame,
            textvariable=self.title_var,
            bg=NOTE_TOAST_BG,
            fg=NOTE_TOAST_FG,
            anchor="w",
            font=("Microsoft YaHei UI", 10, "bold"),
        ).grid(row=0, column=0, sticky="ew")
        tk.Label(
            frame,
            textvariable=self.detail_var,
            bg=NOTE_TOAST_BG,
            fg="#e9dac4",
            anchor="w",
            justify="left",
            wraplength=300,
            font=("Microsoft YaHei UI", 8),
        ).grid(row=1, column=0, sticky="ew", pady=(3, 0))

        self.actions = tk.Frame(frame, bg=NOTE_TOAST_BG)
        self.actions.grid(row=2, column=0, sticky="e", pady=(10, 0))
        self.retry_button = self._make_button(self.actions, "重新框选")
        self.return_button = self._make_button(self.actions, "返回便签")
        self.cancel_button = self._make_button(
            self.actions,
            "取消 (Esc)",
            command=self.cancel_callback,
        )

    def _make_button(self, parent, text, command=None):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=NOTE_ACCENT_SOFT,
            fg=NOTE_ACCENT,
            activebackground=NOTE_ACCENT_HOVER,
            activeforeground=NOTE_ACCENT_ACTIVE,
            relief="flat",
            bd=0,
            padx=9,
            pady=4,
            cursor="hand2",
            font=("Microsoft YaHei UI", 8, "bold"),
        )

    def show_status(self, title, detail, cancellable=True):
        self.title_var.set(title)
        self.detail_var.set(detail)
        self.retry_button.pack_forget()
        self.return_button.pack_forget()
        self.cancel_button.configure(command=self.cancel_callback)
        if cancellable:
            self.cancel_button.pack(side="right")
        else:
            self.cancel_button.pack_forget()
        self._show_near_pointer()

    def show_failure(self, detail, retry_callback, return_callback):
        self.title_var.set("任务未完成")
        self.detail_var.set(detail)
        self.cancel_button.pack_forget()
        self.retry_button.configure(command=retry_callback)
        self.return_button.configure(command=return_callback)
        self.retry_button.pack(side="right")
        self.return_button.pack(side="right", padx=(0, 6))
        self._show_near_pointer()

    def show_completed(self, detail):
        self.show_status("已完成", detail, cancellable=False)

    def hide(self):
        try:
            self.window.withdraw()
        except tk.TclError:
            pass

    def destroy(self):
        try:
            self.window.destroy()
        except tk.TclError:
            pass

    def _show_near_pointer(self):
        try:
            self.window.update_idletasks()
            width = self.window.winfo_reqwidth()
            height = self.window.winfo_reqheight()
            pointer_x = self.root.winfo_pointerx()
            pointer_y = self.root.winfo_pointery()
            left, top, right, bottom = monitor_work_area_for_point(
                pointer_x,
                pointer_y,
                self.root.winfo_screenwidth(),
                self.root.winfo_screenheight(),
            )
            x = min(max(pointer_x + 12, left), right - width)
            y = min(max(pointer_y + 12, top), bottom - height)
            self.window.geometry(f"{width}x{height}+{x}+{y}")
            self.window.deiconify()
            self.window.lift()
        except tk.TclError:
            pass


class VocabularyStudyDialog:
    def __init__(
        self,
        root,
        entries,
        generate_callback,
        save_callback,
        close_callback,
    ):
        self.root = root
        self.entries = list(entries)
        self.generate_callback = generate_callback
        self.save_callback = save_callback
        self.close_callback = close_callback
        self.output_path = None
        self.closed = False
        self.scope_var = tk.StringVar(value="recent")
        self.status_var = tk.StringVar(value="准备整理")

        self.window = tk.Toplevel(root)
        self.window.title("整理单词")
        self.window.configure(bg=NOTE_DIALOG_BG)
        self.window.resizable(True, True)
        if ICON_FILE.exists():
            self.window.iconbitmap(ICON_FILE)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.window.bind("<Escape>", lambda _event: self.close())
        self.window.bind("<Control-Return>", lambda _event: self._generate())
        self.window.bind("<Control-s>", lambda _event: self._save())

        pointer_x = root.winfo_pointerx()
        pointer_y = root.winfo_pointery()
        work_area = monitor_work_area_for_point(
            pointer_x,
            pointer_y,
            root.winfo_screenwidth(),
            root.winfo_screenheight(),
        )
        width, height, x, y = clamp_dialog_to_work_area(700, 600, work_area)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        self.window.minsize(min(540, width), min(440, height))

        header = tk.Frame(self.window, bg=NOTE_HEADER_BG, height=52)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Frame(header, bg=NOTE_ACCENT, width=4).pack(side="left", fill="y")
        tk.Label(
            header,
            text="整理单词",
            bg=NOTE_HEADER_BG,
            fg=NOTE_HEADER_TEXT,
            anchor="w",
            font=("Microsoft YaHei UI", 12, "bold"),
        ).pack(side="left", fill="y", padx=16)
        tk.Button(
            header,
            text="×",
            command=self.close,
            bg=NOTE_HEADER_BG,
            fg=NOTE_MUTED_TEXT,
            activebackground=NOTE_CLOSE_HOVER_BG,
            activeforeground=NOTE_CLOSE_HOVER_FG,
            relief="flat",
            bd=0,
            width=4,
            cursor="hand2",
            font=("Microsoft YaHei UI", 14),
        ).pack(side="right", fill="y")

        body = tk.Frame(self.window, bg=NOTE_DIALOG_BG, padx=22, pady=18)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(3, weight=1)

        tk.Label(
            body,
            text=f"单词本中找到 {len(self.entries)} 个不重复单词",
            bg=NOTE_DIALOG_BG,
            fg=NOTE_TEXT,
            anchor="w",
            font=("Microsoft YaHei UI", 10, "bold"),
        ).grid(row=0, column=0, sticky="ew")

        scope_row = tk.Frame(body, bg=NOTE_DIALOG_BG)
        scope_row.grid(row=1, column=0, sticky="ew", pady=(12, 14))
        tk.Label(
            scope_row,
            text="整理范围",
            bg=NOTE_DIALOG_BG,
            fg=NOTE_MUTED_TEXT,
            font=("Microsoft YaHei UI", 9),
        ).pack(side="left", padx=(0, 10))
        self.scope_buttons = []
        for value, label in (
            ("recent", f"最近 {min(VOCABULARY_RECENT_LIMIT, len(self.entries))} 个"),
            ("all", f"全部 {min(VOCABULARY_MAX_ENTRIES, len(self.entries))} 个"),
        ):
            button = tk.Radiobutton(
                scope_row,
                text=label,
                value=value,
                variable=self.scope_var,
                indicatoron=False,
                bg=NOTE_FIELD_BG,
                fg=NOTE_TEXT,
                selectcolor=NOTE_ACCENT_SOFT,
                activebackground=NOTE_ACCENT_HOVER,
                activeforeground=NOTE_ACCENT_ACTIVE,
                relief="flat",
                bd=0,
                padx=12,
                pady=5,
                cursor="hand2",
                takefocus=True,
                font=("Microsoft YaHei UI", 9),
            )
            button.pack(side="left", padx=(0, 6))
            self.scope_buttons.append(button)

        tk.Label(
            body,
            text="词汇学习包",
            bg=NOTE_DIALOG_BG,
            fg=NOTE_MUTED_TEXT,
            anchor="w",
            font=("Microsoft YaHei UI", 9),
        ).grid(row=2, column=0, sticky="ew", pady=(0, 6))

        result_frame = tk.Frame(
            body,
            bg=NOTE_PAPER_BORDER,
            padx=1,
            pady=1,
        )
        result_frame.grid(row=3, column=0, sticky="nsew")
        result_frame.grid_rowconfigure(0, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)
        self.result_text = tk.Text(
            result_frame,
            width=1,
            height=1,
            wrap="word",
            relief="flat",
            bd=0,
            padx=14,
            pady=12,
            undo=True,
            bg=NOTE_PAPER_BG,
            fg=NOTE_MUTED_TEXT,
            insertbackground=NOTE_INSERT,
            selectbackground=NOTE_SELECTION_BG,
            selectforeground=NOTE_SELECTION_FG,
            font=("Microsoft YaHei UI", 10),
            spacing3=5,
        )
        self.result_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = tk.Scrollbar(result_frame, command=self.result_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.result_text.configure(yscrollcommand=scrollbar.set)
        self.result_text.insert("1.0", "点击“生成学习包”开始整理。")
        self.result_text.configure(state="disabled")

        status_row = tk.Frame(body, bg=NOTE_DIALOG_BG)
        status_row.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        self.status_label = tk.Label(
            status_row,
            textvariable=self.status_var,
            bg=NOTE_DIALOG_BG,
            fg=NOTE_MUTED_TEXT,
            anchor="w",
            font=("Microsoft YaHei UI", 8),
        )
        self.status_label.pack(side="left", fill="x", expand=True)

        footer = tk.Frame(self.window, bg=NOTE_HEADER_BG, padx=18, pady=12)
        footer.pack(fill="x")
        self.open_button = self._make_button(
            footer,
            "打开目录",
            self._open_folder,
        )
        self.open_button.pack(side="left")
        self.copy_button = self._make_button(footer, "复制全部", self._copy)
        self.copy_button.pack(side="right", padx=(8, 0))
        self.save_button = self._make_button(footer, "保存修改", self._save)
        self.save_button.pack(side="right", padx=(8, 0))
        self.generate_button = self._make_button(
            footer,
            "生成学习包",
            self._generate,
            primary=True,
        )
        self.generate_button.pack(side="right")
        for button in (self.open_button, self.copy_button, self.save_button):
            button.configure(state="disabled")

        self.window.transient(root)
        self.window.lift()
        self.window.focus_force()

    def _make_button(self, parent, text, command, primary=False):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=NOTE_ACCENT if primary else NOTE_ACCENT_SOFT,
            fg=NOTE_PAPER_BG if primary else NOTE_ACCENT,
            activebackground=NOTE_ACCENT_ACTIVE if primary else NOTE_ACCENT_HOVER,
            activeforeground=NOTE_PAPER_BG if primary else NOTE_ACCENT_ACTIVE,
            disabledforeground=NOTE_MUTED_TEXT,
            relief="flat",
            bd=0,
            padx=14,
            pady=7,
            cursor="hand2",
            takefocus=True,
            font=("Microsoft YaHei UI", 9, "bold"),
        )

    def selected_entries(self):
        if self.scope_var.get() == "recent":
            return self.entries[-VOCABULARY_RECENT_LIMIT:]
        return self.entries[-VOCABULARY_MAX_ENTRIES:]

    def _generate(self):
        if str(self.generate_button.cget("state")) == "disabled":
            return
        self.generate_callback(self.selected_entries())

    def set_generating(self):
        self.status_var.set("正在整理单词，请稍候…")
        self.status_label.configure(fg=NOTE_WARNING_NOTE)
        self.generate_button.configure(state="disabled", text="正在生成")
        for button in self.scope_buttons:
            button.configure(state="disabled")

    def show_failure(self, message):
        self.status_var.set(message)
        self.status_label.configure(fg=NOTE_DANGER)
        self.generate_button.configure(state="normal", text="重新生成")
        for button in self.scope_buttons:
            button.configure(state="normal")

    def show_result(self, content, output_path):
        self.output_path = Path(output_path)
        self.result_text.configure(state="normal", fg=NOTE_TEXT)
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", content)
        self.result_text.edit_modified(False)
        self.status_var.set(f"已保存：{self.output_path.name}")
        self.status_label.configure(fg=NOTE_SUCCESS)
        self.generate_button.configure(state="normal", text="重新生成")
        for button in self.scope_buttons:
            button.configure(state="normal")
        for button in (self.open_button, self.copy_button, self.save_button):
            button.configure(state="normal")

    def _save(self):
        if self.output_path is None:
            return
        content = self.result_text.get("1.0", "end-1c")
        try:
            self.output_path = Path(self.save_callback(content, self.output_path))
        except OSError:
            self.status_var.set("保存失败，请检查文件是否被其他程序占用。")
            self.status_label.configure(fg=NOTE_DANGER)
            return
        self.result_text.edit_modified(False)
        self.status_var.set(f"已保存：{self.output_path.name}")
        self.status_label.configure(fg=NOTE_SUCCESS)

    def _copy(self):
        content = self.result_text.get("1.0", "end-1c")
        if not content.strip():
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.root.update_idletasks()
        self.status_var.set("已复制全部内容")
        self.status_label.configure(fg=NOTE_SUCCESS)

    def _open_folder(self):
        STUDIO_DIR.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(str(STUDIO_DIR))
        except OSError:
            self.status_var.set(f"成果目录：{STUDIO_DIR}")
            self.status_label.configure(fg=NOTE_MUTED_TEXT)

    def focus(self):
        try:
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
        except tk.TclError:
            pass

    def exists(self):
        try:
            return bool(self.window.winfo_exists())
        except tk.TclError:
            return False

    def close(self):
        if self.closed:
            return
        self.closed = True
        try:
            self.window.destroy()
        except tk.TclError:
            pass
        self.close_callback()


class ScreenCaptureOverlay:
    def __init__(self, root, on_complete):
        self.root = root
        self.on_complete = on_complete
        self.start_x = 0
        self.start_y = 0
        self.rect_id = None
        self.screen_x = 0
        self.screen_y = 0
        self.screen_width = 0
        self.screen_height = 0
        self.closed = False
        self.hud_items = []
        self.window = tk.Toplevel(root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.attributes("-alpha", OVERLAY_ALPHA)
        self.window.configure(bg="black")
        self.canvas = tk.Canvas(
            self.window,
            cursor="crosshair",
            bg="black",
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<ButtonPress-1>", self._start)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._finish)
        self.window.bind("<Escape>", lambda _event: self._cancel())

    def start(self):
        self.screen_x = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
        self.screen_y = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
        self.screen_width = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
        self.screen_height = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
        if self.screen_width <= 0 or self.screen_height <= 0:
            self.screen_width = self.root.winfo_screenwidth()
            self.screen_height = self.root.winfo_screenheight()
        geometry = (
            f"{self.screen_width}x{self.screen_height}"
            f"{self.screen_x:+d}{self.screen_y:+d}"
        )
        self.window.geometry(geometry)
        self.window.deiconify()
        self.window.update_idletasks()
        self.window.focus_force()
        self._draw_hud("框选英文区域", "拖动选择屏幕英文文本，再次按侧键或 Esc 取消。")

    def _start(self, event):
        self.start_x = event.x_root
        self.start_y = event.y_root
        self._clear_hud()
        self.rect_id = self.canvas.create_rectangle(
            event.x,
            event.y,
            event.x,
            event.y,
            outline=UI_OCR,
            width=2,
            dash=(6, 4),
        )

    def _drag(self, event):
        if self.rect_id is None:
            return
        x0 = self.start_x - self.window.winfo_rootx()
        y0 = self.start_y - self.window.winfo_rooty()
        self.canvas.coords(self.rect_id, x0, y0, event.x, event.y)

    def _finish(self, event):
        if self.closed:
            return

        x1 = event.x_root
        y1 = event.y_root
        left, right = sorted((self.start_x, x1))
        top, bottom = sorted((self.start_y, y1))

        if right - left < MIN_CAPTURE_SIZE or bottom - top < MIN_CAPTURE_SIZE:
            self._finish_without_capture("框选区域太小")
            return

        bbox = (left, top, right, bottom)
        self.closed = True
        self.window.withdraw()
        self.window.update_idletasks()
        self.root.after(
            CAPTURE_AFTER_OVERLAY_DELAY_MS,
            lambda: self._capture_bbox(bbox),
        )

    def _capture_bbox(self, bbox):
        try:
            TMP_DIR.mkdir(parents=True, exist_ok=True)
            image_path = TMP_DIR / f"capture-{int(time.time() * 1000)}.png"
            image = ImageGrab.grab(bbox=bbox, all_screens=True)
            image.save(image_path)
            self.on_complete(image_path, None)
        except Exception as exc:
            self.on_complete(None, f"截图失败：{exc}")
        finally:
            self._destroy_window()

    def cancel(self):
        self._finish_without_capture("已取消")

    def _cancel(self):
        self.cancel()

    def _finish_without_capture(self, message):
        if self.closed:
            return

        self.closed = True
        self._destroy_window()
        self.on_complete(None, message)

    def _destroy_window(self):
        try:
            if self.window.winfo_exists():
                self.window.destroy()
        except tk.TclError:
            pass

    def _draw_hud(self, title, detail):
        self._clear_hud()
        width = min(430, max(320, self.screen_width - 64))
        height = 70
        pointer = POINT()
        try:
            user32.GetCursorPos(ctypes.byref(pointer))
            work_area = monitor_work_area_for_point(
                pointer.x,
                pointer.y,
                self.screen_width,
                self.screen_height,
            )
        except Exception:
            work_area = (
                self.screen_x,
                self.screen_y,
                self.screen_x + self.screen_width,
                self.screen_y + self.screen_height,
            )
            pointer.x = self.screen_x + self.screen_width // 2
            pointer.y = self.screen_y + self.screen_height // 2
        left, top, right, bottom = work_area
        local_x, local_y = opposite_corner_position(
            right - left,
            bottom - top,
            width,
            height,
            pointer.x - left,
            pointer.y - top,
        )
        x0 = left - self.screen_x + local_x
        y0 = top - self.screen_y + local_y
        x1 = x0 + width
        y1 = y0 + height
        self.hud_items.extend(
            [
                self.canvas.create_rectangle(
                    x0,
                    y0,
                    x1,
                    y1,
                    fill=UI_HUD_PANEL,
                    outline=UI_HUD_PANEL,
                ),
                self.canvas.create_text(
                    x0 + 16,
                    y0 + 20,
                    text=title,
                    fill=UI_OCR,
                    anchor="w",
                    font=("Microsoft YaHei UI", 10, "bold"),
                ),
                self.canvas.create_text(
                    x0 + 16,
                    y0 + 48,
                    text=detail,
                    fill=UI_HUD_TEXT,
                    anchor="w",
                    font=("Microsoft YaHei UI", 9),
                ),
                self.canvas.create_text(
                    x1 - 18,
                    y0 + 20,
                    text="Esc",
                    fill=UI_HUD_MUTED,
                    anchor="e",
                    font=("Consolas", 9, "bold"),
                ),
            ]
        )

    def _clear_hud(self):
        for item in self.hud_items:
            self.canvas.delete(item)
        self.hud_items = []


class WindowsTrayIcon:
    def __init__(self, app):
        self.app = app
        self.root = app.root
        self.hwnd = None
        self.hicon = None
        self.added = False
        self.menu_open = False
        self.menu_pending = False
        self.current_menu = None
        self.wndproc = WindowProc(self._window_proc)
        self.thread = None
        self.ready = threading.Event()
        self.class_name = f"QuickSideNoteTrayWindow_{os.getpid()}_{id(self)}"
        self.taskbar_created_message = user32.RegisterWindowMessageW("TaskbarCreated")
        self.thread = threading.Thread(target=self._message_loop, daemon=True)
        self.thread.start()
        if not self.ready.wait(3) or not self.added:
            log("tray icon setup failed: message window was not ready")

    def _message_loop(self):
        try:
            hinstance = kernel32.GetModuleHandleW(None)
            wndclass = WNDCLASSEXW()
            wndclass.cbSize = ctypes.sizeof(WNDCLASSEXW)
            wndclass.style = 0
            wndclass.lpfnWndProc = self.wndproc
            wndclass.cbClsExtra = 0
            wndclass.cbWndExtra = 0
            wndclass.hInstance = hinstance
            wndclass.hIcon = None
            wndclass.hCursor = None
            wndclass.hbrBackground = None
            wndclass.lpszMenuName = None
            wndclass.lpszClassName = self.class_name
            wndclass.hIconSm = None
            if not user32.RegisterClassExW(ctypes.byref(wndclass)):
                log(f"tray window class registration failed: {kernel32.GetLastError()}")
                self.ready.set()
                return

            self.hwnd = user32.CreateWindowExW(
                0,
                self.class_name,
                APP_NAME,
                0,
                0,
                0,
                0,
                0,
                None,
                None,
                hinstance,
                None,
            )
            if not self.hwnd:
                log(f"tray message window creation failed: {kernel32.GetLastError()}")
                self.ready.set()
                return

            self._add_icon()
            self.ready.set()
            msg = wintypes.MSG()
            while True:
                result = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if result == 0:
                    break
                if result == -1:
                    log(f"tray message loop failed: {kernel32.GetLastError()}")
                    break
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        except Exception as exc:
            log(f"tray message loop crashed: {exc}")
            self.ready.set()
        finally:
            self._delete_icon()
            if self.hicon:
                user32.DestroyIcon(self.hicon)
                self.hicon = None
            self.hwnd = None

    def _load_icon(self):
        if ICON_FILE.exists():
            icon = user32.LoadImageW(
                None,
                str(ICON_FILE),
                IMAGE_ICON,
                0,
                0,
                LR_LOADFROMFILE | LR_DEFAULTSIZE,
            )
            if icon:
                return icon
        return None

    def _notify_data(self):
        data = NOTIFYICONDATAW()
        data.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        data.hWnd = self.hwnd
        data.uID = TRAY_ICON_ID
        data.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        data.uCallbackMessage = WM_TRAYICON
        data.hIcon = self.hicon
        data.szTip = APP_NAME
        return data

    def _add_icon(self):
        if not self.hwnd:
            return
        if self.hicon is None:
            self.hicon = self._load_icon()
        if not self.hicon:
            log("tray icon skipped: icon file could not be loaded")
            return
        data = self._notify_data()
        if shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(data)):
            self.added = True
            log("tray icon added")
        else:
            log("tray icon add failed")

    def _delete_icon(self):
        if not self.added:
            return
        data = self._notify_data()
        shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(data))
        self.added = False

    def _window_proc(self, hwnd, message, wparam, lparam):
        if message == WM_TRAYICON and int(wparam) == TRAY_ICON_ID:
            tray_event = int(lparam) & 0xFFFF
            if tray_event == WM_LBUTTONDBLCLK:
                self.app.events.put(("tray_toggle",))
                return 0
            if tray_event in {WM_RBUTTONUP, WM_CONTEXTMENU}:
                self.app.events.put(("tray_menu",))
                return 0
        if message == self.taskbar_created_message:
            self._delete_icon()
            self._add_icon()
            return 0
        if message == WM_CLOSE:
            self._delete_icon()
            user32.DestroyWindow(hwnd)
            return 0
        if message == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0
        return user32.DefWindowProcW(hwnd, message, wparam, lparam)

    def _queue_menu(self):
        if self.menu_open or self.menu_pending:
            return
        self.menu_pending = True
        self.root.after(50, self.show_menu)

    def show_menu(self):
        self.menu_pending = False
        if self.menu_open:
            if self.current_menu is not None:
                self._finish_menu(self.current_menu, destroy=True)
            return
        self.menu_open = True
        popup = None
        try:
            note_visible = self.app.visible and self.app.root.state() != "withdrawn"
            toggle_label = "隐藏便签" if note_visible else "显示便签"
            popup = tk.Toplevel(self.root)
            popup.withdraw()
            popup.overrideredirect(True)
            popup.attributes("-topmost", True)
            popup.configure(
                bg=NOTE_CARD_BG,
                highlightbackground=NOTE_BORDER,
                highlightcolor=NOTE_BORDER,
                highlightthickness=1,
            )
            self.current_menu = popup
            menu_body = tk.Frame(popup, bg=NOTE_CARD_BG, padx=8, pady=8)
            menu_body.pack(fill="both", expand=True)

            def add_menu_item(label, callback, shortcut="", danger=False):
                item = tk.Frame(menu_body, bg=NOTE_CARD_BG, cursor="hand2")
                item.pack(fill="x")
                fg = NOTE_DANGER if danger else NOTE_HEADER_TEXT
                hover_bg = NOTE_DANGER_SOFT if danger else NOTE_ACCENT_SOFTER
                left = tk.Label(
                    item,
                    text=label,
                    anchor="w",
                    bg=NOTE_CARD_BG,
                    fg=fg,
                    padx=12,
                    pady=8,
                    font=("Microsoft YaHei UI", 9),
                    cursor="hand2",
                )
                left.pack(side="left", fill="x", expand=True)
                right = tk.Label(
                    item,
                    text=shortcut,
                    anchor="e",
                    bg=NOTE_CARD_BG,
                    fg=NOTE_DANGER if danger else NOTE_MUTED_TEXT,
                    padx=12,
                    pady=8,
                    font=("Consolas", 9),
                    cursor="hand2",
                )
                right.pack(side="right")

                def set_item_bg(bg):
                    item.configure(bg=bg)
                    left.configure(bg=bg)
                    right.configure(bg=bg)

                for widget in (item, left, right):
                    widget.bind("<Enter>", lambda _event, bg=hover_bg: set_item_bg(bg))
                    widget.bind("<Leave>", lambda _event: set_item_bg(NOTE_CARD_BG))
                    widget.bind(
                        "<ButtonRelease-1>",
                        lambda _event: self._run_menu_command(popup, callback),
                    )

            add_menu_item(toggle_label, self.app.toggle_from_tray, "Enter")
            add_menu_item("整理单词", self.app.show_vocabulary_study_from_tray, "Ctrl+M")
            add_menu_item("设置", self.app.show_settings_from_tray, "Ctrl+,")
            tk.Frame(menu_body, height=1, bg=NOTE_DIVIDER).pack(fill="x", pady=4)
            add_menu_item("退出 Quick Side Note", self.app.quit_app, "Alt+F4", danger=True)
            popup.bind(
                "<Escape>",
                lambda _event: self._finish_menu(popup, destroy=True),
                add="+",
            )
            popup.bind(
                "<FocusOut>",
                lambda _event: popup.after(
                    120,
                    lambda: self._finish_menu(popup, destroy=True),
                ),
                add="+",
            )

            point = POINT()
            if user32.GetCursorPos(ctypes.byref(point)):
                x, y = point.x, point.y
            else:
                x, y = self.root.winfo_pointerx(), self.root.winfo_pointery()
            popup.update_idletasks()
            width = popup.winfo_reqwidth()
            height = popup.winfo_reqheight()
            left = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
            top = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
            right = left + user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
            bottom = top + user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
            x = min(max(x, left), right - width)
            if y + height > bottom:
                y = y - height
            y = min(max(y, top), bottom - height)
            popup.geometry(f"{width}x{height}+{x}+{y}")
            popup.deiconify()
            popup.lift()
            popup.focus_force()
            popup.after(15000, lambda: self._finish_menu(popup, destroy=True))
            log(f"tray tk popup menu shown at {x},{y}")
        except Exception as exc:
            log(f"tray menu failed: {exc}")
            if popup is not None:
                self._finish_menu(popup, destroy=True)
            else:
                self.menu_open = False

    def _run_menu_command(self, popup, callback):
        self._finish_menu(popup, destroy=True)
        self.root.after(0, callback)

    def _finish_menu(self, popup, destroy=False):
        if self.current_menu is not popup:
            return
        self.current_menu = None
        self.menu_open = False
        if not destroy:
            return
        try:
            if popup.winfo_exists():
                popup.destroy()
        except tk.TclError:
            pass

    def destroy(self):
        if self.current_menu is not None:
            self._finish_menu(self.current_menu, destroy=True)
        if self.hwnd:
            user32.PostMessageW(self.hwnd, WM_CLOSE, 0, 0)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        self._delete_icon()
        if self.hicon:
            user32.DestroyIcon(self.hicon)
            self.hicon = None


class QuickNoteApp:
    def __init__(self):
        NOTE_DIR.mkdir(parents=True, exist_ok=True)
        configure_dpi_awareness()
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        if ICON_FILE.exists():
            self.root.iconbitmap(ICON_FILE)
        state = read_state_data()
        self.settings = normalize_app_settings(state.get(SETTINGS_STATE_KEY))
        self.note_pages = normalize_note_pages(state.get("pages") or discover_note_pages())
        self.current_page = self._load_active_page()
        self.page_buttons = {}
        self.add_page_button = None
        self.page_title_label = None
        self.ocr_status_label = None
        self.autosave_label = None
        self.editor_size_label = None
        self.hide_button = None
        self.settings_button = None
        self.organize_button = None
        self.footer_hint_left = None
        self.footer_hint_right = None
        self.clear_undo_label = None
        self.tray_icon = None
        self.root.geometry(self._load_geometry())
        self.root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.root.overrideredirect(True)
        self.root.configure(bg=NOTE_BORDER)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_and_save)

        self.events = queue.Queue()
        self.mouse_hook = MouseSideButtonHook(self.events, lambda: self.settings)
        self.browser_key_hook = BrowserKeyHook(
            self.events,
            lambda: self.settings,
            lambda: self.ocr_active,
        )
        self.visible = True
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.resize_start_x = 0
        self.resize_start_y = 0
        self.resize_start_width = WINDOW_WIDTH
        self.resize_start_height = WINDOW_HEIGHT
        self.last_toggle_time = 0
        self.hook_check_ticks = 0
        self.pending_single_click = None
        self.ocr_active = False
        self.capture_overlay = None
        self.translation_task = None
        self.next_translation_task_id = 0
        self.vocabulary_dialog = None
        self.vocabulary_generation_id = 0
        self.active_vocabulary_generation_id = None
        self.task_hud = None
        self.task_restore_visible = False
        self.clear_undo_state = None
        self.clear_undo_after_id = None
        self.api_setup_after_id = None
        self.closing = False
        self.autosave_after_id = None
        self.backend = FastTranslationBackend(
            CodexCliBackend(),
            lambda: self.settings["allow_image_fallback"],
        )
        self.vocabulary_backend = VocabularyOrganizerBackend()
        self.note_store = NoteStore(NOTE_FILE, VOCABULARY_FILE)

        self._build_ui()
        self._load_note()
        self._bind_keys()
        self.text.bind("<<Modified>>", self._on_note_modified, add="+")
        self._set_autosave_status("已保存")
        self._poll_events()
        self.api_setup_after_id = self.root.after(250, self._ensure_api_setup)

    def run(self):
        log("app start")
        self._init_tray_icon()
        self.mouse_hook.start()
        self.browser_key_hook.start()
        if not self.mouse_hook.hook_id:
            pass
        try:
            self.root.mainloop()
        finally:
            self.closing = True
            self._cancel_translation_task(show_message=False)
            self._destroy_tray_icon()
            self.mouse_hook.stop()
            self.browser_key_hook.stop()
            self.mouse_hook.join()
            self.browser_key_hook.join()

    def _init_tray_icon(self):
        if sys.platform != "win32" or self.tray_icon is not None:
            return
        try:
            self.root.update_idletasks()
            self.tray_icon = WindowsTrayIcon(self)
        except Exception as exc:
            self.tray_icon = None
            log(f"tray icon setup failed: {exc}")

    def _destroy_tray_icon(self):
        if self.tray_icon is None:
            return
        try:
            self.tray_icon.destroy()
        except Exception as exc:
            log(f"tray icon cleanup failed: {exc}")
        self.tray_icon = None

    def _build_ui(self):
        shell = tk.Frame(self.root, bg=NOTE_BORDER, padx=8, pady=8)
        shell.pack(fill="both", expand=True, padx=1, pady=1)

        # --- 标题栏(暖色,可拖拽) ---
        header = tk.Frame(shell, bg=NOTE_HEADER_BG, height=40)
        header.pack(fill="x")
        header.pack_propagate(False)
        self._bind_move_handle(header)

        accent = tk.Frame(header, bg=NOTE_ACCENT, width=4)
        accent.pack(side="left", fill="y", padx=(0, 10))

        self.page_title_label = tk.Label(
            header,
            text="",
            bg=NOTE_HEADER_BG,
            fg=NOTE_HEADER_TEXT,
            bd=0,
            anchor="w",
            font=("Microsoft YaHei UI", 10, "bold"),
        )
        self.page_title_label.pack(side="left", fill="x", expand=True)
        self._bind_move_handle(self.page_title_label)

        self.hide_button = tk.Label(
            header,
            text="隐藏",
            bg=NOTE_HEADER_BG,
            fg=NOTE_MUTED_TEXT,
            bd=0,
            width=5,
            anchor="center",
            cursor="hand2",
            font=("Microsoft YaHei UI", 12),
        )
        self.hide_button.pack(side="right", fill="y")
        self.hide_button.bind("<Button-1>", lambda _event: self.hide_and_save())
        self.hide_button.bind("<Enter>", lambda _event: self._set_hide_hover(True))
        self.hide_button.bind("<Leave>", lambda _event: self._set_hide_hover(False))

        self.settings_button = tk.Label(
            header,
            text="设置",
            bg=NOTE_HEADER_BG,
            fg=NOTE_MUTED_TEXT,
            bd=0,
            width=5,
            anchor="center",
            cursor="hand2",
            font=("Microsoft YaHei UI", 9),
        )
        self.settings_button.pack(side="right", fill="y")
        self.settings_button.bind("<Button-1>", lambda _event: self._show_settings_dialog())
        self.settings_button.bind("<Enter>", lambda _event: self._set_settings_hover(True))
        self.settings_button.bind("<Leave>", lambda _event: self._set_settings_hover(False))

        self.organize_button = tk.Label(
            header,
            text="整理",
            bg=NOTE_HEADER_BG,
            fg=NOTE_ACCENT,
            bd=0,
            width=5,
            anchor="center",
            cursor="hand2",
            font=("Microsoft YaHei UI", 9, "bold"),
        )
        self.organize_button.pack(side="right", fill="y")
        self.organize_button.bind(
            "<Button-1>", lambda _event: self._show_vocabulary_study_dialog()
        )
        self.organize_button.bind(
            "<Enter>", lambda _event: self._set_organize_hover(True)
        )
        self.organize_button.bind(
            "<Leave>", lambda _event: self._set_organize_hover(False)
        )

        self.ocr_status_label = tk.Label(
            header,
            text="就绪",
            bg=NOTE_OCR_SOFT,
            fg=NOTE_OCR,
            bd=0,
            padx=6,
            pady=1,
            anchor="center",
            font=("Microsoft YaHei UI", 8, "bold"),
        )
        self.ocr_status_label.pack(side="right", padx=(0, 8), pady=8)

        # --- 顶部页签：可横向浏览，更多菜单始终保留入口 ---
        page_tab_bar = tk.Frame(shell, bg=NOTE_SHELL_BG, height=34)
        page_tab_bar.pack(fill="x", pady=(8, 6))
        page_tab_bar.pack_propagate(False)
        self.page_overflow_button = tk.Button(
            page_tab_bar,
            text="更多",
            command=self._show_page_overflow_menu,
            bg=NOTE_INACTIVE_PAGE_BG,
            fg=NOTE_INACTIVE_PAGE_FG,
            activebackground=NOTE_PAGE_HOVER_BG,
            activeforeground=NOTE_TEXT,
            relief="flat",
            bd=0,
            padx=8,
            pady=3,
            cursor="hand2",
            takefocus=True,
            font=("Microsoft YaHei UI", 8),
        )
        self.page_overflow_button.pack(side="right", pady=(0, 4))
        self.page_tab_canvas = tk.Canvas(
            page_tab_bar,
            bg=NOTE_SHELL_BG,
            bd=0,
            highlightthickness=0,
            height=30,
        )
        self.page_tab_canvas.pack(side="left", fill="both", expand=True)
        self.page_tabs = tk.Frame(self.page_tab_canvas, bg=NOTE_SHELL_BG)
        self.page_tab_window = self.page_tab_canvas.create_window(
            (0, 0),
            window=self.page_tabs,
            anchor="nw",
        )
        self.page_tabs.bind("<Configure>", self._sync_page_tab_region)
        self.page_tab_canvas.bind("<Configure>", self._sync_page_tab_region)
        self.page_tab_canvas.bind(
            "<Shift-MouseWheel>",
            lambda event: self.page_tab_canvas.xview_scroll(
                int(-event.delta / 120), "units"
            ),
        )
        self._rebuild_page_tabs()

        # --- 编辑器卡片(纸张质感) ---
        editor = tk.Frame(shell, bg=NOTE_PAPER_BORDER, padx=1, pady=1)
        editor.pack(fill="both", expand=True)

        editor_surface = tk.Frame(editor, bg=NOTE_PAPER_BG)
        editor_surface.pack(fill="both", expand=True)

        editor_meta = tk.Frame(editor_surface, bg=NOTE_PAPER_BG, height=26)
        editor_meta.pack(fill="x", padx=14, pady=(8, 0))
        editor_meta.pack_propagate(False)

        self.autosave_label = tk.Label(
            editor_meta,
            text="已保存",
            bg=NOTE_AUTOSAVE_BG,
            fg=NOTE_AUTOSAVE_FG,
            bd=0,
            padx=8,
            pady=2,
            anchor="center",
            font=("Microsoft YaHei UI", 8),
        )
        self.autosave_label.pack(side="left", pady=3)

        self.editor_size_label = tk.Label(
            editor_meta,
            text="",
            bg=NOTE_PAPER_BG,
            fg=NOTE_MUTED_TEXT,
            bd=0,
            anchor="e",
            font=("Consolas", 8),
        )
        self.editor_size_label.pack(side="right", fill="y")

        self.text = tk.Text(
            editor_surface,
            wrap="word",
            undo=True,
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=14,
            pady=10,
            font=("Microsoft YaHei UI", 10),
            bg=NOTE_PAPER_BG,
            fg=NOTE_TEXT,
            insertbackground=NOTE_INSERT,
            insertwidth=2,
            selectbackground=NOTE_SELECTION_BG,
            selectforeground=NOTE_SELECTION_FG,
            inactiveselectbackground=NOTE_SELECTION_BG,
            spacing1=2,
            spacing2=1,
            spacing3=6,
            tabs=("2c",),
        )
        self.text.pack(side="top", fill="both", expand=True, padx=14, pady=(2, 0))
        self.text.tag_config("placeholder", foreground=NOTE_MUTED_TEXT)
        # 翻译结果视觉区分 tag
        self.text.tag_config("src", foreground=NOTE_SRC_TAG)
        self.text.tag_config(
            "dst",
            foreground=NOTE_DST_TAG,
            font=("Microsoft YaHei UI", 10, "bold"),
        )

        # --- 底部操作栏(替代原静态提示) ---
        editor_footer = tk.Frame(editor_surface, bg=NOTE_FOOTER_BG, height=34)
        editor_footer.pack(side="bottom", fill="x", padx=14, pady=(4, 8))
        editor_footer.pack_propagate(False)

        self.footer_save_btn = tk.Label(
            editor_footer,
            text="保存",
            bg=NOTE_FOOTER_BG,
            fg=NOTE_MUTED_TEXT,
            bd=0,
            padx=8,
            pady=2,
            anchor="center",
            cursor="hand2",
            font=("Microsoft YaHei UI", 9),
        )
        self.footer_save_btn.pack(side="left", pady=4)
        self.footer_save_btn.bind("<Button-1>", lambda _event: self.save_note())
        self.footer_save_btn.bind("<Enter>", lambda _event: self._set_footer_btn_hover(self.footer_save_btn, True))
        self.footer_save_btn.bind("<Leave>", lambda _event: self._set_footer_btn_hover(self.footer_save_btn, False))

        self.footer_clear_btn = tk.Label(
            editor_footer,
            text="清空",
            bg=NOTE_FOOTER_BG,
            fg=NOTE_MUTED_TEXT,
            bd=0,
            padx=8,
            pady=2,
            anchor="center",
            cursor="hand2",
            font=("Microsoft YaHei UI", 9),
        )
        self.footer_clear_btn.pack(side="left", pady=4)
        self.footer_clear_btn.bind("<Button-1>", lambda _event: self._clear_note())
        self.footer_clear_btn.bind("<Enter>", lambda _event: self._set_footer_btn_hover(self.footer_clear_btn, True))
        self.footer_clear_btn.bind("<Leave>", lambda _event: self._set_footer_btn_hover(self.footer_clear_btn, False))

        self.footer_hide_btn = tk.Label(
            editor_footer,
            text="隐藏",
            bg=NOTE_FOOTER_BG,
            fg=NOTE_MUTED_TEXT,
            bd=0,
            padx=8,
            pady=2,
            anchor="center",
            cursor="hand2",
            font=("Microsoft YaHei UI", 9),
        )
        self.footer_hide_btn.pack(side="left", pady=4)
        self.footer_hide_btn.bind("<Button-1>", lambda _event: self.hide_and_save())
        self.footer_hide_btn.bind("<Enter>", lambda _event: self._set_footer_btn_hover(self.footer_hide_btn, True))
        self.footer_hide_btn.bind("<Leave>", lambda _event: self._set_footer_btn_hover(self.footer_hide_btn, False))

        # 快捷键小字提示(左)
        self.footer_hint_left = tk.Label(
            editor_footer,
            text="Ctrl+S · Ctrl+L · Esc",
            bg=NOTE_FOOTER_BG,
            fg=NOTE_FOOTER_HINT,
            bd=0,
            padx=8,
            pady=2,
            anchor="w",
            font=("Microsoft YaHei UI", 8),
        )
        self.footer_hint_left.pack(side="left", pady=4)

        self.footer_settings_btn = tk.Label(
            editor_footer,
            text="设置",
            bg=NOTE_FOOTER_BG,
            fg=NOTE_MUTED_TEXT,
            bd=0,
            padx=8,
            pady=2,
            anchor="center",
            cursor="hand2",
            font=("Microsoft YaHei UI", 9),
        )
        self.footer_settings_btn.pack(side="right", pady=4)
        self.footer_settings_btn.bind("<Button-1>", lambda _event: self._show_settings_dialog())
        self.footer_settings_btn.bind("<Enter>", lambda _event: self._set_footer_btn_hover(self.footer_settings_btn, True))
        self.footer_settings_btn.bind("<Leave>", lambda _event: self._set_footer_btn_hover(self.footer_settings_btn, False))

        # 右侧快捷键提示
        self.footer_hint_right = tk.Label(
            editor_footer,
            text="Ctrl+,",
            bg=NOTE_FOOTER_BG,
            fg=NOTE_FOOTER_HINT,
            bd=0,
            padx=8,
            pady=2,
            anchor="e",
            font=("Microsoft YaHei UI", 8),
        )
        self.footer_hint_right.pack(side="right", pady=4)

        self.clear_undo_label = tk.Label(
            editor_footer,
            text="撤销",
            bg=NOTE_FOOTER_BG,
            fg=NOTE_ACCENT,
            bd=0,
            padx=8,
            pady=2,
            cursor="hand2",
            takefocus=True,
            font=("Microsoft YaHei UI", 8, "bold"),
        )
        self.clear_undo_label.bind("<Button-1>", lambda _event: self._undo_clear_note())
        self.clear_undo_label.bind("<Return>", lambda _event: self._undo_clear_note())
        self.clear_undo_label.bind("<space>", lambda _event: self._undo_clear_note())

        for widget, command in (
            (self.hide_button, self.hide_and_save),
            (self.settings_button, self._show_settings_dialog),
            (self.organize_button, self._show_vocabulary_study_dialog),
            (self.footer_save_btn, self.save_note),
            (self.footer_clear_btn, self._clear_note),
            (self.footer_hide_btn, self.hide_and_save),
            (self.footer_settings_btn, self._show_settings_dialog),
        ):
            widget.configure(takefocus=True)
            widget.bind("<Return>", lambda _event, action=command: action())
            widget.bind("<space>", lambda _event, action=command: action())

        # Repack after every footer child exists so the editor takes only the remaining height.
        self.text.pack_forget()
        editor_footer.pack_forget()
        editor_footer.pack(side="bottom", fill="x", padx=14, pady=(4, 8))
        self.text.pack(side="top", fill="both", expand=True, padx=14, pady=(2, 0))

        self._update_page_buttons()
        self._update_window_size_label()
        self._update_footer_density()
        self.root.bind("<Configure>", self._on_root_configure, add="+")

        # --- 右下角拉伸手柄(暖色) ---
        self.resize_grip = tk.Canvas(
            shell,
            width=RESIZE_GRIP_SIZE,
            height=RESIZE_GRIP_SIZE,
            bg=NOTE_PAPER_BG,
            bd=0,
            highlightthickness=0,
            cursor="size_nw_se",
        )
        self.resize_grip.place(relx=1.0, rely=1.0, x=-5, y=-5, anchor="se")
        self.resize_grip.create_line(8, 17, 17, 8, fill=NOTE_RESIZE_GRIP, width=1)
        self.resize_grip.create_line(12, 17, 17, 12, fill=NOTE_RESIZE_GRIP, width=1)
        self.resize_grip.bind("<ButtonPress-1>", self._start_resize)
        self.resize_grip.bind("<B1-Motion>", self._resize_window)
        self.resize_grip.bind("<ButtonRelease-1>", self._finish_resize)

    def _bind_keys(self):
        self.root.bind("<Control-s>", lambda _event: self.save_note())
        self.root.bind("<Escape>", lambda _event: self.hide_and_save())
        self.root.bind("<FocusOut>", lambda _event: self.save_note())
        self.root.bind("<Control-l>", lambda _event: self._clear_note())
        self.root.bind("<Control-z>", self._undo_clear_note, add="+")
        self.root.bind("<F2>", lambda _event: self.rename_page(self.current_page))
        self.root.bind("<Control-k>", lambda _event: self._show_settings_dialog("api"))
        self.root.bind("<Control-comma>", lambda _event: self._show_settings_dialog())
        self.root.bind("<Control-m>", lambda _event: self._show_vocabulary_study_dialog())
        self.root.bind("<Control-Alt-n>", lambda _event: self.toggle_window())
        self.root.bind("<Control-q>", lambda _event: self.quit_app())
        self.root.bind_all("<Alt-ButtonPress-1>", self._start_move)
        self.root.bind_all("<Alt-B1-Motion>", self._move_window)
        self.root.bind_all("<Alt-ButtonRelease-1>", lambda _event: self._save_state())

    def _on_root_configure(self, event):
        if event.widget == self.root:
            self._update_window_size_label()
            self._update_footer_density()

    def _update_window_size_label(self):
        if self.editor_size_label is None:
            return
        width = max(self.root.winfo_width(), MIN_WINDOW_WIDTH)
        height = max(self.root.winfo_height(), MIN_WINDOW_HEIGHT)
        self.editor_size_label.configure(text=f"{width}×{height}")

    def _update_footer_density(self):
        if self.footer_hint_left is None or self.footer_hint_right is None:
            return
        if self.root.winfo_width() < 540:
            self.footer_hint_left.pack_forget()
            self.footer_hint_right.pack_forget()
        else:
            if not self.footer_hint_left.winfo_manager():
                self.footer_hint_left.pack(side="left", pady=4)
            if not self.footer_hint_right.winfo_manager():
                self.footer_hint_right.pack(side="right", pady=4)

    def _set_ocr_status(self, active=False, text=None):
        if self.ocr_status_label is None:
            return
        if active:
            self.ocr_status_label.configure(
                text=text or "处理中",
                bg=NOTE_WARNING_SOFT,
                fg=NOTE_WARNING,
            )
        else:
            self.ocr_status_label.configure(
                text=text or "就绪",
                bg=NOTE_OCR_SOFT,
                fg=NOTE_OCR,
            )

    def _bind_move_handle(self, widget):
        widget.bind("<ButtonPress-1>", self._start_move)
        widget.bind("<B1-Motion>", self._move_window)
        widget.bind("<ButtonRelease-1>", lambda _event: self._save_state())

    def _ensure_api_setup(self):
        self.api_setup_after_id = None
        if not is_deepseek_api_configured():
            self._show_settings_dialog("api", first_run=True)

    def _show_api_setup_dialog(self, first_run=False):
        self.root.deiconify()
        dialog = tk.Toplevel(self.root)
        dialog.title("配置翻译 API")
        dialog.resizable(True, True)
        dialog.attributes("-topmost", True)
        dialog.configure(bg=NOTE_HEADER_BG)
        dialog.transient(self.root)

        frame = tk.Frame(dialog, bg=NOTE_HEADER_BG, padx=18, pady=16)
        frame.pack(fill="both", expand=True)

        title_text = "首次运行设置" if first_run else "配置 DeepSeek API"
        title = tk.Label(
            frame,
            text=title_text,
            bg=NOTE_HEADER_BG,
            fg=NOTE_HEADER_TEXT,
            anchor="w",
            font=("Microsoft YaHei UI", 11, "bold"),
        )
        title.pack(fill="x")

        description = tk.Label(
            frame,
            text=(
                "请输入 DeepSeek API Key。保存后会写入当前 Windows 用户环境变量 "
                "DEEPSEEK_API_KEY，并立即用于翻译。"
            ),
            bg=NOTE_HEADER_BG,
            fg=NOTE_INACTIVE_PAGE_FG,
            justify="left",
            anchor="w",
            wraplength=380,
            font=("Microsoft YaHei UI", 9),
        )
        description.pack(fill="x", pady=(8, 10))

        key_var = tk.StringVar(value=get_user_environment_value("DEEPSEEK_API_KEY"))
        entry = tk.Entry(
            frame,
            textvariable=key_var,
            show="*",
            relief="solid",
            bd=1,
            width=46,
            font=("Consolas", 10),
            bg=NOTE_FIELD_BG,
            fg=NOTE_TEXT,
            insertbackground=NOTE_INSERT,
        )
        entry.pack(fill="x")

        status = tk.Label(
            frame,
            text="",
            bg=NOTE_HEADER_BG,
            fg=NOTE_DANGER,
            anchor="w",
            font=("Microsoft YaHei UI", 9),
        )
        status.pack(fill="x", pady=(8, 0))

        buttons = tk.Frame(frame, bg=NOTE_HEADER_BG)
        buttons.pack(fill="x", pady=(12, 0))

        def close_dialog():
            dialog.grab_release()
            dialog.destroy()

        def save_key():
            key = normalize_api_key(key_var.get())
            if not is_plausible_api_key(key):
                status.configure(text="API Key 看起来不完整，请检查后再保存。")
                return
            try:
                set_user_environment_value("DEEPSEEK_API_KEY", key)
            except Exception as exc:
                status.configure(text=f"保存失败：{exc}")
                log(f"DeepSeek API key save failed: {exc}")
                return

            log("DeepSeek API key configured")
            close_dialog()
            self._show_short_message("API 已配置")

        save_button = tk.Button(
            buttons,
            text="保存",
            command=save_key,
            bg=NOTE_ACCENT,
            fg="#ffffff",
            activebackground=NOTE_ACCENT,
            activeforeground="#ffffff",
            relief="flat",
            padx=14,
            pady=5,
            font=("Microsoft YaHei UI", 9),
        )
        save_button.pack(side="right")

        later_button = tk.Button(
            buttons,
            text="稍后再说",
            command=close_dialog,
            bg=NOTE_ACCENT_SOFT,
            fg=NOTE_ACCENT,
            activebackground=NOTE_ACCENT_HOVER,
            activeforeground=NOTE_ACCENT,
            relief="flat",
            padx=12,
            pady=5,
            font=("Microsoft YaHei UI", 9),
        )
        later_button.pack(side="right", padx=(0, 8))

        dialog.protocol("WM_DELETE_WINDOW", close_dialog)
        dialog.update_idletasks()
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_w = max(self.root.winfo_width(), WINDOW_WIDTH)
        root_h = max(self.root.winfo_height(), WINDOW_HEIGHT)
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = root_x + max(0, (root_w - width) // 2)
        y = root_y + max(0, (root_h - height) // 2)
        dialog.geometry(f"+{x}+{y}")
        dialog.grab_set()
        entry.focus_set()

    def _show_settings_dialog(self, initial_section="general", first_run=False):
        self.root.deiconify()
        dialog = tk.Toplevel(self.root)
        dialog.title("首次运行设置" if first_run else "设置")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)
        dialog.configure(bg=NOTE_DIALOG_BG)
        dialog.transient(self.root)

        dialog_width = 820
        dialog_height = 640
        dialog_min_width = 760
        dialog_min_height = 540
        section_key = initial_section if initial_section in {"api", "input", "startup", "about"} else "api"
        if first_run:
            section_key = "api"

        dialog.grid_columnconfigure(1, weight=1)
        dialog.grid_rowconfigure(0, weight=1)

        nav = tk.Frame(dialog, bg=NOTE_NAV_BG, width=188)
        nav.grid(row=0, column=0, sticky="ns")
        nav.grid_propagate(False)
        nav.grid_columnconfigure(0, weight=1)

        tk.Label(
            nav,
            text="Quick Note",
            bg=NOTE_NAV_BG,
            fg=NOTE_HEADER_TEXT,
            anchor="w",
            font=("Microsoft YaHei UI", 10, "bold"),
        ).grid(row=0, column=0, sticky="ew", padx=16, pady=(18, 2))
        tk.Label(
            nav,
            text=f"v{APP_VERSION}",
            bg=NOTE_NAV_BG,
            fg=NOTE_MUTED_TEXT,
            anchor="w",
            font=("Microsoft YaHei UI", 8),
        ).grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 14))

        right = tk.Frame(dialog, bg=NOTE_DIALOG_BG)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        header = tk.Frame(right, bg=NOTE_DIALOG_BG, padx=20, pady=12)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title_var = tk.StringVar(value="")
        subtitle_var = tk.StringVar(value="")
        tk.Label(
            header,
            textvariable=title_var,
            bg=NOTE_DIALOG_BG,
            fg=NOTE_HEADER_TEXT,
            anchor="w",
            font=("Microsoft YaHei UI", 15, "bold"),
        ).grid(row=0, column=0, sticky="ew")
        tk.Label(
            header,
            textvariable=subtitle_var,
            bg=NOTE_DIALOG_BG,
            fg=NOTE_MUTED_TEXT,
            anchor="w",
            justify="left",
            wraplength=540,
            font=("Microsoft YaHei UI", 9),
        ).grid(row=1, column=0, sticky="ew", pady=(5, 0))

        content = tk.Frame(
            right,
            bg=NOTE_SETTINGS_PANEL_BG,
            highlightthickness=1,
            highlightbackground=NOTE_DIVIDER,
            highlightcolor=NOTE_DIVIDER,
        )
        content.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 12))
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        tk.Frame(dialog, bg=NOTE_DIVIDER, height=1).grid(
            row=1, column=0, columnspan=2, sticky="ew"
        )
        footer = tk.Frame(dialog, bg=NOTE_DIALOG_BG, padx=20, pady=8)
        footer.grid(row=2, column=0, columnspan=2, sticky="ew")

        def make_button(parent, text, command, primary=False):
            if primary:
                bg = NOTE_ACCENT
                fg = "#ffffff"
                active_bg = NOTE_ACCENT_ACTIVE
                active_fg = "#ffffff"
            else:
                bg = NOTE_ACCENT_SOFT
                fg = NOTE_ACCENT
                active_bg = NOTE_ACCENT_HOVER
                active_fg = NOTE_ACCENT
            return tk.Button(
                parent,
                text=text,
                command=command,
                bg=bg,
                fg=fg,
                activebackground=active_bg,
                activeforeground=active_fg,
                relief="flat",
                bd=0,
                padx=16,
                pady=7,
                cursor="hand2",
                font=("Microsoft YaHei UI", 9),
            )

        def make_page():
            page = tk.Frame(content, bg=NOTE_SETTINGS_PANEL_BG, padx=20, pady=10)
            page.grid(row=0, column=0, sticky="nsew")
            page.grid_columnconfigure(0, weight=1)
            page.grid_remove()
            return page

        def make_scrollable(parent):
            parent.grid_rowconfigure(0, weight=1)
            parent.grid_columnconfigure(0, weight=1)
            canvas = tk.Canvas(
                parent,
                bg=NOTE_SETTINGS_PANEL_BG,
                bd=0,
                highlightthickness=0,
            )
            scrollbar = tk.Scrollbar(
                parent,
                orient="vertical",
                command=canvas.yview,
                bd=0,
                highlightthickness=0,
            )
            inner = tk.Frame(canvas, bg=NOTE_SETTINGS_PANEL_BG)
            inner_window = canvas.create_window((0, 0), window=inner, anchor="nw")

            def sync_width(event):
                canvas.itemconfigure(inner_window, width=event.width)
                canvas.configure(scrollregion=canvas.bbox("all"))

            def sync_region(_event=None):
                canvas.configure(scrollregion=canvas.bbox("all"))

            def on_wheel(event):
                canvas.yview_scroll(int(-event.delta / 120), "units")

            def bind_wheel(_event):
                canvas.bind_all("<MouseWheel>", on_wheel)

            def unbind_wheel(_event):
                canvas.unbind_all("<MouseWheel>")

            canvas.bind("<Configure>", sync_width)
            inner.bind("<Configure>", sync_region)
            canvas.bind("<Enter>", bind_wheel)
            canvas.bind("<Leave>", unbind_wheel)
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.grid(row=0, column=0, sticky="nsew")
            scrollbar.grid(row=0, column=1, sticky="ns", padx=(8, 0))
            inner.grid_columnconfigure(0, weight=1)
            return inner

        def make_section(parent, row, text, detail=None):
            tk.Label(
                parent,
                text=text,
                bg=NOTE_SETTINGS_PANEL_BG,
                fg=NOTE_HEADER_TEXT,
                anchor="w",
                font=("Microsoft YaHei UI", 10, "bold"),
            ).grid(row=row, column=0, sticky="ew", pady=(0, 2))
            if detail:
                tk.Label(
                    parent,
                    text=detail,
                    bg=NOTE_SETTINGS_PANEL_BG,
                    fg=NOTE_MUTED_TEXT,
                    anchor="w",
                    justify="left",
                    wraplength=480,
                    font=("Microsoft YaHei UI", 8),
                ).grid(row=row + 1, column=0, sticky="ew", pady=(0, 6))
                return row + 2
            return row + 1

        def make_check(parent, text, variable, command=None):
            return tk.Checkbutton(
                parent,
                text=text,
                variable=variable,
                command=command,
                bg=NOTE_SETTINGS_PANEL_BG,
                fg=NOTE_TEXT,
                activebackground=NOTE_SETTINGS_PANEL_BG,
                activeforeground=NOTE_TEXT,
                selectcolor=NOTE_SETTINGS_PANEL_BG,
                anchor="w",
                justify="left",
                wraplength=480,
                font=("Microsoft YaHei UI", 9),
            )

        def make_radio(parent, text, variable, value):
            return tk.Radiobutton(
                parent,
                text=text,
                value=value,
                variable=variable,
                bg=NOTE_SETTINGS_PANEL_BG,
                fg=NOTE_TEXT,
                activebackground=NOTE_SETTINGS_PANEL_BG,
                activeforeground=NOTE_TEXT,
                selectcolor=NOTE_SETTINGS_PANEL_BG,
                anchor="w",
                justify="left",
                wraplength=480,
                font=("Microsoft YaHei UI", 9),
            )

        def make_setting_card(parent, row, pady=(0, 8)):
            card = tk.Frame(
                parent,
                bg=NOTE_FIELD_BG,
                highlightthickness=1,
                highlightbackground=NOTE_PAPER_BORDER,
                highlightcolor=NOTE_ACCENT,
                padx=12,
                pady=10,
            )
            card.grid(row=row, column=0, sticky="ew", pady=pady)
            card.grid_columnconfigure(0, weight=1)
            return card

        def make_badge(parent, text, bg=NOTE_ACCENT_SOFT, fg=NOTE_ACCENT):
            return tk.Label(
                parent,
                text=text,
                bg=bg,
                fg=fg,
                bd=0,
                padx=8,
                pady=2,
                font=("Microsoft YaHei UI", 8, "bold"),
            )

        key_var = tk.StringVar(value=get_user_environment_value("DEEPSEEK_API_KEY"))
        show_key_var = tk.BooleanVar(value=False)
        startup_var = tk.BooleanVar(value=is_startup_enabled())
        startup_command = get_startup_registry_value()
        side_button_var = tk.StringVar(value=self.settings["side_button"])
        block_browser_var = tk.BooleanVar(value=self.settings["block_browser_key"])
        double_click_var = tk.IntVar(value=int(self.settings["double_click_ms"]))
        double_click_value_var = tk.StringVar(value=f"{double_click_var.get()} ms")
        side_response_var = tk.StringVar(value=self.settings["side_response_mode"])
        image_fallback_var = tk.BooleanVar(value=self.settings["allow_image_fallback"])
        api_status_var = tk.StringVar(
            value="已保存，尚未验证。" if key_var.get() else "未配置 API Key。"
        )
        status_var = tk.StringVar(value="")

        pages = {}
        nav_items = {}

        api_page = make_page()
        pages["api"] = api_page
        api_body = make_scrollable(api_page)
        row = make_section(
            api_body,
            0,
            "翻译 API",
            "配置 DeepSeek API Key。保存后立即用于 OCR 翻译。",
        )
        key_entry = tk.Entry(
            api_body,
            textvariable=key_var,
            show="*",
            relief="solid",
            bd=1,
            font=("Consolas", 10),
            bg=NOTE_FIELD_BG,
            fg=NOTE_TEXT,
            insertbackground=NOTE_INSERT,
        )
        key_entry.grid(row=row, column=0, sticky="ew", ipady=5)

        def update_key_visibility():
            key_entry.configure(show="" if show_key_var.get() else "*")

        show_key = make_check(api_body, "显示 API Key", show_key_var, update_key_visibility)
        show_key.grid(row=row + 1, column=0, sticky="w", pady=(10, 0))

        api_status = tk.Label(
            api_body,
            textvariable=api_status_var,
            bg=NOTE_SETTINGS_PANEL_BG,
            fg=NOTE_MUTED_TEXT,
            anchor="w",
            font=("Microsoft YaHei UI", 8),
        )
        api_status.grid(row=row + 2, column=0, sticky="ew", pady=(12, 0))

        def clear_api_key():
            if not key_var.get() and not get_user_environment_value("DEEPSEEK_API_KEY"):
                api_status_var.set("当前没有可清除的 API Key。")
                return
            confirmed = messagebox.askyesno(
                "清除 API Key",
                "清除后翻译将不可用，但本地便签不会删除。是否清除并保存？",
                parent=dialog,
            )
            if not confirmed:
                return
            key_var.set("")
            api_status_var.set("正在清除并保存 API Key。")
            api_status.configure(fg=NOTE_DANGER)
            save_settings()

        def test_api_connection():
            key = normalize_api_key(key_var.get())
            if not is_plausible_api_key(key):
                api_status_var.set("请先输入完整的 API Key，再测试连接。")
                api_status.configure(fg=NOTE_DANGER)
                return
            api_status_var.set("正在验证 API 连接…")
            api_status.configure(fg=NOTE_WARNING_NOTE)

            def run_test():
                ok, message = verify_deepseek_api_key(key)

                def update_result():
                    if not dialog.winfo_exists():
                        return
                    api_status_var.set(message)
                    api_status.configure(fg=NOTE_SUCCESS if ok else NOTE_DANGER)

                dialog.after(0, update_result)

            threading.Thread(
                target=run_test,
                daemon=True,
                name="QuickSideNote-ApiVerify",
            ).start()

        api_actions = tk.Frame(api_body, bg=NOTE_SETTINGS_PANEL_BG)
        api_actions.grid(row=row + 3, column=0, sticky="ew", pady=(16, 0))
        test_api_button = make_button(api_actions, "测试连接", test_api_connection)
        test_api_button.pack(side="left")
        clear_api_button = make_button(api_actions, "清除并保存", clear_api_key)
        clear_api_button.configure(bg=NOTE_DANGER_SOFT, fg=NOTE_DANGER)
        clear_api_button.pack(side="right")

        privacy_card = make_setting_card(api_body, row + 4, pady=(18, 0))
        tk.Label(
            privacy_card,
            text="图片兜底（可选）",
            bg=NOTE_FIELD_BG,
            fg=NOTE_TEXT,
            anchor="w",
            font=("Microsoft YaHei UI", 9, "bold"),
        ).grid(row=0, column=0, sticky="ew")
        tk.Label(
            privacy_card,
            text=(
                "默认关闭。本地 Windows OCR 失败时，开启后会把框选截图交给当前配置的 "
                "Codex CLI 服务商处理。"
            ),
            bg=NOTE_FIELD_BG,
            fg=NOTE_MUTED_TEXT,
            anchor="w",
            justify="left",
            wraplength=430,
            font=("Microsoft YaHei UI", 8),
        ).grid(row=1, column=0, sticky="ew", pady=(4, 0))
        make_check(
            privacy_card,
            "我理解图片可能被发送到外部服务，允许图片兜底",
            image_fallback_var,
        ).grid(row=2, column=0, sticky="w", pady=(10, 0))

        input_page = make_page()
        pages["input"] = input_page
        input_body = make_scrollable(input_page)
        input_row = make_section(
            input_body,
            0,
            "侧键",
            "选择用于框选识别的鼠标侧键。框选中再次按侧键或 Esc 可取消。",
        )
        side_button_badges = {}
        for index, (key, option) in enumerate(SIDE_BUTTON_OPTIONS.items()):
            card = make_setting_card(input_body, input_row)
            radio = tk.Radiobutton(
                card,
                text=option["label"],
                value=key,
                variable=side_button_var,
                bg=NOTE_FIELD_BG,
                fg=NOTE_TEXT,
                activebackground=NOTE_FIELD_BG,
                activeforeground=NOTE_TEXT,
                selectcolor=NOTE_FIELD_BG,
                anchor="w",
                font=("Microsoft YaHei UI", 9, "bold"),
            )
            radio.grid(row=0, column=0, sticky="w")
            tk.Label(
                card,
                text=option["detail"],
                bg=NOTE_FIELD_BG,
                fg=NOTE_MUTED_TEXT,
                anchor="w",
                font=("Microsoft YaHei UI", 8),
            ).grid(row=1, column=0, sticky="ew", padx=(24, 0), pady=(3, 0))
            badge_text = "当前" if key == side_button_var.get() else "备用"
            badge = make_badge(card, badge_text)
            badge.grid(row=0, column=1, rowspan=2, sticky="e")
            side_button_badges[key] = badge
            input_row += 1

        def update_side_button_badges(*_args):
            selected_key = side_button_var.get()
            for key, badge in side_button_badges.items():
                active = key == selected_key
                badge.configure(
                    text="当前" if active else "备用",
                    bg=NOTE_ACCENT_SOFT if active else NOTE_DISABLED_BG,
                    fg=NOTE_ACCENT if active else NOTE_MUTED_TEXT,
                )

        side_button_var.trace_add("write", update_side_button_badges)
        update_side_button_badges()

        tk.Frame(input_body, bg=NOTE_DIVIDER, height=1).grid(
            row=input_row, column=0, sticky="ew", pady=(6, 14)
        )
        input_row += 1

        input_row = make_section(
            input_body,
            input_row,
            "浏览器快捷键拦截",
            "选中的鼠标侧键始终由 Quick Side Note 使用；此选项只控制浏览器虚拟后退/前进键。",
        )
        block_card = make_setting_card(input_body, input_row)
        tk.Label(
            block_card,
            text="同时拦截浏览器后退/前进快捷键",
            bg=NOTE_FIELD_BG,
            fg=NOTE_TEXT,
            anchor="w",
            font=("Microsoft YaHei UI", 9, "bold"),
        ).grid(row=0, column=0, sticky="ew")
        block_status_var = tk.StringVar()

        def update_block_toggle():
            enabled = bool(block_browser_var.get())
            block_status_var.set(
                "已开启，同时拦截浏览器虚拟后退/前进键。"
                if enabled
                else "已关闭，不再处理浏览器虚拟后退/前进键。"
            )
            block_browser.configure(
                text="ON" if enabled else "OFF",
                bg=NOTE_OCR if enabled else NOTE_DISABLED_BG,
                fg="#ffffff" if enabled else NOTE_MUTED_TEXT,
                activebackground=NOTE_OCR if enabled else NOTE_DISABLED_BG,
                activeforeground="#ffffff" if enabled else NOTE_MUTED_TEXT,
            )

        tk.Label(
            block_card,
            textvariable=block_status_var,
            bg=NOTE_FIELD_BG,
            fg=NOTE_MUTED_TEXT,
            anchor="w",
            font=("Microsoft YaHei UI", 8),
        ).grid(row=1, column=0, sticky="ew", pady=(3, 0))
        block_browser = tk.Checkbutton(
            block_card,
            text="ON",
            variable=block_browser_var,
            command=update_block_toggle,
            indicatoron=False,
            relief="flat",
            bd=0,
            padx=12,
            pady=4,
            cursor="hand2",
            font=("Consolas", 8, "bold"),
        )
        block_browser.grid(row=0, column=1, rowspan=2, sticky="e")
        update_block_toggle()
        input_row += 1

        input_row = make_section(
            input_body,
            input_row,
            "双击判定间隔",
            "用于区分连续侧键触发与取消。当前实现范围为 150–900 ms。",
        )

        def update_double_click_label(_value=None):
            double_click_value_var.set(f"{int(double_click_var.get())} ms")

        delay_card = make_setting_card(input_body, input_row, pady=(0, 0))
        delay_row = tk.Frame(delay_card, bg=NOTE_FIELD_BG)
        delay_row.grid(row=0, column=0, sticky="ew")
        delay_row.grid_columnconfigure(0, weight=1)
        double_click_scale = tk.Scale(
            delay_row,
            from_=MIN_DOUBLE_CLICK_MS,
            to=MAX_DOUBLE_CLICK_MS,
            orient="horizontal",
            resolution=50,
            variable=double_click_var,
            command=update_double_click_label,
            showvalue=False,
            bg=NOTE_FIELD_BG,
            fg=NOTE_TEXT,
            activebackground=NOTE_ACCENT,
            highlightthickness=0,
            troughcolor=NOTE_DISABLED_BG,
        )
        double_click_scale.grid(row=0, column=0, sticky="ew")
        tk.Label(
            delay_row,
            textvariable=double_click_value_var,
            bg=NOTE_FIELD_BG,
            fg=NOTE_MUTED_TEXT,
            width=8,
            anchor="e",
            font=("Consolas", 9),
        ).grid(row=0, column=1, sticky="e", padx=(10, 0))
        tk.Label(
            delay_card,
            text="固定快捷键：Ctrl+S 保存，Esc 隐藏，Ctrl+L 清空，Ctrl+M 整理单词，Ctrl+K API，Ctrl+, 设置，Ctrl+Q 退出。",
            bg=NOTE_ACCENT_SOFTER,
            fg=NOTE_MUTED_TEXT,
            anchor="w",
            justify="left",
            wraplength=480,
            font=("Microsoft YaHei UI", 8),
            padx=10,
            pady=8,
        ).grid(row=1, column=0, sticky="ew", pady=(8, 0))

        input_row += 1
        input_row = make_section(
            input_body,
            input_row,
            "侧键响应模式",
            "兼容模式保留双击显示/隐藏；即时框选会在第一次按下时直接进入框选。",
        )
        response_card = make_setting_card(input_body, input_row, pady=(0, 0))
        make_radio(
            response_card,
            "兼容模式：单击框选，双击显示或隐藏便签",
            side_response_var,
            "compatibility",
        ).grid(row=0, column=0, sticky="w")
        make_radio(
            response_card,
            "即时框选：单击立即框选，窗口切换请使用托盘或 Ctrl+Alt+N",
            side_response_var,
            "immediate",
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))

        startup_page = make_page()
        pages["startup"] = startup_page
        startup_body = make_scrollable(startup_page)
        startup_row = make_section(
            startup_body,
            0,
            "开机启动",
            "保存时写入当前用户启动项，不需要管理员权限。",
        )

        startup_status_var = tk.StringVar(value="")
        startup_status = tk.Label(
            startup_body,
            textvariable=startup_status_var,
            bg=NOTE_SETTINGS_PANEL_BG,
            fg=NOTE_MUTED_TEXT,
            anchor="w",
            font=("Microsoft YaHei UI", 8),
        )

        def update_startup_status():
            if startup_var.get():
                startup_status_var.set("保存后将启用开机启动。")
                startup_status.configure(fg=NOTE_SUCCESS)
            elif startup_command:
                startup_status_var.set("保存后将取消当前开机启动项。")
                startup_status.configure(fg=NOTE_WARNING_NOTE)
            else:
                startup_status_var.set("当前未启用开机启动。")
                startup_status.configure(fg=NOTE_MUTED_TEXT)

        startup_check = make_check(
            startup_body,
            "登录 Windows 后自动启动 Quick Side Note",
            startup_var,
            update_startup_status,
        )
        startup_check.grid(row=startup_row, column=0, sticky="w")
        startup_status.grid(row=startup_row + 1, column=0, sticky="ew", pady=(12, 0))
        update_startup_status()

        about_page = make_page()
        pages["about"] = about_page
        about_body = make_scrollable(about_page)
        about_row = make_section(about_body, 0, f"Quick Side Note v{APP_VERSION}")
        tk.Label(
            about_body,
            text="轻量侧键便签工具：本地 OCR 识别屏幕文字，并调用 DeepSeek 完成翻译。",
            bg=NOTE_SETTINGS_PANEL_BG,
            fg=NOTE_TEXT,
            anchor="w",
            justify="left",
            wraplength=470,
            font=("Microsoft YaHei UI", 9),
        ).grid(row=about_row, column=0, sticky="ew", pady=(0, 10))
        tk.Label(
            about_body,
            text=f"数据目录：{NOTE_DIR}",
            bg=NOTE_SETTINGS_PANEL_BG,
            fg=NOTE_MUTED_TEXT,
            anchor="w",
            justify="left",
            wraplength=470,
            font=("Microsoft YaHei UI", 8),
        ).grid(row=about_row + 1, column=0, sticky="ew", pady=(0, 6))
        tk.Label(
            about_body,
            text=f"日志文件：{LOG_FILE}",
            bg=NOTE_SETTINGS_PANEL_BG,
            fg=NOTE_MUTED_TEXT,
            anchor="w",
            justify="left",
            wraplength=470,
            font=("Microsoft YaHei UI", 8),
        ).grid(row=about_row + 2, column=0, sticky="ew")

        section_meta = {
            "api": ("API", "翻译 API", "配置 DeepSeek API Key 后即可开始翻译。"),
            "input": ("输入", "侧键和快捷操作", "管理触发侧键、浏览器键拦截和双击间隔。"),
            "startup": ("开机启动", "开机启动", "控制登录 Windows 后是否自动启动 Quick Side Note。"),
            "about": ("关于", "关于此应用", "查看版本、数据目录和日志位置。"),
        }
        section_keys = tuple(section_meta)
        active_section_var = tk.StringVar(value="")

        def focus_nav(target, offset):
            index = section_keys.index(target)
            nav_items[section_keys[(index + offset) % len(section_keys)]].focus_set()
            return "break"

        def apply_nav_style(active_key):
            for key, widget in nav_items.items():
                active = key == active_key
                widget.configure(
                    bg=NOTE_NAV_ACTIVE_BG if active else NOTE_NAV_BG,
                    fg=NOTE_ACCENT if active else NOTE_INACTIVE_PAGE_FG,
                    font=("Microsoft YaHei UI", 9, "bold" if active else "normal"),
                )

        def switch_section(target):
            if target not in pages:
                target = "api"
            for key, page in pages.items():
                if key == target:
                    page.grid()
                else:
                    page.grid_remove()
            active_section_var.set(target)
            apply_nav_style(target)
            _nav_text, title_text, subtitle_text = section_meta[target]
            title_var.set(title_text)
            subtitle_var.set(subtitle_text)
            if target == "api":
                dialog.after(60, lambda: (key_entry.focus_set(), key_entry.icursor("end")))

        for index, (key, (nav_text, _title, _subtitle)) in enumerate(section_meta.items(), start=2):
            item = tk.Label(
                nav,
                text=nav_text,
                bg=NOTE_NAV_BG,
                fg=NOTE_INACTIVE_PAGE_FG,
                anchor="w",
                padx=14,
                pady=9,
                cursor="hand2",
                takefocus=True,
                font=("Microsoft YaHei UI", 9),
            )
            item.grid(row=index, column=0, sticky="ew", padx=8, pady=2)
            item.bind("<Button-1>", lambda _event, target=key: switch_section(target))
            item.bind("<Return>", lambda _event, target=key: switch_section(target))
            item.bind("<space>", lambda _event, target=key: switch_section(target))
            item.bind("<Up>", lambda _event, target=key: focus_nav(target, -1))
            item.bind("<Down>", lambda _event, target=key: focus_nav(target, 1))
            item.bind(
                "<Enter>",
                lambda _event, target=key, widget=item: widget.configure(
                    bg=NOTE_NAV_HOVER_BG
                    if active_section_var.get() != target
                    else NOTE_NAV_ACTIVE_BG
                ),
            )
            item.bind(
                "<Leave>",
                lambda _event, target=key, widget=item: widget.configure(
                    bg=NOTE_NAV_ACTIVE_BG
                    if active_section_var.get() == target
                    else NOTE_NAV_BG
                ),
            )
            nav_items[key] = item

        status = tk.Label(
            footer,
            textvariable=status_var,
            bg=NOTE_DIALOG_BG,
            fg=NOTE_DANGER,
            anchor="w",
            font=("Microsoft YaHei UI", 9),
        )
        status.pack(side="left", fill="x", expand=True)

        def close_dialog():
            try:
                dialog.grab_release()
            except tk.TclError:
                pass
            dialog.destroy()

        def save_settings():
            key = normalize_api_key(key_var.get())
            if key and not is_plausible_api_key(key):
                status_var.set("API Key 看起来不完整，请检查后再保存。")
                switch_section("api")
                return

            try:
                if key:
                    set_user_environment_value("DEEPSEEK_API_KEY", key)
                elif get_user_environment_value("DEEPSEEK_API_KEY"):
                    delete_user_environment_value("DEEPSEEK_API_KEY")

                set_startup_enabled(startup_var.get())
            except Exception as exc:
                status_var.set(f"保存失败：{exc}")
                log(f"settings save failed: {exc}")
                return

            self.settings = normalize_app_settings(
                {
                    "side_button": side_button_var.get(),
                    "block_browser_key": block_browser_var.get(),
                    "double_click_ms": double_click_var.get(),
                    "side_response_mode": side_response_var.get(),
                    "allow_image_fallback": image_fallback_var.get(),
                }
            )
            self._save_state()
            log(f"settings saved: {self.settings}")
            close_dialog()
            self._show_short_message("设置已保存")

        save_button = make_button(footer, "保存设置", save_settings, primary=True)
        save_button.pack(side="right", padx=(8, 0))

        cancel_text = "稍后再说" if first_run else "取消"
        cancel_button = make_button(footer, cancel_text, close_dialog)
        cancel_button.pack(side="right")

        dialog.protocol("WM_DELETE_WINDOW", close_dialog)
        dialog.bind("<Escape>", lambda _event: close_dialog())
        dialog.update_idletasks()
        pointer_x = self.root.winfo_pointerx()
        pointer_y = self.root.winfo_pointery()
        work_area = monitor_work_area_for_point(
            pointer_x,
            pointer_y,
            self.root.winfo_screenwidth(),
            self.root.winfo_screenheight(),
        )
        dialog_width, dialog_height, x, y = clamp_dialog_to_work_area(
            dialog_width,
            dialog_height,
            work_area,
        )
        dialog.minsize(
            min(dialog_min_width, dialog_width),
            min(dialog_min_height, dialog_height),
        )
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        dialog.grab_set()
        switch_section(section_key)

    def _rebuild_page_tabs(self):
        for child in self.page_tabs.winfo_children():
            child.destroy()
        self.page_buttons = {}

        for page in self.note_pages:
            page_id = page["id"]
            page_button = tk.Label(
                self.page_tabs,
                text=page["name"],
                bd=0,
                padx=PAGE_LABEL_PADDING_X,
                pady=4,
                anchor="center",
                font=PAGE_LABEL_FONT,
                cursor="hand2",
                takefocus=True,
            )
            page_button.pack(side="left", padx=(0, 4), pady=(0, 4))
            page_button.bind(
                "<Button-1>", lambda _event, target=page_id: self.switch_page(target)
            )
            page_button.bind(
                "<Double-Button-1>",
                lambda _event, target=page_id: self.rename_page(target),
            )
            page_button.bind(
                "<Return>", lambda _event, target=page_id: self.switch_page(target)
            )
            page_button.bind(
                "<space>", lambda _event, target=page_id: self.switch_page(target)
            )
            page_button.bind(
                "<F2>", lambda _event, target=page_id: self.rename_page(target)
            )
            page_button.bind(
                "<Left>", lambda _event, target=page_id: self._focus_page_tab(target, -1)
            )
            page_button.bind(
                "<Right>", lambda _event, target=page_id: self._focus_page_tab(target, 1)
            )
            page_button.bind(
                "<Enter>",
                lambda _event, target=page_id: self._set_page_hover(target, True),
            )
            page_button.bind(
                "<Leave>",
                lambda _event, target=page_id: self._set_page_hover(target, False),
            )
            self.page_buttons[page_id] = page_button

        add_button = tk.Label(
            self.page_tabs,
            text="+",
            bd=0,
            padx=PAGE_LABEL_PADDING_X,
            pady=4,
            anchor="center",
            font=PAGE_ADD_FONT,
            cursor="hand2",
            takefocus=True,
            bg=NOTE_INACTIVE_PAGE_BG,
            fg=NOTE_INACTIVE_PAGE_FG,
        )
        add_button.pack(side="left", padx=(4, 0), pady=(0, 4))
        add_button.bind("<Button-1>", lambda _event: self.create_page())
        add_button.bind("<Return>", lambda _event: self.create_page())
        add_button.bind("<space>", lambda _event: self.create_page())
        add_button.bind("<Enter>", lambda _event: self._set_add_hover(True))
        add_button.bind("<Leave>", lambda _event: self._set_add_hover(False))
        self.add_page_button = add_button
        self._update_page_buttons()
        self.root.after_idle(self._sync_page_tab_region)

    def _sync_page_tab_region(self, _event=None):
        if not getattr(self, "page_tab_canvas", None):
            return
        bbox = self.page_tab_canvas.bbox("all")
        if bbox:
            self.page_tab_canvas.configure(scrollregion=bbox)

    def _focus_page_tab(self, page, offset):
        page_ids = [item["id"] for item in self.note_pages]
        try:
            index = page_ids.index(page)
        except ValueError:
            return "break"
        target = page_ids[(index + offset) % len(page_ids)]
        button = self.page_buttons.get(target)
        if button is not None:
            button.focus_set()
            self.page_tab_canvas.xview_moveto(0)
        return "break"

    def _show_page_overflow_menu(self):
        menu = tk.Menu(
            self.root,
            tearoff=False,
            bg=NOTE_PAPER_BG,
            fg=NOTE_TEXT,
            activebackground=NOTE_ACCENT_SOFT,
            activeforeground=NOTE_ACCENT_ACTIVE,
        )
        for page in self.note_pages:
            marker = "* " if page["id"] == self.current_page else ""
            menu.add_command(
                label=f"{marker}{page['name']}",
                command=lambda target=page["id"]: self.switch_page(target),
            )
        menu.add_separator()
        menu.add_command(label="新建标签", command=self.create_page)
        menu.add_command(
            label="重命名当前标签",
            command=lambda: self.rename_page(self.current_page),
        )
        try:
            menu.tk_popup(
                self.page_overflow_button.winfo_rootx(),
                self.page_overflow_button.winfo_rooty()
                + self.page_overflow_button.winfo_height(),
            )
        finally:
            menu.grab_release()

    def switch_page(self, page):
        page = normalized_note_page(page, self.note_pages)
        if page == self.current_page:
            return

        self.save_note()
        self.current_page = page
        self._load_note()
        self._update_page_buttons()
        self._save_state()
        self.text.focus_set()

    def create_page(self):
        self.save_note()
        next_page_id = max(page["id"] for page in self.note_pages) + 1
        page_name = self._ask_page_name("新建标签", str(next_page_id))
        if page_name is None:
            return

        self.note_pages.append({"id": next_page_id, "name": page_name})
        self.current_page = next_page_id
        self._rebuild_page_tabs()
        self._load_note()
        self._save_state()
        self.text.focus_set()

    def rename_page(self, page):
        page = normalized_note_page(page, self.note_pages)
        current_name = self._page_name(page)
        page_name = self._ask_page_name("重命名标签", current_name)
        if page_name is None:
            return "break"

        for item in self.note_pages:
            if item["id"] == page:
                item["name"] = page_name
                break
        self._rebuild_page_tabs()
        self._save_state()
        return "break"

    def _ask_page_name(self, title, initial_value):
        name = simpledialog.askstring(
            title,
            "标签名字",
            initialvalue=initial_value,
            parent=self.root,
        )
        if name is None:
            return None
        return normalize_page_name(name, initial_value)

    def _page_name(self, page):
        page = normalized_note_page(page, self.note_pages)
        for item in self.note_pages:
            if item["id"] == page:
                return item["name"]
        return str(page)

    def _update_page_buttons(self):
        for page, button in self.page_buttons.items():
            self._apply_page_button_style(page, button)
        if self.add_page_button is not None:
            self._apply_add_button_style(False)
        if self.page_title_label is not None:
            # 显示当前页名,而非写死 "Quick Note"
            self.page_title_label.configure(text=self._page_name(self.current_page))

    def _apply_page_button_style(self, page, button, hover=False):
        active = page == self.current_page
        if active:
            bg = NOTE_ACTIVE_PAGE_BG
            fg = NOTE_ACTIVE_PAGE_FG
        elif hover:
            bg = NOTE_PAGE_HOVER_BG
            fg = NOTE_TEXT
        else:
            bg = NOTE_INACTIVE_PAGE_BG
            fg = NOTE_INACTIVE_PAGE_FG

        button.configure(bg=bg, fg=fg)

    def _set_page_hover(self, page, hover):
        button = self.page_buttons.get(page)
        if button is not None:
            self._apply_page_button_style(page, button, hover)

    def _apply_add_button_style(self, hover):
        bg = NOTE_PAGE_HOVER_BG if hover else NOTE_INACTIVE_PAGE_BG
        fg = NOTE_ACCENT if hover else NOTE_INACTIVE_PAGE_FG
        self.add_page_button.configure(bg=bg, fg=fg)

    def _set_add_hover(self, hover):
        if self.add_page_button is not None:
            self._apply_add_button_style(hover)

    def _set_hide_hover(self, hover):
        if self.hide_button is None:
            return
        bg = NOTE_CLOSE_HOVER_BG if hover else NOTE_HEADER_BG
        fg = NOTE_CLOSE_HOVER_FG if hover else NOTE_MUTED_TEXT
        self.hide_button.configure(bg=bg, fg=fg)

    def _set_settings_hover(self, hover):
        if self.settings_button is None:
            return
        bg = NOTE_HEADER_BUTTON_HOVER if hover else NOTE_HEADER_BG
        fg = NOTE_TEXT if hover else NOTE_MUTED_TEXT
        self.settings_button.configure(bg=bg, fg=fg)

    def _set_organize_hover(self, hover):
        if self.organize_button is None:
            return
        bg = NOTE_ACCENT_SOFT if hover else NOTE_HEADER_BG
        fg = NOTE_ACCENT_ACTIVE if hover else NOTE_ACCENT
        self.organize_button.configure(bg=bg, fg=fg)

    def _set_footer_btn_hover(self, btn, hover):
        """底部操作栏按钮的 hover 反馈(暖色)。"""
        if btn is None:
            return
        fg = NOTE_ACCENT if hover else NOTE_MUTED_TEXT
        btn.configure(fg=fg)

    def _poll_events(self):
        if getattr(self, "closing", False):
            return
        self.hook_check_ticks += 1
        if self.hook_check_ticks >= 20:
            self.hook_check_ticks = 0
            if not self.mouse_hook.is_alive():
                self.mouse_hook.start()
            if not self.browser_key_hook.is_alive():
                self.browser_key_hook.start()

        while True:
            try:
                event = self.events.get_nowait()
            except queue.Empty:
                break

            if event[0] == "toggle":
                now = time.monotonic()
                if now - self.last_toggle_time >= EVENT_DEBOUNCE_SECONDS:
                    self.last_toggle_time = now
                    self._handle_side_click(event[1], event[2])
            elif event[0] == "cancel_task":
                self._cancel_active_task()
            elif event[0] == "tray_toggle":
                self.toggle_from_tray()
            elif event[0] == "tray_menu" and self.tray_icon is not None:
                self.tray_icon._queue_menu()
            elif event[0] == "translation_done":
                self._finish_ocr_translation(*event[1:])
            elif event[0] == "translation_progress":
                self._update_translation_progress(*event[1:])
            elif event[0] == "vocabulary_done":
                self._finish_vocabulary_generation(*event[1:])

        if not self.closing:
            self.root.after(60, self._poll_events)

    def _handle_side_click(self, pointer_x, pointer_y):
        if self.ocr_active:
            if self.pending_single_click is not None:
                self.root.after_cancel(self.pending_single_click)
                self.pending_single_click = None
            if self.capture_overlay is not None:
                log("side click cancels OCR selection")
                self.capture_overlay.cancel()
            else:
                self._cancel_translation_task()
            return

        if self.settings["side_response_mode"] == "immediate":
            self.start_ocr_selection()
            return

        if self.pending_single_click is not None:
            self.root.after_cancel(self.pending_single_click)
            self.pending_single_click = None
            hide_hud = getattr(self, "_hide_task_hud", None)
            if callable(hide_hud):
                hide_hud()
            self.toggle_window(pointer_x, pointer_y)
            return

        show_hud = getattr(self, "_show_task_hud", None)
        if callable(show_hud):
            show_hud(
                "准备框选",
                "再次按侧键可显示或隐藏便签。",
                cancellable=False,
            )
        self.pending_single_click = self.root.after(
            self.settings["double_click_ms"],
            lambda: self._run_single_click_ocr(pointer_x, pointer_y),
        )

    def _run_single_click_ocr(self, _pointer_x=None, _pointer_y=None):
        self.pending_single_click = None
        self.start_ocr_selection()

    def toggle_window(self, pointer_x=None, pointer_y=None):
        if self.visible and self.root.state() != "withdrawn" and self._should_hide_on_toggle():
            log("toggle: visible note, hide")
            self.hide_and_save()
            return

        log("toggle: show note")
        self.show_window(pointer_x, pointer_y)

    def show_window(self, pointer_x=None, pointer_y=None):
        self.visible = True
        if pointer_x is None:
            pointer_x = self.root.winfo_pointerx()
        if pointer_y is None:
            pointer_y = self.root.winfo_pointery()
        if pointer_x is not None and pointer_y is not None:
            self._move_near_pointer(pointer_x, pointer_y)
        self.root.deiconify()
        self._force_window_to_front()
        self.text.focus_set()
        self.text.mark_set("insert", "end-1c")
        self.text.see("insert")

    def show_window_from_tray(self):
        self.visible = True
        self.root.deiconify()
        self._force_window_to_front()
        self.text.focus_set()
        self.text.mark_set("insert", "end-1c")
        self.text.see("insert")

    def toggle_from_tray(self):
        if self.visible and self.root.state() != "withdrawn":
            log("tray toggle: visible note, hide")
            self.hide_and_save()
            return

        log("tray toggle: show note")
        self.show_window_from_tray()

    def show_settings_from_tray(self):
        if not self.visible or self.root.state() == "withdrawn":
            self.show_window_from_tray()
        self._show_settings_dialog()

    def show_vocabulary_study_from_tray(self):
        if not self.visible or self.root.state() == "withdrawn":
            self.show_window_from_tray()
        self._show_vocabulary_study_dialog()

    def _wordbook_page_id(self):
        for page in self.note_pages:
            if "单词" in str(page.get("name") or ""):
                return int(page["id"])
        return self.current_page

    def _show_vocabulary_study_dialog(self):
        if self.vocabulary_dialog is not None and self.vocabulary_dialog.exists():
            self.vocabulary_dialog.focus()
            return

        try:
            self.save_note()
        except OSError:
            self._show_short_message("便签保存失败，暂时无法整理单词")
            return

        wordbook_path = note_file_for_page(self._wordbook_page_id())
        entries = collect_vocabulary_entries(
            note_paths=(wordbook_path,),
            vocabulary_path=VOCABULARY_FILE,
        )
        if not entries:
            self._show_short_message("单词本中还没有可整理的英文单词")
            return

        self.vocabulary_dialog = VocabularyStudyDialog(
            self.root,
            entries,
            self._start_vocabulary_generation,
            self._save_vocabulary_result,
            self._close_vocabulary_study_dialog,
        )

    def _start_vocabulary_generation(self, entries):
        if self.active_vocabulary_generation_id is not None:
            return
        if self.vocabulary_dialog is None or not self.vocabulary_dialog.exists():
            return

        self.vocabulary_generation_id += 1
        generation_id = self.vocabulary_generation_id
        self.active_vocabulary_generation_id = generation_id
        self.vocabulary_dialog.set_generating()
        thread = threading.Thread(
            target=self._vocabulary_generation_worker,
            args=(generation_id, tuple(entries)),
            daemon=True,
            name=f"QuickSideNote-Vocabulary-{generation_id}",
        )
        thread.start()

    def _vocabulary_generation_worker(self, generation_id, entries):
        output = None
        error = None
        started = time.perf_counter()
        try:
            output = self.vocabulary_backend.generate(entries)
        except Exception as exc:
            error = str(exc)
            log(f"vocabulary generation failed: {type(exc).__name__}")
        else:
            log(
                "vocabulary generation completed "
                f"entry_count={len(entries)} elapsed={time.perf_counter() - started:.2f}s"
            )
        self.events.put(("vocabulary_done", generation_id, output, error))

    def _finish_vocabulary_generation(self, generation_id, output, error):
        if self.active_vocabulary_generation_id != generation_id:
            log("discarded stale vocabulary generation result")
            return
        self.active_vocabulary_generation_id = None
        dialog = self.vocabulary_dialog
        if dialog is None or not dialog.exists():
            return
        if error:
            dialog.show_failure(error)
            return
        try:
            output_path = save_studio_output(output)
        except OSError:
            dialog.show_failure("学习包已生成，但保存文件失败。")
            return
        dialog.show_result(output.content, output_path)

    def _save_vocabulary_result(self, content, output_path):
        output_path = Path(output_path)
        atomic_write_text(output_path, str(content).rstrip() + "\n")
        return output_path

    def _close_vocabulary_study_dialog(self):
        self.active_vocabulary_generation_id = None
        self.vocabulary_dialog = None

    def quit_app(self):
        log("quit app")
        self.closing = True
        if self.pending_single_click is not None:
            self.root.after_cancel(self.pending_single_click)
            self.pending_single_click = None
        self._cancel_autosave()
        if self.api_setup_after_id is not None:
            try:
                self.root.after_cancel(self.api_setup_after_id)
            except tk.TclError:
                pass
            self.api_setup_after_id = None
        self._cancel_translation_task(show_message=False)
        if self.vocabulary_dialog is not None:
            self.vocabulary_dialog.close()
        if self.task_hud is not None:
            self.task_hud.destroy()
        try:
            self.save_note()
        except Exception as exc:
            log(f"save on quit failed: {exc}")
        self._destroy_tray_icon()
        self.root.destroy()

    def hide_and_save(self):
        log("hide note")
        self.save_note()
        self.visible = False
        self.root.attributes("-topmost", False)
        self._release_topmost()
        self.root.withdraw()

    def _set_autosave_status(self, text, color=None):
        if getattr(self, "autosave_label", None) is None:
            return
        self.autosave_label.configure(
            text=text,
            fg=color if color is not None else NOTE_AUTOSAVE_FG,
        )

    def _cancel_autosave(self):
        if getattr(self, "autosave_after_id", None) is None:
            return
        try:
            self.root.after_cancel(self.autosave_after_id)
        except tk.TclError:
            pass
        self.autosave_after_id = None

    def _on_note_modified(self, _event=None):
        try:
            if not self.text.edit_modified():
                return
            self.text.edit_modified(False)
        except tk.TclError:
            return
        if self.clear_undo_state and not self._is_placeholder_active():
            self._dismiss_clear_undo()
        if self._is_placeholder_active() or getattr(self, "closing", False):
            return
        self._set_autosave_status("未保存", NOTE_WARNING_NOTE)
        self._cancel_autosave()
        self.autosave_after_id = self.root.after(
            AUTOSAVE_DELAY_MS,
            self._autosave_current_note,
        )

    def _autosave_current_note(self):
        self.autosave_after_id = None
        if getattr(self, "closing", False):
            return
        self._set_autosave_status("保存中", NOTE_MUTED_TEXT)
        try:
            self.save_note()
        except OSError:
            log("autosave failed")

    def save_note(self):
        self._cancel_autosave()
        content = "" if self._is_placeholder_active() else self.text.get("1.0", "end-1c")
        if self.clear_undo_state and self.clear_undo_state["page"] == self.current_page:
            self._dismiss_clear_undo()
        try:
            atomic_write_text(note_file_for_page(self.current_page), content)
            self._save_state()
        except OSError:
            self._set_autosave_status("保存失败", NOTE_DANGER)
            raise
        self._set_autosave_status("已保存", NOTE_SUCCESS)

    def start_ocr_selection(self):
        if self.ocr_active:
            log("OCR selection already active")
            return

        self.task_restore_visible = self.visible and self.root.state() != "withdrawn"
        self.ocr_active = True
        self._set_ocr_status(True, "准备框选")
        self._hide_task_hud()
        self.hide_and_save()
        overlay = ScreenCaptureOverlay(self.root, self._on_capture_complete)
        self.capture_overlay = overlay
        try:
            overlay.start()
            self._set_ocr_status(True, "框选中")
        except Exception as exc:
            self.ocr_active = False
            update_ocr_status_if_available(self, False)
            self.capture_overlay = None
            log(f"OCR overlay failed: {exc}")
            self._show_task_failure(f"框选启动失败：{exc}")

    def _on_capture_complete(self, image_path, error):
        self.capture_overlay = None
        if getattr(self, "closing", False):
            if image_path:
                Path(image_path).unlink(missing_ok=True)
            return
        if error:
            self.ocr_active = False
            update_ocr_status_if_available(self, False)
            log(error)
            if error == "已取消":
                show_cancelled = getattr(self, "_show_task_cancelled", None)
                if callable(show_cancelled):
                    show_cancelled("已取消框选")
                else:
                    self._show_short_message("已取消框选")
            else:
                show_failure = getattr(self, "_show_task_failure", None)
                if callable(show_failure):
                    show_failure(error)
                else:
                    self._show_short_message(error)
            return

        self.next_translation_task_id += 1
        task = TranslationTask(self.next_translation_task_id, Path(image_path))
        self.translation_task = task
        self._set_ocr_status(True, "正在识别")
        self._show_task_hud("正在识别", "正在读取框选内容…")
        task.timeout_after_id = self.root.after(
            TRANSLATION_TASK_TIMEOUT_SECONDS * 1000,
            lambda task_id=task.task_id: self._expire_translation_task(task_id),
        )
        thread = threading.Thread(
            target=self._translate_capture_worker,
            args=(task,),
            daemon=True,
            name=f"QuickSideNote-Translate-{task.task_id}",
        )
        thread.start()

    def _translate_capture_worker(self, task):
        result = None
        error = None
        try:
            if not task.cancelled.is_set():
                if isinstance(self.backend, FastTranslationBackend):
                    result = self.backend.translate_image(
                        task.image_path,
                        progress_callback=lambda stage: self.events.put(
                            ("translation_progress", task.task_id, stage)
                        ),
                    )
                else:
                    result = self.backend.translate_image(task.image_path)
        except Exception as exc:
            error = str(exc)
            log(f"ocr translate failed: {type(exc).__name__}")
        finally:
            try:
                task.image_path.unlink(missing_ok=True)
            except OSError as exc:
                log(f"failed to delete temp capture: {type(exc).__name__}")

        self.events.put(
            ("translation_done", task.task_id, result, error, task.cancelled.is_set())
        )

    def _update_translation_progress(self, task_id, stage):
        task = self.translation_task
        if task is None or task.task_id != task_id:
            return
        if stage == "translating":
            self._set_ocr_status(True, "正在翻译")
            self._show_task_hud("正在翻译", "正在生成简明中文释义…")
        else:
            self._set_ocr_status(True, "正在识别")
            self._show_task_hud("正在识别", "正在读取框选内容…")

    def _finish_ocr_translation(self, task_id, result, error, cancelled=False):
        task = self.translation_task
        if task is None or task.task_id != task_id:
            log("discarded stale translation result")
            return
        if task.timeout_after_id is not None:
            self.root.after_cancel(task.timeout_after_id)
        self.translation_task = None
        self.ocr_active = False
        update_ocr_status_if_available(self, False)
        if cancelled:
            self._show_task_cancelled("已取消翻译")
            return
        if error:
            self._show_task_failure(error)
            return

        self.append_translation_result(result)
        self.note_store.append_vocabulary(result)
        self.show_window()
        self._show_task_hud("已完成", "识别结果已写入当前便签。", cancellable=False)
        self.root.after(900, self._hide_task_hud)

    def _cancel_translation_task(self, show_message=True):
        task = self.translation_task
        if task is None:
            return False
        task.cancelled.set()
        if task.timeout_after_id is not None:
            try:
                self.root.after_cancel(task.timeout_after_id)
            except tk.TclError:
                pass
        self.translation_task = None
        self.ocr_active = False
        update_ocr_status_if_available(self, False)
        if show_message and not self.closing:
            self._show_task_cancelled("已取消翻译")
        log("translation task cancelled")
        return True

    def _expire_translation_task(self, task_id):
        task = self.translation_task
        if task is not None and task.task_id == task_id:
            self._cancel_translation_task(show_message=False)
            self._show_task_failure("翻译超时。请检查网络或 API 配置后重新框选。")

    def _cancel_active_task(self):
        if self.capture_overlay is not None:
            self.capture_overlay.cancel()
            return True
        return self._cancel_translation_task()

    def _show_task_hud(self, title, detail, cancellable=True):
        if self.task_hud is None:
            self.task_hud = TaskProgressHud(self.root, self._cancel_active_task)
        self.task_hud.show_status(title, detail, cancellable=cancellable)

    def _hide_task_hud(self):
        if self.task_hud is not None:
            self.task_hud.hide()

    def _show_task_cancelled(self, message):
        self._restore_window_after_task()
        self._show_task_hud("任务已取消", message, cancellable=False)
        self.root.after(1000, self._hide_task_hud)

    def _show_task_failure(self, message):
        self._restore_window_after_task()
        if self.task_hud is None:
            self.task_hud = TaskProgressHud(self.root, self._cancel_active_task)
        self.task_hud.show_failure(
            message,
            self.start_ocr_selection,
            self._return_to_note_after_task,
        )

    def _restore_window_after_task(self):
        if self.task_restore_visible:
            self.show_window_from_tray()
        self.task_restore_visible = False

    def _return_to_note_after_task(self):
        self._hide_task_hud()
        self.show_window_from_tray()

    def append_translation_result(self, result):
        self._remove_placeholder()
        current = self.text.get("1.0", "end-1c")
        if current.strip():
            self.text.insert("end", "\n\n")

        # 原文/译文分别着色,存储格式不变(向后兼容)
        self.text.insert("end", f"原文：{result.source_text}\n", ("src",))
        self.text.insert("end", f"译文：{result.translation}\n", ("dst",))
        self.text.see("end")
        self.save_note()

    def _show_short_message(self, message):
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        label = tk.Label(
            toast,
            text=message,
            bg=NOTE_TOAST_BG,
            fg=NOTE_TOAST_FG,
            padx=12,
            pady=7,
            font=("Microsoft YaHei UI", 10),
        )
        label.pack()
        x = self.root.winfo_pointerx() + 12
        y = self.root.winfo_pointery() + 12
        toast.geometry(f"+{x}+{y}")
        toast.after(1800, toast.destroy)

    def _load_note(self):
        self.text.delete("1.0", "end")
        self.text.tag_remove("placeholder", "1.0", "end")
        note_file = note_file_for_page(self.current_page)
        if note_file.exists():
            try:
                content, recovered = read_text_with_backup(note_file)
            except (OSError, UnicodeDecodeError):
                log("note could not be read")
                self._show_short_message("便签无法读取，原文件已保留")
                self._insert_placeholder()
                return
            if recovered:
                log("note recovered from backup")
            if content:
                self.text.insert("1.0", content)
                self._apply_translation_tags()
                self.text.edit_modified(False)
                return

        self._insert_placeholder()
        self.text.edit_modified(False)

    def _apply_translation_tags(self):
        """扫描已加载的笔记文本,为 原文：/译文： 行回填 src/dst tag。"""
        self.text.tag_remove("src", "1.0", "end")
        self.text.tag_remove("dst", "1.0", "end")
        start = "1.0"
        while True:
            line_start = self.text.search(
                "原文：", start, stopindex="end", regexp=False
            )
            if not line_start:
                break
            line_end = f"{line_start} lineend"
            self.text.tag_add("src", line_start, line_end)
            # 下一行通常是译文
            dst_line = f"{line_start} +1l"
            dst_end = f"{dst_line} lineend"
            dst_text = self.text.get(dst_line, dst_end)
            if dst_text.startswith("译文："):
                self.text.tag_add("dst", dst_line, dst_end)
                start = f"{dst_end} +1c"
            else:
                start = f"{line_end} +1c"

    def _insert_placeholder(self):
        self.text.insert("1.0", PLACEHOLDER_TEXT)
        self.text.tag_add("placeholder", "1.0", "end")
        self.text.tag_config("placeholder", foreground=NOTE_MUTED_TEXT)
        self.text.bind("<KeyPress>", self._remove_placeholder, add="+")

    def _is_placeholder_active(self):
        return bool(self.text.tag_ranges("placeholder")) and (
            self.text.get("1.0", "end-1c") == PLACEHOLDER_TEXT
        )

    def _remove_placeholder(self, _event=None):
        if self._is_placeholder_active():
            self.text.delete("1.0", "end")
            self.text.tag_remove("placeholder", "1.0", "end")

    def _clear_note(self):
        if self._is_placeholder_active() or not self.text.get("1.0", "end-1c").strip():
            self._show_short_message("当前页已经是空白。")
            return "break"

        self._dismiss_clear_undo()
        selection = None
        try:
            selection = (self.text.index("sel.first"), self.text.index("sel.last"))
        except tk.TclError:
            pass
        self.clear_undo_state = {
            "page": self.current_page,
            "content": self.text.get("1.0", "end-1c"),
            "insert": self.text.index("insert"),
            "selection": selection,
        }
        self._cancel_autosave()
        self.text.delete("1.0", "end")
        self._insert_placeholder()
        if self.clear_undo_label is not None:
            self.clear_undo_label.pack(side="left", padx=(4, 0), pady=4)
        self._set_autosave_status("已清空，可撤销", NOTE_WARNING_NOTE)
        self.clear_undo_after_id = self.root.after(
            CLEAR_UNDO_WINDOW_MS,
            self._commit_clear_note,
        )
        return "break"

    def _undo_clear_note(self, _event=None):
        state = self.clear_undo_state
        if state is None or state["page"] != self.current_page:
            return None
        self._dismiss_clear_undo()
        self.text.delete("1.0", "end")
        self.text.tag_remove("placeholder", "1.0", "end")
        self.text.insert("1.0", state["content"])
        self._apply_translation_tags()
        self.text.mark_set("insert", state["insert"])
        if state["selection"]:
            self.text.tag_add("sel", *state["selection"])
        self.text.focus_set()
        self._set_autosave_status("已恢复", NOTE_SUCCESS)
        self._on_note_modified()
        return "break"

    def _commit_clear_note(self):
        state = self.clear_undo_state
        self._dismiss_clear_undo()
        if state is not None and state["page"] == self.current_page:
            self.save_note()

    def _dismiss_clear_undo(self):
        if self.clear_undo_after_id is not None:
            try:
                self.root.after_cancel(self.clear_undo_after_id)
            except tk.TclError:
                pass
        self.clear_undo_after_id = None
        self.clear_undo_state = None
        if self.clear_undo_label is not None:
            self.clear_undo_label.pack_forget()

    def _start_move(self, event):
        self.drag_start_x = event.x_root - self.root.winfo_x()
        self.drag_start_y = event.y_root - self.root.winfo_y()

    def _move_window(self, event):
        x = event.x_root - self.drag_start_x
        y = event.y_root - self.drag_start_y
        self.root.geometry(f"+{x}+{y}")

    def _start_resize(self, event):
        self.root.update_idletasks()
        self.resize_start_x = event.x_root
        self.resize_start_y = event.y_root
        self.resize_start_width = max(self.root.winfo_width(), MIN_WINDOW_WIDTH)
        self.resize_start_height = max(self.root.winfo_height(), MIN_WINDOW_HEIGHT)
        return "break"

    def _resize_window(self, event):
        width = max(
            self.resize_start_width + event.x_root - self.resize_start_x,
            MIN_WINDOW_WIDTH,
        )
        height = max(
            self.resize_start_height + event.y_root - self.resize_start_y,
            MIN_WINDOW_HEIGHT,
        )
        self.root.geometry(f"{width}x{height}+{self.root.winfo_x()}+{self.root.winfo_y()}")
        self._update_window_size_label()
        return "break"

    def _finish_resize(self, _event):
        self._save_state()
        return "break"

    def _move_near_pointer(self, pointer_x, pointer_y):
        self.root.update_idletasks()
        width, height = self._current_window_size()

        screen_x, screen_y, right, bottom = monitor_work_area_for_point(
            pointer_x,
            pointer_y,
            fallback_width=self.root.winfo_screenwidth(),
            fallback_height=self.root.winfo_screenheight(),
        )

        x = pointer_x + POPUP_OFFSET
        y = pointer_y + POPUP_OFFSET
        if x + width > right:
            x = pointer_x - width - POPUP_OFFSET
        if y + height > bottom:
            y = pointer_y - height - POPUP_OFFSET

        x = max(screen_x, min(x, right - width))
        y = max(screen_y, min(y, bottom - height))
        log(f"move note to {x},{y} from pointer {pointer_x},{pointer_y}")
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _force_window_to_front(self):
        self.root.update_idletasks()
        self.root.attributes("-topmost", True)
        hwnd = wintypes.HWND(self.root.winfo_id())
        user32.ShowWindow(hwnd, SW_SHOWNORMAL)
        user32.SetWindowPos(
            hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
        )
        user32.SetForegroundWindow(hwnd)
        user32.SetActiveWindow(hwnd)
        self.root.lift()
        self.root.focus_force()

    def _release_topmost(self):
        hwnd = wintypes.HWND(self.root.winfo_id())
        user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)

    def _is_foreground(self):
        return user32.GetForegroundWindow() == self.root.winfo_id()

    def _should_hide_on_toggle(self):
        return self._is_foreground() or bool(self.root.attributes("-topmost"))

    def _load_geometry(self):
        state = read_state_data()
        return normalize_window_geometry(state.get("geometry"))

    def _load_active_page(self):
        state = read_state_data()
        return normalized_note_page(state.get("active_page", 1), self.note_pages)

    def _save_state(self):
        atomic_write_text(
            STATE_FILE,
            json.dumps(
                {
                    "geometry": self._fixed_geometry(),
                    "active_page": normalized_note_page(self.current_page, self.note_pages),
                    "pages": self.note_pages,
                    SETTINGS_STATE_KEY: self.settings,
                },
                ensure_ascii=False,
                indent=2,
            ),
        )

    def _fixed_geometry(self):
        return normalize_window_geometry(self.root.geometry())

    def _current_window_size(self):
        return parse_window_size(self.root.geometry())

def main():
    global INSTANCE_MUTEX
    if sys.platform != "win32":
        raise SystemExit("这个版本使用 Windows 鼠标侧键监听，只支持 Windows。")

    NOTE_DIR.mkdir(parents=True, exist_ok=True)
    INSTANCE_MUTEX = kernel32.CreateMutexW(None, False, "Local\\QuickSideNoteSingleInstance")
    if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        log("another quick note instance is already running")
        return

    app = QuickNoteApp()
    app.run()


if __name__ == "__main__":
    main()
