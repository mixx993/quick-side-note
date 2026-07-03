import asyncio
import ctypes
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import simpledialog, font as tkfont
from PIL import Image, ImageGrab, ImageOps


APP_NAME = "Quick Side Note"
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
WM_QUIT = 0x0012
ERROR_ALREADY_EXISTS = 183
VK_BROWSER_BACK = 0xA6
VK_BROWSER_FORWARD = 0xA7
SW_SHOWNORMAL = 1
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
HWND_BROADCAST = 0xFFFF
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_SHOWWINDOW = 0x0040
WM_SETTINGCHANGE = 0x001A
SMTO_ABORTIFHUNG = 0x0002
SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79
POPUP_OFFSET = 10
WINDOW_WIDTH = 420
WINDOW_HEIGHT = 300
MIN_WINDOW_WIDTH = 300
MIN_WINDOW_HEIGHT = 200
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
UI_BORDER = "#d7dee8"
UI_SHELL_BG = "#f4f7fb"
UI_HEADER_BG = "#fbfcfe"
UI_HEADER_TEXT = "#1f2a3a"
UI_PAPER_BG = "#ffffff"
UI_PAPER_BORDER = "#e5ebf2"
UI_TEXT = "#172033"
UI_MUTED_TEXT = "#667085"
UI_SELECTION_BG = "#d8e8ff"
UI_SELECTION_FG = "#10223a"
UI_INSERT = "#2563eb"
UI_RESIZE_GRIP = "#9aa8b8"
UI_ACCENT = "#2563eb"
UI_ACCENT_SOFT = "#e8f1ff"
UI_ACCENT_HOVER = "#dceafe"
UI_PAGE_HOVER_BG = "#eef5ff"
UI_ACTIVE_PAGE_BG = UI_ACCENT_SOFT
UI_ACTIVE_PAGE_FG = UI_ACCENT
UI_INACTIVE_PAGE_BG = UI_SHELL_BG
UI_INACTIVE_PAGE_FG = "#526173"
UI_TOAST_BG = "#17202a"
UI_TOAST_FG = "#f8fafc"
UI_DIALOG_BG = "#f6f8fb"
UI_CARD_BG = "#ffffff"
UI_DIVIDER = "#e8edf4"
UI_FIELD_BG = "#fbfdff"
UI_SUCCESS = "#0f8f6f"
UI_WARNING = "#d97706"
UI_DANGER = "#b42318"
UI_DISABLED_BG = "#eef2f7"
EVENT_DEBOUNCE_SECONDS = 0.05
DOUBLE_CLICK_SECONDS = 0.3
CODEX_TIMEOUT_SECONDS = 25
CODEX_MODEL = "gpt-5.4-mini"
CODEX_REASONING_EFFORT = "low"
DEEPSEEK_TEXT_MODEL = "deepseek-chat"
DEEPSEEK_CHAT_COMPLETIONS_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_TIMEOUT_SECONDS = 8
DEFAULT_APP_SETTINGS = {
    "side_button": "xbutton1",
    "block_browser_key": True,
    "double_click_ms": 300,
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


user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
ULONG_PTR = wintypes.WPARAM
LRESULT = wintypes.LPARAM
INSTANCE_MUTEX = None
DPI_AWARENESS_CONFIGURED = False
WINDOW_GEOMETRY_RE = re.compile(r"^(?:(\d+)x(\d+))?([+-]\d+)([+-]\d+)$")


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


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
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with LOG_FILE.open("a", encoding="utf-8") as file:
            file.write(f"{timestamp} {message}\n")
    except OSError:
        pass


@dataclass(frozen=True)
class TranslationResult:
    source_text: str
    translation: str


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


def read_state_data():
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
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
    }


def side_button_value(settings):
    settings = normalize_app_settings(settings)
    return SIDE_BUTTON_OPTIONS[settings["side_button"]]["button"]


def blocked_browser_keys_for_settings(settings):
    settings = normalize_app_settings(settings)
    if not settings["block_browser_key"]:
        return set()
    return {SIDE_BUTTON_OPTIONS[settings["side_button"]]["browser_key"]}


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
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"DeepSeek text translation failed: {detail}") from exc
        except OSError as exc:
            raise RuntimeError(f"DeepSeek text translation failed: {exc}") from exc

        data = json.loads(response_text)
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("DeepSeek response missing translation content") from exc

        result = parse_codex_translation_output(content)
        return TranslationResult(source_text=source_text, translation=result.translation)


class FastTranslationBackend:
    def __init__(self, fallback_backend):
        self.ocr_backend = WindowsOcrBackend()
        self.text_backend = DeepSeekTextBackend()
        self.fallback_backend = fallback_backend

    def translate_image(self, image_path):
        started = time.perf_counter()
        try:
            ocr_started = time.perf_counter()
            source_text = normalize_ocr_text(self.ocr_backend.recognize_text(image_path))
            log(
                "windows OCR recognized "
                f"{source_text!r} in {time.perf_counter() - ocr_started:.2f}s"
            )
        except Exception as exc:
            log(f"fast OCR failed, falling back to Codex CLI: {exc}")
            fallback_started = time.perf_counter()
            result = self.fallback_backend.translate_image(image_path)
            log(f"Codex CLI fallback completed in {time.perf_counter() - fallback_started:.2f}s")
            return result

        try:
            result = self.text_backend.translate_text(source_text)
        except Exception as exc:
            log(f"fast text translation failed: {exc}")
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


class MouseSideButtonHook:
    def __init__(self, event_queue, settings_provider=None):
        self.event_queue = event_queue
        self.settings_provider = settings_provider or (lambda: DEFAULT_APP_SETTINGS)
        self.hook_id = None
        self.thread_id = None
        self._callback = LowLevelMouseProc(self._handle_mouse)
        self._ready = threading.Event()
        self.thread = None

    def start(self):
        if self.is_alive():
            return
        self._ready.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        self._ready.wait(timeout=2)

    def stop(self):
        if self.thread_id:
            user32.PostThreadMessageW(self.thread_id, WM_QUIT, 0, 0)

    def is_alive(self):
        return bool(self.thread and self.thread.is_alive() and self.hook_id)

    def _run(self):
        self.thread_id = kernel32.GetCurrentThreadId()
        self.hook_id = user32.SetWindowsHookExW(
            WH_MOUSE_LL,
            ctypes.cast(self._callback, ctypes.c_void_p),
            kernel32.GetModuleHandleW(None),
            0,
        )
        if not self.hook_id:
            log(f"mouse hook failed: {kernel32.GetLastError()}")
        self._ready.set()

        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        if self.hook_id:
            user32.UnhookWindowsHookEx(self.hook_id)
            self.hook_id = None
        self.thread_id = None

    def _handle_mouse(self, n_code, w_param, l_param):
        if n_code >= 0 and w_param in (WM_XBUTTONDOWN, WM_XBUTTONUP):
            info = ctypes.cast(l_param, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
            button = (info.mouseData >> 16) & 0xFFFF
            target_button = side_button_value(self.settings_provider())
            if w_param == WM_XBUTTONDOWN and button == target_button:
                log(f"mouse side button down at {info.pt.x},{info.pt.y}")
                self.event_queue.put(("toggle", info.pt.x, info.pt.y))
            if button == target_button:
                return 1

        return user32.CallNextHookEx(self.hook_id, n_code, w_param, l_param)


class BrowserKeyHook:
    def __init__(self, event_queue, settings_provider=None):
        self.event_queue = event_queue
        self.settings_provider = settings_provider or (lambda: DEFAULT_APP_SETTINGS)
        self.hook_id = None
        self.thread_id = None
        self._callback = LowLevelKeyboardProc(self._handle_keyboard)
        self._ready = threading.Event()
        self.thread = None

    def start(self):
        if self.is_alive():
            return
        self._ready.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        self._ready.wait(timeout=2)

    def stop(self):
        if self.thread_id:
            user32.PostThreadMessageW(self.thread_id, WM_QUIT, 0, 0)

    def is_alive(self):
        return bool(self.thread and self.thread.is_alive() and self.hook_id)

    def _run(self):
        self.thread_id = kernel32.GetCurrentThreadId()
        self.hook_id = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL,
            ctypes.cast(self._callback, ctypes.c_void_p),
            kernel32.GetModuleHandleW(None),
            0,
        )
        if not self.hook_id:
            log(f"keyboard hook failed: {kernel32.GetLastError()}")
        self._ready.set()

        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        if self.hook_id:
            user32.UnhookWindowsHookEx(self.hook_id)
            self.hook_id = None
        self.thread_id = None

    def _handle_keyboard(self, n_code, w_param, l_param):
        if n_code >= 0 and w_param in (WM_KEYDOWN, WM_SYSKEYDOWN, WM_KEYUP, WM_SYSKEYUP):
            info = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            if info.vkCode in blocked_browser_keys_for_settings(self.settings_provider()):
                if w_param in (WM_KEYDOWN, WM_SYSKEYDOWN):
                    point = POINT()
                    user32.GetCursorPos(ctypes.byref(point))
                    log(f"browser key down {info.vkCode} at {point.x},{point.y}")
                    self.event_queue.put(("toggle", point.x, point.y))
                return 1

        return user32.CallNextHookEx(self.hook_id, n_code, w_param, l_param)


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

    def _start(self, event):
        self.start_x = event.x_root
        self.start_y = event.y_root
        self.rect_id = self.canvas.create_rectangle(
            event.x,
            event.y,
            event.x,
            event.y,
            outline="white",
            width=2,
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
        self.note_pages = normalize_note_pages(state.get("pages"))
        self.current_page = self._load_active_page()
        self.page_buttons = {}
        self.add_page_button = None
        self.page_title_label = None
        self.hide_button = None
        self.settings_button = None
        self.root.geometry(self._load_geometry())
        self.root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.root.overrideredirect(True)
        self.root.configure(bg=UI_BORDER)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_and_save)

        self.events = queue.Queue()
        self.mouse_hook = MouseSideButtonHook(self.events, lambda: self.settings)
        self.browser_key_hook = BrowserKeyHook(self.events, lambda: self.settings)
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
        self.backend = FastTranslationBackend(CodexCliBackend())
        self.note_store = NoteStore(NOTE_FILE, VOCABULARY_FILE)

        self._build_ui()
        self._load_note()
        self._bind_keys()
        self._poll_events()
        self.root.after(250, self._ensure_api_setup)

    def run(self):
        log("app start")
        self.mouse_hook.start()
        self.browser_key_hook.start()
        if not self.mouse_hook.hook_id:
            pass
        self.root.mainloop()
        self.mouse_hook.stop()
        self.browser_key_hook.stop()

    def _build_ui(self):
        shell = tk.Frame(self.root, bg=UI_SHELL_BG, padx=8, pady=8)
        shell.pack(fill="both", expand=True, padx=1, pady=1)

        header = tk.Frame(shell, bg=UI_HEADER_BG, height=32)
        header.pack(fill="x")
        header.pack_propagate(False)
        self._bind_move_handle(header)

        accent = tk.Frame(header, bg=UI_ACCENT, width=3)
        accent.pack(side="left", fill="y", padx=(0, 9))

        self.page_title_label = tk.Label(
            header,
            text="",
            bg=UI_HEADER_BG,
            fg=UI_HEADER_TEXT,
            bd=0,
            anchor="w",
            font=("Microsoft YaHei UI", 10, "bold"),
        )
        self.page_title_label.pack(side="left", fill="x", expand=True)
        self._bind_move_handle(self.page_title_label)

        self.settings_button = tk.Label(
            header,
            text="⚙",
            bg=UI_HEADER_BG,
            fg=UI_MUTED_TEXT,
            bd=0,
            width=3,
            anchor="center",
            cursor="hand2",
            font=("Segoe UI Symbol", 12),
        )
        self.settings_button.pack(side="right", fill="y")
        self.settings_button.bind("<Button-1>", lambda _event: self._show_settings_dialog())
        self.settings_button.bind("<Enter>", lambda _event: self._set_settings_hover(True))
        self.settings_button.bind("<Leave>", lambda _event: self._set_settings_hover(False))

        self.hide_button = tk.Label(
            header,
            text="×",
            bg=UI_HEADER_BG,
            fg=UI_MUTED_TEXT,
            bd=0,
            width=3,
            anchor="center",
            cursor="hand2",
            font=("Microsoft YaHei UI", 12),
        )
        self.hide_button.pack(side="right", fill="y")
        self.hide_button.bind("<Button-1>", lambda _event: self.hide_and_save())
        self.hide_button.bind("<Enter>", lambda _event: self._set_hide_hover(True))
        self.hide_button.bind("<Leave>", lambda _event: self._set_hide_hover(False))

        body = tk.Frame(shell, bg=UI_SHELL_BG)
        body.pack(fill="both", expand=True, pady=(8, 0))

        self.page_rail = tk.Frame(body, bg=UI_SHELL_BG, width=self._page_rail_width())
        self.page_rail.pack(side="left", fill="y", padx=(0, 8))
        self.page_rail.pack_propagate(False)

        self._rebuild_page_tabs()

        editor = tk.Frame(body, bg=UI_PAPER_BORDER, padx=1, pady=1)
        editor.pack(side="left", fill="both", expand=True)

        self.text = tk.Text(
            editor,
            wrap="word",
            undo=True,
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=16,
            pady=14,
            font=("Microsoft YaHei UI", 11),
            bg=UI_PAPER_BG,
            fg=UI_TEXT,
            insertbackground=UI_INSERT,
            insertwidth=2,
            selectbackground=UI_SELECTION_BG,
            selectforeground=UI_SELECTION_FG,
            inactiveselectbackground=UI_SELECTION_BG,
            spacing1=2,
            spacing2=1,
            spacing3=8,
            tabs=("2c",),
        )
        self.text.pack(side="left", fill="both", expand=True)
        self.text.tag_config("placeholder", foreground=UI_MUTED_TEXT)
        self._update_page_buttons()

        self.resize_grip = tk.Canvas(
            shell,
            width=RESIZE_GRIP_SIZE,
            height=RESIZE_GRIP_SIZE,
            bg=UI_PAPER_BG,
            bd=0,
            highlightthickness=0,
            cursor="size_nw_se",
        )
        self.resize_grip.place(relx=1.0, rely=1.0, x=-5, y=-5, anchor="se")
        self.resize_grip.create_line(8, 17, 17, 8, fill=UI_RESIZE_GRIP, width=1)
        self.resize_grip.create_line(12, 17, 17, 12, fill=UI_RESIZE_GRIP, width=1)
        self.resize_grip.bind("<ButtonPress-1>", self._start_resize)
        self.resize_grip.bind("<B1-Motion>", self._resize_window)
        self.resize_grip.bind("<ButtonRelease-1>", self._finish_resize)

    def _bind_keys(self):
        self.root.bind("<Control-s>", lambda _event: self.save_note())
        self.root.bind("<Escape>", lambda _event: self.hide_and_save())
        self.root.bind("<FocusOut>", lambda _event: self.save_note())
        self.root.bind("<Control-l>", lambda _event: self._clear_note())
        self.root.bind("<Control-k>", lambda _event: self._show_settings_dialog("api"))
        self.root.bind("<Control-comma>", lambda _event: self._show_settings_dialog())
        self.root.bind("<Control-q>", lambda _event: self.root.destroy())
        self.root.bind_all("<Alt-ButtonPress-1>", self._start_move)
        self.root.bind_all("<Alt-B1-Motion>", self._move_window)
        self.root.bind_all("<Alt-ButtonRelease-1>", lambda _event: self._save_state())

    def _bind_move_handle(self, widget):
        widget.bind("<ButtonPress-1>", self._start_move)
        widget.bind("<B1-Motion>", self._move_window)
        widget.bind("<ButtonRelease-1>", lambda _event: self._save_state())

    def _ensure_api_setup(self):
        if not is_deepseek_api_configured():
            self._show_settings_dialog("api", first_run=True)

    def _show_api_setup_dialog(self, first_run=False):
        self.root.deiconify()
        dialog = tk.Toplevel(self.root)
        dialog.title("配置翻译 API")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)
        dialog.configure(bg=UI_HEADER_BG)
        dialog.transient(self.root)

        frame = tk.Frame(dialog, bg=UI_HEADER_BG, padx=18, pady=16)
        frame.pack(fill="both", expand=True)

        title_text = "首次运行设置" if first_run else "配置 DeepSeek API"
        title = tk.Label(
            frame,
            text=title_text,
            bg=UI_HEADER_BG,
            fg=UI_HEADER_TEXT,
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
            bg=UI_HEADER_BG,
            fg=UI_INACTIVE_PAGE_FG,
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
        )
        entry.pack(fill="x")

        status = tk.Label(
            frame,
            text="",
            bg=UI_HEADER_BG,
            fg="#b42318",
            anchor="w",
            font=("Microsoft YaHei UI", 9),
        )
        status.pack(fill="x", pady=(8, 0))

        buttons = tk.Frame(frame, bg=UI_HEADER_BG)
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
            bg=UI_ACCENT,
            fg="#ffffff",
            activebackground=UI_ACCENT,
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
            bg=UI_ACCENT_SOFT,
            fg=UI_ACCENT,
            activebackground=UI_ACCENT_HOVER,
            activeforeground=UI_ACCENT,
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
        dialog.configure(bg=UI_DIALOG_BG)
        dialog.transient(self.root)

        frame = tk.Frame(dialog, bg=UI_DIALOG_BG, padx=20, pady=18)
        frame.pack(fill="both", expand=True)

        title_text = "首次运行设置" if first_run else "设置"
        title = tk.Label(
            frame,
            text=title_text,
            bg=UI_DIALOG_BG,
            fg=UI_HEADER_TEXT,
            anchor="w",
            font=("Microsoft YaHei UI", 14, "bold"),
        )
        title.pack(fill="x")

        subtitle = (
            "配置 DeepSeek API Key 后即可开始翻译。其他选项可以稍后再调整。"
            if first_run
            else "管理 API、启动项和侧键行为。保存后立即生效。"
        )
        description = tk.Label(
            frame,
            text=subtitle,
            bg=UI_DIALOG_BG,
            fg=UI_INACTIVE_PAGE_FG,
            anchor="w",
            justify="left",
            font=("Microsoft YaHei UI", 9),
        )
        description.pack(fill="x", pady=(5, 14))

        def make_card(parent, title_text, status_text=None, status_color=UI_MUTED_TEXT):
            card = tk.Frame(
                parent,
                bg=UI_CARD_BG,
                bd=0,
                highlightthickness=1,
                highlightbackground=UI_DIVIDER,
                padx=14,
                pady=12,
            )
            card.pack(fill="x", pady=(0, 10))

            header = tk.Frame(card, bg=UI_CARD_BG)
            header.pack(fill="x", pady=(0, 8))
            heading = tk.Label(
                header,
                text=title_text,
                bg=UI_CARD_BG,
                fg=UI_HEADER_TEXT,
                anchor="w",
                font=("Microsoft YaHei UI", 10, "bold"),
            )
            heading.pack(side="left")
            if status_text is not None:
                status = tk.Label(
                    header,
                    text=status_text,
                    bg=UI_FIELD_BG,
                    fg=status_color,
                    padx=8,
                    pady=2,
                    font=("Microsoft YaHei UI", 8),
                )
                status.pack(side="right")
            return card

        def make_row(parent, label_text, pady=(0, 8)):
            row = tk.Frame(parent, bg=UI_CARD_BG)
            row.pack(fill="x", pady=pady)
            label = tk.Label(
                row,
                text=label_text,
                bg=UI_CARD_BG,
                fg=UI_INACTIVE_PAGE_FG,
                anchor="w",
                width=10,
                font=("Microsoft YaHei UI", 9),
            )
            label.pack(side="left")
            content = tk.Frame(row, bg=UI_CARD_BG)
            content.pack(side="left", fill="x", expand=True)
            return content

        def make_hint(parent, text):
            hint = tk.Label(
                parent,
                text=text,
                bg=UI_CARD_BG,
                fg=UI_MUTED_TEXT,
                anchor="w",
                justify="left",
                wraplength=500,
                font=("Microsoft YaHei UI", 8),
            )
            hint.pack(fill="x", pady=(2, 0))
            return hint

        def make_button(parent, text, command, primary=False):
            if primary:
                bg = UI_ACCENT
                fg = "#ffffff"
                active_bg = "#1d4ed8"
            else:
                bg = UI_ACCENT_SOFT
                fg = UI_ACCENT
                active_bg = UI_ACCENT_HOVER
            return tk.Button(
                parent,
                text=text,
                command=command,
                bg=bg,
                fg=fg,
                activebackground=active_bg,
                activeforeground=fg,
                relief="flat",
                bd=0,
                padx=14,
                pady=6,
                font=("Microsoft YaHei UI", 9),
            )

        def make_check(parent, text, variable):
            return tk.Checkbutton(
                parent,
                text=text,
                variable=variable,
                bg=UI_CARD_BG,
                fg=UI_TEXT,
                activebackground=UI_CARD_BG,
                selectcolor=UI_CARD_BG,
                font=("Microsoft YaHei UI", 9),
                anchor="w",
            )

        key_var = tk.StringVar(value=get_user_environment_value("DEEPSEEK_API_KEY"))
        api_configured = bool(key_var.get())
        api_section = make_card(
            frame,
            "翻译 API",
            "已配置" if api_configured else "未配置",
            UI_SUCCESS if api_configured else UI_WARNING,
        )

        key_row = make_row(api_section, "API Key")
        key_entry = tk.Entry(
            key_row,
            textvariable=key_var,
            show="*",
            relief="solid",
            bd=1,
            font=("Consolas", 10),
            bg=UI_FIELD_BG,
            fg=UI_TEXT,
            insertbackground=UI_INSERT,
        )
        key_entry.pack(side="left", fill="x", expand=True, ipady=3)

        show_key_var = tk.BooleanVar(value=False)

        def update_key_visibility():
            key_entry.configure(show="" if show_key_var.get() else "*")

        show_key = tk.Checkbutton(
            key_row,
            text="显示",
            variable=show_key_var,
            command=update_key_visibility,
            bg=UI_CARD_BG,
            fg=UI_INACTIVE_PAGE_FG,
            activebackground=UI_CARD_BG,
            selectcolor=UI_CARD_BG,
            font=("Microsoft YaHei UI", 9),
        )
        show_key.pack(side="left", padx=(8, 0))

        api_status_var = tk.StringVar(
            value="DeepSeek 文本翻译使用当前 Windows 用户环境变量。"
        )
        api_status = tk.Label(
            api_section,
            textvariable=api_status_var,
            bg=UI_CARD_BG,
            fg=UI_MUTED_TEXT,
            anchor="w",
            font=("Microsoft YaHei UI", 8),
        )
        api_status.pack(fill="x", pady=(0, 8))

        def clear_api_key():
            key_var.set("")
            api_status_var.set("保存后会清除当前用户的 DEEPSEEK_API_KEY。")
            api_status.configure(fg=UI_DANGER)

        api_actions = tk.Frame(api_section, bg=UI_CARD_BG)
        api_actions.pack(fill="x")
        clear_api_button = make_button(api_actions, "清除 Key", clear_api_key)
        clear_api_button.pack(side="right")

        startup_var = tk.BooleanVar(value=is_startup_enabled())
        startup_command = get_startup_registry_value()
        startup_section = make_card(
            frame,
            "开机启动",
            "已启用" if startup_command else "未启用",
            UI_SUCCESS if startup_command else UI_MUTED_TEXT,
        )
        startup_row = make_row(startup_section, "启动项", pady=(0, 4))
        startup_check = make_check(
            startup_row,
            "登录 Windows 后自动启动",
            startup_var,
        )
        startup_check.pack(anchor="w")
        make_hint(
            startup_section,
            "保存后写入当前用户启动项，不需要管理员权限。卸载应用会移除程序文件，便签数据仍保留。",
        )

        shortcut_section = make_card(frame, "侧键和快捷操作")
        side_button_var = tk.StringVar(value=self.settings["side_button"])
        side_row = make_row(shortcut_section, "触发侧键", pady=(0, 6))
        for index, (key, option) in enumerate(SIDE_BUTTON_OPTIONS.items()):
            radio = tk.Radiobutton(
                side_row,
                text=option["label"],
                value=key,
                variable=side_button_var,
                bg=UI_CARD_BG,
                fg=UI_TEXT,
                activebackground=UI_CARD_BG,
                selectcolor=UI_CARD_BG,
                font=("Microsoft YaHei UI", 9),
            )
            radio.pack(side="left", padx=(0, 16 if index == 0 else 0))

        block_browser_var = tk.BooleanVar(value=self.settings["block_browser_key"])
        block_row = make_row(shortcut_section, "浏览器键", pady=(0, 6))
        block_browser = make_check(
            block_row,
            "拦截对应后退/前进键，避免浏览器跳转",
            block_browser_var,
        )
        block_browser.pack(anchor="w")

        delay_row = make_row(shortcut_section, "双击间隔", pady=(0, 6))
        double_click_var = tk.StringVar(value=str(self.settings["double_click_ms"]))
        double_click_spin = tk.Spinbox(
            delay_row,
            from_=MIN_DOUBLE_CLICK_MS,
            to=MAX_DOUBLE_CLICK_MS,
            increment=50,
            textvariable=double_click_var,
            width=6,
            relief="solid",
            bd=1,
            bg=UI_FIELD_BG,
            fg=UI_TEXT,
            buttonbackground=UI_DISABLED_BG,
            font=("Consolas", 10),
        )
        double_click_spin.pack(side="left", ipady=2)
        tk.Label(
            delay_row,
            text="毫秒",
            bg=UI_CARD_BG,
            fg=UI_MUTED_TEXT,
            font=("Microsoft YaHei UI", 9),
        ).pack(side="left", padx=(6, 0))
        make_hint(
            shortcut_section,
            "固定快捷键：Ctrl+S 保存 · Esc 隐藏 · Ctrl+L 清空 · Ctrl+K API · Ctrl+, 设置 · Ctrl+Q 退出",
        )

        status_var = tk.StringVar(value="")
        status = tk.Label(
            frame,
            textvariable=status_var,
            bg=UI_DIALOG_BG,
            fg=UI_DANGER,
            anchor="w",
            font=("Microsoft YaHei UI", 9),
        )
        status.pack(fill="x")

        buttons = tk.Frame(frame, bg=UI_DIALOG_BG)
        buttons.pack(fill="x", pady=(12, 0))

        def close_dialog():
            dialog.grab_release()
            dialog.destroy()

        def save_settings():
            key = normalize_api_key(key_var.get())
            if key and not is_plausible_api_key(key):
                status_var.set("API Key 看起来不完整，请检查后再保存。")
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
                }
            )
            self._save_state()
            log(f"settings saved: {self.settings}")
            close_dialog()
            self._show_short_message("设置已保存")

        save_button = make_button(buttons, "保存设置", save_settings, primary=True)
        save_button.pack(side="right")

        cancel_text = "稍后再说" if first_run else "取消"
        cancel_button = make_button(buttons, cancel_text, close_dialog)
        cancel_button.pack(side="right", padx=(0, 8))

        dialog.protocol("WM_DELETE_WINDOW", close_dialog)
        dialog.update_idletasks()
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_w = max(self.root.winfo_width(), WINDOW_WIDTH)
        root_h = max(self.root.winfo_height(), WINDOW_HEIGHT)
        width = max(dialog.winfo_width(), 560)
        height = dialog.winfo_height()
        x = root_x + max(0, (root_w - width) // 2)
        y = root_y + max(0, (root_h - height) // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        dialog.grab_set()
        if initial_section == "api":
            key_entry.focus_set()
        else:
            dialog.focus_set()

    def _page_rail_width(self):
        names = [str(page["name"]) for page in self.note_pages] + ["+"]
        try:
            label_font = tkfont.Font(
                root=self.root, family=PAGE_LABEL_FONT[0], size=PAGE_LABEL_FONT[1]
            )
            content_width = max(label_font.measure(name) for name in names)
        except tk.TclError:
            content_width = max(len(name) for name in names) * 12
        return clamp_page_rail_width(content_width)

    def _rebuild_page_tabs(self):
        self.page_rail.configure(width=self._page_rail_width())
        for child in self.page_rail.winfo_children():
            child.destroy()
        self.page_buttons = {}

        for page in self.note_pages:
            page_id = page["id"]
            page_button = tk.Label(
                self.page_rail,
                text=page["name"],
                bd=0,
                padx=PAGE_LABEL_PADDING_X,
                pady=6,
                anchor=page_label_anchor(page["name"]),
                font=PAGE_LABEL_FONT,
                cursor="hand2",
            )
            page_button.pack(fill="x", pady=(0, 4))
            page_button.bind(
                "<Button-1>", lambda _event, target=page_id: self.switch_page(target)
            )
            page_button.bind(
                "<Double-Button-1>",
                lambda _event, target=page_id: self.rename_page(target),
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
            self.page_rail,
            text="+",
            bd=0,
            padx=0,
            pady=5,
            anchor="center",
            font=PAGE_ADD_FONT,
            cursor="hand2",
            bg=UI_INACTIVE_PAGE_BG,
            fg=UI_INACTIVE_PAGE_FG,
        )
        add_button.pack(fill="x", pady=(4, 0))
        add_button.bind("<Button-1>", lambda _event: self.create_page())
        add_button.bind("<Enter>", lambda _event: self._set_add_hover(True))
        add_button.bind("<Leave>", lambda _event: self._set_add_hover(False))
        self.add_page_button = add_button
        self._update_page_buttons()

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
            self.page_title_label.configure(
                text=f"Quick Note · {self._page_name(self.current_page)}"
            )

    def _apply_page_button_style(self, page, button, hover=False):
        active = page == self.current_page
        if active:
            bg = UI_ACTIVE_PAGE_BG
            fg = UI_ACTIVE_PAGE_FG
        elif hover:
            bg = UI_PAGE_HOVER_BG
            fg = UI_TEXT
        else:
            bg = UI_INACTIVE_PAGE_BG
            fg = UI_INACTIVE_PAGE_FG

        button.configure(bg=bg, fg=fg)

    def _set_page_hover(self, page, hover):
        button = self.page_buttons.get(page)
        if button is not None:
            self._apply_page_button_style(page, button, hover)

    def _apply_add_button_style(self, hover):
        bg = UI_ACCENT_HOVER if hover else UI_INACTIVE_PAGE_BG
        fg = UI_ACCENT if hover else UI_INACTIVE_PAGE_FG
        self.add_page_button.configure(bg=bg, fg=fg)

    def _set_add_hover(self, hover):
        if self.add_page_button is not None:
            self._apply_add_button_style(hover)

    def _set_hide_hover(self, hover):
        if self.hide_button is None:
            return
        bg = UI_ACCENT_HOVER if hover else UI_HEADER_BG
        fg = UI_TEXT if hover else UI_MUTED_TEXT
        self.hide_button.configure(bg=bg, fg=fg)

    def _set_settings_hover(self, hover):
        if self.settings_button is None:
            return
        bg = UI_ACCENT_HOVER if hover else UI_HEADER_BG
        fg = UI_TEXT if hover else UI_MUTED_TEXT
        self.settings_button.configure(bg=bg, fg=fg)

    def _poll_events(self):
        self.hook_check_ticks += 1
        if self.hook_check_ticks >= 20:
            self.hook_check_ticks = 0
            if not self.mouse_hook.is_alive():
                log("mouse hook stopped, restarting")
                self.mouse_hook.start()
            if not self.browser_key_hook.is_alive():
                log("keyboard hook stopped, restarting")
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
                log("side click ignored while OCR is active")
            return

        if self.pending_single_click is not None:
            self.root.after_cancel(self.pending_single_click)
            self.pending_single_click = None
            self.toggle_window(pointer_x, pointer_y)
            return

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
        pointer_x = self.root.winfo_pointerx()
        pointer_y = self.root.winfo_pointery()
        if pointer_x is not None and pointer_y is not None:
            self._move_near_pointer(pointer_x, pointer_y)
        self.root.deiconify()
        self._force_window_to_front()
        self.text.focus_set()
        self.text.mark_set("insert", "end-1c")
        self.text.see("insert")

    def hide_and_save(self):
        log("hide note")
        self.save_note()
        self.visible = False
        self.root.attributes("-topmost", False)
        self._release_topmost()
        self.root.withdraw()

    def save_note(self):
        content = "" if self._is_placeholder_active() else self.text.get("1.0", "end-1c")
        note_file_for_page(self.current_page).write_text(content, encoding="utf-8")
        self._save_state()

    def start_ocr_selection(self):
        if self.ocr_active:
            log("OCR selection already active")
            return

        self.ocr_active = True
        self.hide_and_save()
        overlay = ScreenCaptureOverlay(self.root, self._on_capture_complete)
        self.capture_overlay = overlay
        try:
            overlay.start()
        except Exception as exc:
            self.ocr_active = False
            self.capture_overlay = None
            log(f"OCR overlay failed: {exc}")
            self._show_short_message(f"框选启动失败：{exc}")

    def _on_capture_complete(self, image_path, error):
        self.capture_overlay = None
        if error:
            self.ocr_active = False
            self._show_short_message(error)
            log(error)
            return

        thread = threading.Thread(
            target=self._translate_capture_worker,
            args=(image_path,),
            daemon=True,
        )
        thread.start()

    def _translate_capture_worker(self, image_path):
        try:
            result = self.backend.translate_image(image_path)
            error = None
        except Exception as exc:
            result = None
            error = str(exc)
            log(f"ocr translate failed: {error}")
        finally:
            try:
                Path(image_path).unlink(missing_ok=True)
            except OSError as exc:
                log(f"failed to delete temp capture: {exc}")

        self.root.after(0, lambda: self._finish_ocr_translation(result, error))

    def _finish_ocr_translation(self, result, error):
        self.ocr_active = False
        if error:
            self._show_short_message(error)
            return

        self.append_translation_result(result)
        self.note_store.append_vocabulary(result)
        self.show_window()

    def append_translation_result(self, result):
        self._remove_placeholder()
        current = self.text.get("1.0", "end-1c")
        if current.strip():
            self.text.insert("end", "\n\n")

        self.text.insert("end", self.note_store.format_note_record(result))
        self.text.see("end")
        self.save_note()

    def _show_short_message(self, message):
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        label = tk.Label(
            toast,
            text=message,
            bg=UI_TOAST_BG,
            fg=UI_TOAST_FG,
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
            content = note_file.read_text(encoding="utf-8")
            if content:
                self.text.insert("1.0", content)
                return

        self._insert_placeholder()

    def _insert_placeholder(self):
        self.text.insert("1.0", PLACEHOLDER_TEXT)
        self.text.tag_add("placeholder", "1.0", "end")
        self.text.tag_config("placeholder", foreground=UI_MUTED_TEXT)
        self.text.bind("<FocusIn>", self._remove_placeholder, add="+")

    def _is_placeholder_active(self):
        return bool(self.text.tag_ranges("placeholder")) and (
            self.text.get("1.0", "end-1c") == PLACEHOLDER_TEXT
        )

    def _remove_placeholder(self, _event=None):
        if self._is_placeholder_active():
            self.text.delete("1.0", "end")
            self.text.tag_remove("placeholder", "1.0", "end")

    def _clear_note(self):
        self.text.delete("1.0", "end")
        self.save_note()
        self._insert_placeholder()
        self.text.focus_set()

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
        return "break"

    def _finish_resize(self, _event):
        self._save_state()
        return "break"

    def _move_near_pointer(self, pointer_x, pointer_y):
        self.root.update_idletasks()
        width, height = self._current_window_size()

        screen_x = 0
        screen_y = 0
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        right = screen_x + screen_width
        bottom = screen_y + screen_height

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
        STATE_FILE.write_text(
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
            encoding="utf-8",
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
