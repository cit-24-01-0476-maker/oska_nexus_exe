import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from commands.parser import CommandParser
from commands.executor import CommandExecutor

class DesktopAutomationTests(unittest.TestCase):
    def setUp(self):
        self.executor = CommandExecutor()

    def test_parser_screenshots(self):
        cases = [
            ("screenshot ganna", "take_screenshot"),
            ("screenshot ekak gahanna", "take_screenshot"),
            ("ස්ක්‍රීන්ෂොට් එකක් ගන්න", "take_screenshot"),
            ("take a screenshot", "take_screenshot"),
            ("capture screen", "take_screenshot"),
        ]
        for phrase, expected_intent in cases:
            res = CommandParser.parse(phrase)
            self.assertEqual(res["intent"], expected_intent, f"Failed for '{phrase}'")

    def test_parser_window_management(self):
        cases = [
            ("show desktop", "show_desktop"),
            ("desktop eka pennanna", "show_desktop"),
            ("ඩෙස්ක්ටොප් එක පෙන්වන්න", "show_desktop"),
            ("minimize karanna", "minimize_window"),
            ("වින්ඩෝ එක මිනිමයිස් කරන්න", "minimize_window"),
            ("maximize karanna", "maximize_window"),
            ("fullscreen karanna", "maximize_window"),
            ("වින්ඩෝ එක මැක්සිමයිස් කරන්න", "maximize_window"),
            ("close window", "close_window"),
            ("window eka wahanna", "close_window"),
            ("වින්ඩෝ එක වහන්න", "close_window"),
            ("switch window", "switch_window"),
            ("alt tab", "switch_window"),
        ]
        for phrase, expected_intent in cases:
            res = CommandParser.parse(phrase)
            self.assertEqual(res["intent"], expected_intent, f"Failed for '{phrase}'")

    def test_parser_browser_tabs(self):
        cases = [
            ("new tab", "new_tab"),
            ("aluth tab ekak", "new_tab"),
            ("අලුත් ටැබ් එකක්", "new_tab"),
            ("close tab", "close_tab"),
            ("tab eka wahanna", "close_tab"),
            ("ටැබ් එක වහන්න", "close_tab"),
            ("reopen tab", "reopen_tab"),
            ("kalin tab eka", "reopen_tab"),
            ("refresh karanna", "refresh_page"),
            ("page eka refresh karanna", "refresh_page"),
            ("පේජ් එක රිෆ්‍රෙෂ් කරන්න", "refresh_page"),
        ]
        for phrase, expected_intent in cases:
            res = CommandParser.parse(phrase)
            self.assertEqual(res["intent"], expected_intent, f"Failed for '{phrase}'")

    def test_parser_keyboard_and_typing(self):
        # Type
        res = CommandParser.parse("type karanna hello world")
        self.assertEqual(res["intent"], "type_text")
        self.assertEqual(res["args"]["text"], "hello world")

        res_sin = CommandParser.parse("ටයිප් කරන්න OSKA NEXUS")
        self.assertEqual(res_sin["intent"], "type_text")
        self.assertEqual(res_sin["args"]["text"], "OSKA NEXUS")

        # Key press
        self.assertEqual(CommandParser.parse("enter obanna")["intent"], "press_key")
        self.assertEqual(CommandParser.parse("press enter")["intent"], "press_key")
        self.assertEqual(CommandParser.parse("escape obanna")["intent"], "press_key")

    def test_parser_clipboard_and_mouse(self):
        self.assertEqual(CommandParser.parse("copy karanna")["intent"], "copy_selection")
        self.assertEqual(CommandParser.parse("paste karanna")["intent"], "paste_clipboard")
        self.assertEqual(CommandParser.parse("okkoma select karanna")["intent"], "select_all")
        self.assertEqual(CommandParser.parse("save karanna")["intent"], "save_file")
        self.assertEqual(CommandParser.parse("click karanna")["intent"], "mouse_click")
        self.assertEqual(CommandParser.parse("double click karanna")["intent"], "mouse_double_click")
        self.assertEqual(CommandParser.parse("right click karanna")["intent"], "mouse_right_click")
        self.assertEqual(CommandParser.parse("scroll down karanna")["intent"], "mouse_scroll")
        self.assertEqual(CommandParser.parse("scroll up karanna")["intent"], "mouse_scroll")

    def test_parser_folder_and_recycle_bin(self):
        res = CommandParser.parse("desktop eke TestProjects folder ekak hadanna")
        self.assertEqual(res["intent"], "create_folder")
        self.assertIn("TestProjects", res["args"]["folder_name"])

        res2 = CommandParser.parse("empty recycle bin")
        self.assertEqual(res2["intent"], "empty_recycle_bin")

        res3 = CommandParser.parse("recycle bin eka as karanna")
        self.assertEqual(res3["intent"], "empty_recycle_bin")

    def test_parser_system_utilities(self):
        self.assertEqual(CommandParser.parse("task manager open karanna")["intent"], "open_system_utility")
        self.assertEqual(CommandParser.parse("control panel")["intent"], "open_system_utility")
        self.assertEqual(CommandParser.parse("wifi settings")["intent"], "open_system_utility")
        self.assertEqual(CommandParser.parse("bluetooth settings")["intent"], "open_system_utility")

    @patch("windows.desktop_automation.DesktopAutomation.take_screenshot", return_value=(True, "C:\\mock\\shot.png"))
    def test_executor_screenshot(self, mock_shot):
        parsed = CommandParser.parse("ස්ක්‍රීන්ෂොට් එකක් ගන්න")
        res = self.executor.execute(parsed)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertIn("Pictures", res["response"])
        mock_shot.assert_called_once()

    @patch("windows.desktop_automation.DesktopAutomation.show_desktop", return_value=(True, "ok"))
    def test_executor_show_desktop(self, mock_show):
        parsed = CommandParser.parse("desktop eka pennanna")
        res = self.executor.execute(parsed)
        self.assertEqual(res["status"], "SUCCESS")
        mock_show.assert_called_once()

if __name__ == '__main__':
    unittest.main()
