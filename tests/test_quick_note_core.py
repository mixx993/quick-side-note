import json
import queue
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import quick_note


class CodexOutputParsingTests(unittest.TestCase):
    def test_parse_strict_json(self):
        result = quick_note.parse_codex_translation_output(
            '{"source_text":"obscure","translation":"模糊的；晦涩的"}'
        )

        self.assertEqual(result.source_text, "obscure")
        self.assertEqual(result.translation, "模糊的；晦涩的")

    def test_parse_markdown_wrapped_json(self):
        result = quick_note.parse_codex_translation_output(
            '```json\n{"source_text":"serendipity","translation":"意外发现美好事物的能力"}\n```'
        )

        self.assertEqual(result.source_text, "serendipity")
        self.assertEqual(result.translation, "意外发现美好事物的能力")

    def test_parse_json_with_trailing_text(self):
        result = quick_note.parse_codex_translation_output(
            '{"source_text":"margin","translation":"edge"}\nextra explanation'
        )

        self.assertEqual(result.source_text, "margin")
        self.assertEqual(result.translation, "edge")

    def test_reject_empty_translation(self):
        with self.assertRaises(ValueError):
            quick_note.parse_codex_translation_output(
                '{"source_text":"obscure","translation":""}'
            )

    def test_extracts_codex_json_error_message(self):
        message = quick_note.extract_codex_error_message(
            'ERROR: {"error":{"message":"model unavailable"}}\n'
        )

        self.assertEqual(message, "model unavailable")


class VocabularyStoreTests(unittest.TestCase):
    def test_append_jsonl_record(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "vocabulary.jsonl"
            store = quick_note.NoteStore(Path(temp_dir) / "note.txt", path)
            result = quick_note.TranslationResult("obscure", "模糊的；晦涩的")

            store.append_vocabulary(result)

            rows = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(rows), 1)
            row = json.loads(rows[0])
            self.assertEqual(row["source_text"], "obscure")
            self.assertEqual(row["translation"], "模糊的；晦涩的")
            self.assertIn("created_at", row)


class VocabularyOrganizerTests(unittest.TestCase):
    def test_extracts_translated_pairs_and_plain_word_lines(self):
        entries = quick_note.extract_vocabulary_entries_from_text(
            "原文：candid\n译文：坦率的\n\naesthetic\n\n不是单词",
            source="note.txt",
        )

        self.assertEqual(
            [(entry.term, entry.translation) for entry in entries],
            [("candid", "坦率的"), ("aesthetic", "")],
        )

    def test_normalizes_numbered_word_lines(self):
        entries = quick_note.extract_vocabulary_entries_from_text(
            "1. entire\n- analog\n3、documentary"
        )

        self.assertEqual(
            [entry.term for entry in entries],
            ["entire", "analog", "documentary"],
        )

    def test_collects_jsonl_and_note_entries_without_duplicates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            vocabulary = root / "vocabulary.jsonl"
            note = root / "note.txt"
            vocabulary.write_text(
                '{"source_text":"Candid","translation":"坦率的"}\n'
                '{broken}\n',
                encoding="utf-8",
            )
            note.write_text(
                "candid\n\n原文：analog\n译文：模拟的\n",
                encoding="utf-8",
            )

            entries = quick_note.collect_vocabulary_entries([note], vocabulary)

            self.assertEqual([entry.term.lower() for entry in entries], ["candid", "analog"])
            self.assertEqual(entries[0].translation, "坦率的")
            self.assertEqual(entries[1].translation, "模拟的")

    def test_learning_prompt_uses_fixed_study_pack_sections(self):
        prompt = quick_note.build_vocabulary_learning_prompt(
            [quick_note.VocabularyEntry("candid", "坦率的")]
        )

        self.assertIn("# 词汇学习包", prompt)
        self.assertIn("## 主题分组", prompt)
        self.assertIn("## 复习小测", prompt)
        self.assertIn("candid — 坦率的", prompt)

    def test_save_studio_output_uses_unique_markdown_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = quick_note.StudioOutput(
                mode="vocabulary_pack",
                title="词汇学习包",
                extension="md",
                content="# 词汇学习包",
            )
            now = quick_note.datetime(2026, 7, 10, 7, 30, 0)

            first = quick_note.save_studio_output(output, temp_dir, now=now)
            second = quick_note.save_studio_output(output, temp_dir, now=now)

            self.assertNotEqual(first, second)
            self.assertEqual(first.read_text(encoding="utf-8"), "# 词汇学习包\n")
            self.assertTrue(second.exists())


class SafeStorageTests(unittest.TestCase):
    def test_atomic_write_keeps_backup_and_replaces_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "note.txt"
            path.write_text("old", encoding="utf-8")

            quick_note.atomic_write_text(path, "new")

            self.assertEqual(path.read_text(encoding="utf-8"), "new")
            self.assertEqual(
                quick_note.backup_file_for(path).read_text(encoding="utf-8"),
                "old",
            )

    def test_atomic_write_preserves_existing_file_when_backup_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "note.txt"
            path.write_text("old", encoding="utf-8")

            with patch("quick_note.shutil.copy2", side_effect=OSError("disk error")):
                with self.assertRaises(OSError):
                    quick_note.atomic_write_text(path, "new")

            self.assertEqual(path.read_text(encoding="utf-8"), "old")

    def test_state_reader_uses_backup_after_corruption(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"
            backup_path = quick_note.backup_file_for(state_path)
            state_path.write_text("{broken", encoding="utf-8")
            backup_path.write_text('{"active_page": 4}', encoding="utf-8")

            with patch.object(quick_note, "STATE_FILE", state_path):
                self.assertEqual(quick_note.read_state_data(), {"active_page": 4})

    def test_read_text_supports_legacy_gb18030_note(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "note.txt"
            path.write_bytes("旧版便签".encode("gb18030"))

            self.assertEqual(quick_note.read_text_with_fallback(path), "旧版便签")

    def test_discover_note_pages_keeps_existing_added_pages(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            note_dir = Path(temp_dir)
            (note_dir / "note-4.txt").write_text("four", encoding="utf-8")
            (note_dir / "note-8.txt").write_text("eight", encoding="utf-8")

            with patch.object(quick_note, "NOTE_DIR", note_dir):
                page_ids = [page["id"] for page in quick_note.discover_note_pages()]

            self.assertEqual(page_ids, [1, 2, 3, 4, 8])


class ApiConfigurationTests(unittest.TestCase):
    def test_plausible_api_key_rejects_empty_or_short_values(self):
        self.assertFalse(quick_note.is_plausible_api_key(""))
        self.assertFalse(quick_note.is_plausible_api_key("short"))

    def test_plausible_api_key_rejects_whitespace_inside_key(self):
        self.assertFalse(quick_note.is_plausible_api_key("token-valid part"))

    def test_plausible_api_key_accepts_long_token(self):
        self.assertTrue(quick_note.is_plausible_api_key("testtoken1234567890abcdefghijk"))


class AppSettingsTests(unittest.TestCase):
    def test_normalize_settings_uses_defaults_for_invalid_values(self):
        settings = quick_note.normalize_app_settings(
            {
                "side_button": "bad",
                "block_browser_key": None,
                "double_click_ms": "bad",
            }
        )

        self.assertEqual(settings["side_button"], "xbutton1")
        self.assertTrue(settings["block_browser_key"])
        self.assertEqual(settings["double_click_ms"], 300)
        self.assertEqual(settings["side_response_mode"], "compatibility")
        self.assertFalse(settings["allow_image_fallback"])

    def test_normalize_settings_clamps_double_click_interval(self):
        low = quick_note.normalize_app_settings({"double_click_ms": 1})
        high = quick_note.normalize_app_settings({"double_click_ms": 5000})

        self.assertEqual(low["double_click_ms"], quick_note.MIN_DOUBLE_CLICK_MS)
        self.assertEqual(high["double_click_ms"], quick_note.MAX_DOUBLE_CLICK_MS)

    def test_normalize_settings_rejects_unknown_side_response_mode(self):
        settings = quick_note.normalize_app_settings({"side_response_mode": "fast"})

        self.assertEqual(settings["side_response_mode"], "compatibility")

    def test_normalize_settings_supports_immediate_side_response_mode(self):
        settings = quick_note.normalize_app_settings({"side_response_mode": "immediate"})

        self.assertEqual(settings["side_response_mode"], "immediate")

    def test_side_button_value_supports_second_side_button(self):
        settings = quick_note.normalize_app_settings({"side_button": "xbutton2"})

        self.assertEqual(quick_note.side_button_value(settings), quick_note.XBUTTON2)

    def test_blocked_browser_keys_follow_side_button_setting(self):
        settings = quick_note.normalize_app_settings({"side_button": "xbutton2"})

        self.assertEqual(
            quick_note.blocked_browser_keys_for_settings(settings),
            {quick_note.VK_BROWSER_FORWARD},
        )

    def test_blocked_browser_keys_can_be_disabled(self):
        settings = quick_note.normalize_app_settings({"block_browser_key": False})

        self.assertEqual(quick_note.blocked_browser_keys_for_settings(settings), set())

    def test_build_startup_command_for_packaged_app(self):
        command = quick_note.build_app_launch_command(
            executable_path=r"C:\Program Files\QuickSideNote\QuickSideNote.exe",
            frozen=True,
        )

        self.assertEqual(
            command,
            r'"C:\Program Files\QuickSideNote\QuickSideNote.exe"',
        )

    def test_build_startup_command_for_source_app(self):
        command = quick_note.build_app_launch_command(
            executable_path=r"C:\Python\pythonw.exe",
            script_path=r"C:\app\quick_note.py",
            frozen=False,
        )

        self.assertEqual(command, r'"C:\Python\pythonw.exe" "C:\app\quick_note.py"')


class NotePageTests(unittest.TestCase):
    def test_note_file_for_page_maps_three_pages(self):
        self.assertEqual(quick_note.note_file_for_page(1).name, "note.txt")
        self.assertEqual(quick_note.note_file_for_page(2).name, "note-2.txt")
        self.assertEqual(quick_note.note_file_for_page(3).name, "note-3.txt")

    def test_note_file_for_page_supports_added_pages(self):
        self.assertEqual(quick_note.note_file_for_page(0).name, "note.txt")
        self.assertEqual(quick_note.note_file_for_page(4).name, "note-4.txt")

    def test_normalize_note_pages_preserves_default_and_added_pages(self):
        pages = quick_note.normalize_note_pages(
            [
                {"id": 4, "name": "单词"},
                {"id": 5, "name": ""},
                {"id": 4, "name": "duplicate"},
            ]
        )

        self.assertEqual(
            pages,
            [
                {"id": 1, "name": "1"},
                {"id": 2, "name": "2"},
                {"id": 3, "name": "3"},
                {"id": 4, "name": "单词"},
                {"id": 5, "name": "5"},
            ],
        )

    def test_normalize_note_pages_allows_renaming_default_pages(self):
        pages = quick_note.normalize_note_pages([{"id": 1, "name": "工作"}])

        self.assertEqual(pages[0], {"id": 1, "name": "工作"})

    def test_normalized_note_page_uses_existing_page_ids(self):
        pages = quick_note.normalize_note_pages([{"id": 4, "name": "单词"}])

        self.assertEqual(quick_note.normalized_note_page(4, pages), 4)
        self.assertEqual(quick_note.normalized_note_page(99, pages), 1)

    def test_note_record_omits_timestamp(self):
        store = quick_note.NoteStore("note.txt", "vocabulary.jsonl")
        result = quick_note.TranslationResult("verification", "validation")

        record = store.format_note_record(result)

        self.assertEqual(record, "原文：verification\n译文：validation\n")
        self.assertNotIn("[", record)


class PageRailLayoutTests(unittest.TestCase):
    def test_page_rail_width_has_minimum(self):
        self.assertEqual(
            quick_note.clamp_page_rail_width(1),
            quick_note.PAGE_RAIL_MIN_WIDTH,
        )

    def test_page_rail_width_has_maximum(self):
        self.assertEqual(
            quick_note.clamp_page_rail_width(1000),
            quick_note.PAGE_RAIL_MAX_WIDTH,
        )

    def test_page_rail_width_adds_label_padding(self):
        self.assertEqual(
            quick_note.clamp_page_rail_width(80),
            80 + quick_note.PAGE_LABEL_PADDING_X * 2,
        )

    def test_numeric_page_label_is_centered(self):
        self.assertEqual(quick_note.page_label_anchor("2"), "center")

    def test_named_page_label_is_left_aligned(self):
        self.assertEqual(quick_note.page_label_anchor("单词本"), "w")


class WindowGeometryTests(unittest.TestCase):
    def test_normalize_keeps_custom_size_and_position(self):
        geometry = quick_note.normalize_window_geometry("640x360+12-8")

        self.assertEqual(geometry, "640x360+12-8")

    def test_normalize_clamps_to_minimum_size(self):
        geometry = quick_note.normalize_window_geometry("120x90-20+30")

        self.assertEqual(geometry, "380x300-20+30")

    def test_normalize_uses_default_for_invalid_geometry(self):
        geometry = quick_note.normalize_window_geometry("bad")

        self.assertEqual(geometry, "440x340+760+260")

    def test_parse_window_size_reads_saved_size(self):
        size = quick_note.parse_window_size("560x340+10+20")

        self.assertEqual(size, (560, 340))

    def test_dialog_geometry_respects_work_area_fraction(self):
        geometry = quick_note.clamp_dialog_to_work_area(
            820,
            640,
            (0, 0, 800, 600),
        )

        self.assertEqual(geometry, (720, 540, 40, 30))

    def test_dialog_geometry_keeps_small_work_area_onscreen(self):
        geometry = quick_note.clamp_dialog_to_work_area(
            820,
            640,
            (-1280, 0, 0, 720),
        )

        self.assertEqual(geometry, (820, 640, -1050, 40))


class CodexCliBackendTests(unittest.TestCase):
    def test_backend_parses_stdout(self):
        backend = quick_note.CodexCliBackend(timeout_seconds=5)
        fake_completed = quick_note.subprocess.CompletedProcess(
            args=["codex"],
            returncode=0,
            stdout='{"source_text":"obscure","translation":"模糊的；晦涩的"}',
            stderr="",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "capture.png"
            image_path.write_bytes(b"fake")
            with patch("quick_note.shutil.which", return_value="codex"):
                with patch("quick_note.subprocess.run", return_value=fake_completed) as run:
                    result = backend.translate_image(image_path)

        self.assertEqual(result.source_text, "obscure")
        self.assertEqual(result.translation, "模糊的；晦涩的")
        self.assertIn("--model", run.call_args.args[0])
        self.assertIn(quick_note.CODEX_MODEL, run.call_args.args[0])
        self.assertIn(f'model_reasoning_effort="{quick_note.CODEX_REASONING_EFFORT}"', run.call_args.args[0])
        self.assertIn("--image", run.call_args.args[0])
        self.assertEqual(run.call_args.args[0][-1], "-")
        self.assertEqual(run.call_args.kwargs["input"], quick_note.CODEX_PROMPT)
        self.assertEqual(
            run.call_args.kwargs["creationflags"],
            quick_note.subprocess.CREATE_NO_WINDOW,
        )
        self.assertIsNotNone(run.call_args.kwargs["startupinfo"])

    def test_backend_raises_on_nonzero_exit(self):
        backend = quick_note.CodexCliBackend(timeout_seconds=5)
        fake_completed = quick_note.subprocess.CompletedProcess(
            args=["codex"],
            returncode=1,
            stdout="",
            stderr="not logged in",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "capture.png"
            image_path.write_bytes(b"fake")
            with patch("quick_note.shutil.which", return_value="codex"):
                with patch("quick_note.subprocess.run", return_value=fake_completed):
                    with self.assertRaises(RuntimeError):
                        backend.translate_image(image_path)

    def test_backend_falls_back_when_configured_model_is_unsupported(self):
        backend = quick_note.CodexCliBackend(timeout_seconds=5)
        unsupported_completed = quick_note.subprocess.CompletedProcess(
            args=["codex"],
            returncode=1,
            stdout="",
            stderr=(
                'ERROR: {"error":{"message":"The '
                "'gpt-5.4-mini' model is not supported"
                ' when using Codex with a ChatGPT account."}}'
            ),
        )
        fallback_completed = quick_note.subprocess.CompletedProcess(
            args=["codex"],
            returncode=0,
            stdout='{"source_text":"obscure","translation":"blurred"}',
            stderr="",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "capture.png"
            image_path.write_bytes(b"fake")
            with patch("quick_note.shutil.which", return_value="codex"):
                with patch("quick_note.log"):
                    with patch(
                        "quick_note.subprocess.run",
                        side_effect=[unsupported_completed, fallback_completed],
                    ) as run:
                        result = backend.translate_image(image_path)

        self.assertEqual(result.source_text, "obscure")
        self.assertEqual(run.call_count, 2)
        self.assertIn(quick_note.CODEX_MODEL, run.call_args_list[0].args[0])
        self.assertNotIn("--model", run.call_args_list[1].args[0])


class FastTranslationBackendTests(unittest.TestCase):
    def test_fast_backend_uses_ocr_text_translation(self):
        class FakeOcr:
            def recognize_text(self, image_path):
                self.image_path = image_path
                return " margin\n"

        class FakeText:
            def translate_text(self, source_text):
                self.source_text = source_text
                return quick_note.TranslationResult(source_text, "边缘；页边距")

        class FakeFallback:
            def __init__(self):
                self.called = False

            def translate_image(self, _image_path):
                self.called = True
                return quick_note.TranslationResult("fallback", "兜底")

        fallback = FakeFallback()
        backend = quick_note.FastTranslationBackend(fallback)
        backend.ocr_backend = FakeOcr()
        backend.text_backend = FakeText()

        with patch("quick_note.log"):
            result = backend.translate_image("capture.png")

        self.assertEqual(result.source_text, "margin")
        self.assertEqual(result.translation, "边缘；页边距")
        self.assertEqual(backend.ocr_backend.image_path, "capture.png")
        self.assertEqual(backend.text_backend.source_text, "margin")
        self.assertFalse(fallback.called)

    def test_fast_backend_logs_only_ocr_text_length(self):
        class FakeOcr:
            def recognize_text(self, _image_path):
                return "confidential phrase"

        class FakeText:
            def translate_text(self, source_text):
                return quick_note.TranslationResult(source_text, "机密短语")

        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "quick_note.log"
            backend = quick_note.FastTranslationBackend(None)
            backend.ocr_backend = FakeOcr()
            backend.text_backend = FakeText()

            with patch.object(quick_note, "LOG_FILE", log_path):
                backend.translate_image("capture.png")

            log_text = log_path.read_text(encoding="utf-8")
            self.assertIn("text_length=19", log_text)
            self.assertNotIn("confidential phrase", log_text)

    def test_fast_backend_falls_back_when_fast_path_fails(self):
        class BrokenOcr:
            def recognize_text(self, _image_path):
                raise RuntimeError("ocr failed")

        class FakeText:
            def translate_text(self, _source_text):
                raise AssertionError("text backend should not be called")

        class FakeFallback:
            def __init__(self):
                self.image_path = None

            def translate_image(self, image_path):
                self.image_path = image_path
                return quick_note.TranslationResult("obscure", "模糊的")

        fallback = FakeFallback()
        backend = quick_note.FastTranslationBackend(fallback, image_fallback_enabled=True)
        backend.ocr_backend = BrokenOcr()
        backend.text_backend = FakeText()

        with patch("quick_note.log"):
            result = backend.translate_image("capture.png")

        self.assertEqual(result.source_text, "obscure")
        self.assertEqual(result.translation, "模糊的")
        self.assertEqual(fallback.image_path, "capture.png")

    def test_fast_backend_keeps_image_fallback_disabled_by_default(self):
        class BrokenOcr:
            def recognize_text(self, _image_path):
                raise RuntimeError("ocr failed")

        class FakeFallback:
            def translate_image(self, _image_path):
                raise AssertionError("image fallback must not run")

        backend = quick_note.FastTranslationBackend(FakeFallback())
        backend.ocr_backend = BrokenOcr()

        with patch("quick_note.log"):
            with self.assertRaisesRegex(RuntimeError, "本地 OCR"):
                backend.translate_image("capture.png")

    def test_fast_backend_does_not_fall_back_when_text_translation_fails(self):
        class FakeOcr:
            def recognize_text(self, _image_path):
                return "margin"

        class BrokenText:
            def translate_text(self, _source_text):
                raise RuntimeError("bad text response")

        class FakeFallback:
            def __init__(self):
                self.called = False

            def translate_image(self, _image_path):
                self.called = True
                return quick_note.TranslationResult("fallback", "fallback")

        fallback = FakeFallback()
        backend = quick_note.FastTranslationBackend(fallback)
        backend.ocr_backend = FakeOcr()
        backend.text_backend = BrokenText()

        with patch("quick_note.log"):
            with self.assertRaises(RuntimeError):
                backend.translate_image("capture.png")

        self.assertFalse(fallback.called)


class SideButtonStateTests(unittest.TestCase):
    def test_selection_hint_uses_corner_opposite_pointer(self):
        self.assertEqual(
            quick_note.opposite_corner_position(1920, 1080, 430, 70, 100, 100),
            (1462, 982),
        )
        self.assertEqual(
            quick_note.opposite_corner_position(1920, 1080, 430, 70, 1800, 900),
            (28, 28),
        )

    def test_starting_selection_hides_pointer_task_hud(self):
        class FakeRoot:
            def state(self):
                return "normal"

        class FakeOverlay:
            def __init__(self, _root, _callback):
                self.started = False

            def start(self):
                self.started = True

        app = SimpleNamespace(
            root=FakeRoot(),
            visible=True,
            ocr_active=False,
            capture_overlay=None,
            task_restore_visible=False,
            hidden=False,
            hud_hidden=0,
            statuses=[],
        )
        app._set_ocr_status = lambda active, text=None: app.statuses.append(
            (active, text)
        )
        app._hide_task_hud = lambda: setattr(app, "hud_hidden", app.hud_hidden + 1)
        app.hide_and_save = lambda: setattr(app, "hidden", True)
        app._on_capture_complete = lambda *_args: None
        app._show_task_failure = lambda _message: None

        with patch("quick_note.ScreenCaptureOverlay", FakeOverlay):
            quick_note.QuickNoteApp.start_ocr_selection(app)

        self.assertEqual(app.hud_hidden, 1)
        self.assertTrue(app.hidden)
        self.assertTrue(app.capture_overlay.started)
        self.assertEqual(app.statuses[-1], (True, "框选中"))

    def test_side_click_cancels_active_ocr_overlay(self):
        class FakeRoot:
            def __init__(self):
                self.after_cancel_calls = 0
                self.after_calls = 0

            def after_cancel(self, _callback_id):
                self.after_cancel_calls += 1

            def after(self, *_args):
                self.after_calls += 1
                return "scheduled"

        class FakeOverlay:
            def __init__(self):
                self.cancel_calls = 0

            def cancel(self):
                self.cancel_calls += 1

        overlay = FakeOverlay()
        app = SimpleNamespace(
            root=FakeRoot(),
            ocr_active=True,
            pending_single_click="queued",
            capture_overlay=overlay,
            toggle_called=False,
        )

        def toggle_window(_pointer_x=None, _pointer_y=None):
            app.toggle_called = True

        app.toggle_window = toggle_window

        with patch("quick_note.log"):
            quick_note.QuickNoteApp._handle_side_click(app, 10, 20)

        self.assertIsNone(app.pending_single_click)
        self.assertEqual(app.root.after_cancel_calls, 1)
        self.assertEqual(app.root.after_calls, 0)
        self.assertEqual(overlay.cancel_calls, 1)
        self.assertFalse(app.toggle_called)

    def test_capture_error_releases_ocr_active(self):
        messages = []
        app = SimpleNamespace(
            ocr_active=True,
            capture_overlay="overlay",
            _show_short_message=messages.append,
        )

        with patch("quick_note.log"):
            quick_note.QuickNoteApp._on_capture_complete(app, None, "failed")

        self.assertFalse(app.ocr_active)
        self.assertIsNone(app.capture_overlay)
        self.assertEqual(messages, ["failed"])

    def test_single_side_click_uses_configured_double_click_interval(self):
        class FakeRoot:
            def __init__(self):
                self.after_delay = None

            def after(self, delay, _callback):
                self.after_delay = delay
                return "scheduled"

        app = SimpleNamespace(
            root=FakeRoot(),
            ocr_active=False,
            pending_single_click=None,
            settings=quick_note.normalize_app_settings({"double_click_ms": 450}),
        )

        quick_note.QuickNoteApp._handle_side_click(app, 10, 20)

        self.assertEqual(app.pending_single_click, "scheduled")
        self.assertEqual(app.root.after_delay, 450)

    def test_immediate_side_click_starts_ocr_without_double_click_wait(self):
        app = SimpleNamespace(
            ocr_active=False,
            pending_single_click=None,
            settings=quick_note.normalize_app_settings(
                {"side_response_mode": "immediate"}
            ),
            started=False,
        )

        def start_ocr_selection():
            app.started = True

        app.start_ocr_selection = start_ocr_selection
        quick_note.QuickNoteApp._handle_side_click(app, 10, 20)

        self.assertTrue(app.started)
        self.assertIsNone(app.pending_single_click)


class TranslationTaskTests(unittest.TestCase):
    def test_worker_only_enqueues_result(self):
        class FakeBackend:
            def translate_image(self, _image_path):
                return quick_note.TranslationResult("margin", "页边距")

        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "capture.png"
            image_path.write_bytes(b"image")
            task = quick_note.TranslationTask(7, image_path)
            app = SimpleNamespace(backend=FakeBackend(), events=queue.Queue())

            quick_note.QuickNoteApp._translate_capture_worker(app, task)

            event = app.events.get_nowait()
            self.assertEqual(event[0], "translation_done")
            self.assertEqual(event[1], 7)
            self.assertEqual(event[2].translation, "页边距")
            self.assertFalse(image_path.exists())

    def test_cancelled_task_result_is_ignored(self):
        current = quick_note.TranslationTask(2, Path("current.png"))
        app = SimpleNamespace(
            translation_task=current,
            ocr_active=True,
            _show_short_message=lambda _message: self.fail("stale result displayed"),
        )

        with patch("quick_note.log"):
            quick_note.QuickNoteApp._finish_ocr_translation(
                app,
                1,
                quick_note.TranslationResult("old", "旧结果"),
                None,
            )

        self.assertIs(app.translation_task, current)
        self.assertTrue(app.ocr_active)


class HookLifecycleTests(unittest.TestCase):
    def test_failed_hook_install_exits_without_message_loop(self):
        fake_user32 = SimpleNamespace(
            SetWindowsHookExW=lambda *_args: 0,
            GetMessageW=lambda *_args: self.fail("message loop must not start"),
        )
        fake_kernel32 = SimpleNamespace(
            GetCurrentThreadId=lambda: 42,
            GetModuleHandleW=lambda _name: None,
        )
        hook = quick_note._WindowsHookBase(1, quick_note.ctypes.c_void_p(), "test")

        with patch("quick_note.user32", fake_user32), patch("quick_note.kernel32", fake_kernel32), patch(
            "quick_note.log"
        ):
            hook._run()

        self.assertIsNone(hook.hook_id)
        self.assertIsNone(hook.thread_id)
        self.assertEqual(hook.failure_count, 1)
        self.assertGreater(hook.next_retry_at, time.monotonic() - 1)


class WindowsCompatibilityTests(unittest.TestCase):
    def test_monitor_work_area_falls_back_to_primary_dimensions(self):
        with patch("quick_note.user32", SimpleNamespace(MonitorFromPoint=lambda *_args: 0)):
            area = quick_note.monitor_work_area_for_point(10, 20, 1920, 1080)

        self.assertEqual(area, (0, 0, 1920, 1080))

    def test_tray_right_click_queues_menu_on_main_event_loop(self):
        events = queue.Queue()
        tray = object.__new__(quick_note.WindowsTrayIcon)
        tray.app = SimpleNamespace(events=events)
        tray.taskbar_created_message = -1

        result = tray._window_proc(
            None,
            quick_note.WM_TRAYICON,
            quick_note.TRAY_ICON_ID,
            quick_note.WM_RBUTTONUP,
        )

        self.assertEqual(result, 0)
        self.assertEqual(events.get_nowait(), ("tray_menu",))


class PackagingTests(unittest.TestCase):
    def test_build_script_checks_native_exit_codes_and_exact_artifacts(self):
        script = Path("scripts/build_installer.ps1").read_text(encoding="utf-8")

        self.assertIn("Assert-NativeSuccess \"PyInstaller\"", script)
        self.assertIn("Assert-NativeSuccess \"Inno Setup\"", script)
        self.assertIn("Assert-AppExecutableVersion", script)
        self.assertIn("build-manifest.json", script)
        self.assertIn("QuickSideNote_Setup_v$appVersion.exe", script)
        self.assertIn("Compress-Archive", script)

    def test_uninstaller_removes_only_the_app_startup_value(self):
        installer = Path("installer/QuickSideNote.iss").read_text(encoding="utf-8")

        self.assertIn("[Registry]", installer)
        self.assertIn('ValueName: "QuickSideNote"', installer)
        self.assertIn("uninsdeletevalue", installer)


if __name__ == "__main__":
    unittest.main()
