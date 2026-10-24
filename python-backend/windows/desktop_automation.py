import os
import time
import datetime
import subprocess
import ctypes
from ctypes import wintypes
from PIL import Image
import pyautogui
from typing import Tuple, Optional

# Disable PyAutoGUI fail-safe pause so actions execute smoothly
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

def _capture_screen_native():
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    w = user32.GetSystemMetrics(0)
    h = user32.GetSystemMetrics(1)
    hdc = user32.GetDC(None)
    mem_dc = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(mem_dc, bmp)
    # SRCCOPY = 0x00CC0020
    gdi32.BitBlt(mem_dc, 0, 0, w, h, hdc, 0, 0, 0x00CC0020)
    
    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ('biSize', wintypes.DWORD),
            ('biWidth', wintypes.LONG),
            ('biHeight', wintypes.LONG),
            ('biPlanes', wintypes.WORD),
            ('biBitCount', wintypes.WORD),
            ('biCompression', wintypes.DWORD),
            ('biSizeImage', wintypes.DWORD),
            ('biXPelsPerMeter', wintypes.LONG),
            ('biYPelsPerMeter', wintypes.LONG),
            ('biClrUsed', wintypes.DWORD),
            ('biClrImportant', wintypes.DWORD)
        ]
    
    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = -h
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0
    buffer = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(mem_dc, bmp, 0, h, buffer, ctypes.byref(bmi), 0)
    
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mem_dc)
    user32.ReleaseDC(None, hdc)
    
    im = Image.frombuffer('RGBA', (w, h), buffer, 'raw', 'BGRA', 0, 1)
    return im.convert('RGB')
class DesktopAutomation:
    @staticmethod
    def take_screenshot() -> Tuple[bool, str]:
        """Captures a full screenshot of the screen and saves it to Pictures\\Screenshots."""
        try:
            screenshots_dir = os.path.expanduser(r"~\Pictures\Screenshots")
            os.makedirs(screenshots_dir, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"OSKA_Screenshot_{timestamp}.png"
            filepath = os.path.join(screenshots_dir, filename)
            try:
                img = _capture_screen_native()
            except Exception:
                img = pyautogui.screenshot()
            img.save(filepath)
            return True, filepath
        except Exception as e:
            return False, str(e)

    @staticmethod
    def show_desktop() -> Tuple[bool, str]:
        """Toggles Show Desktop (Win+D)."""
        try:
            pyautogui.hotkey('win', 'd')
            return True, "Show desktop toggled"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def minimize_active_window() -> Tuple[bool, str]:
        """Minimizes the currently active window (Win+Down)."""
        try:
            pyautogui.hotkey('win', 'down')
            return True, "Window minimized"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def maximize_active_window() -> Tuple[bool, str]:
        """Maximizes the currently active window (Win+Up)."""
        try:
            pyautogui.hotkey('win', 'up')
            return True, "Window maximized"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def close_active_window() -> Tuple[bool, str]:
        """Closes the currently active window (Alt+F4)."""
        try:
            pyautogui.hotkey('alt', 'f4')
            return True, "Closed active window"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def switch_window() -> Tuple[bool, str]:
        """Switches to the previous window (Alt+Tab)."""
        try:
            pyautogui.hotkey('alt', 'tab')
            return True, "Switched window"
        except Exception as e:
            return False, str(e)

    # ---------------- Browser / Tab Navigation ----------------
    @staticmethod
    def new_tab() -> Tuple[bool, str]:
        """Opens a new tab in browser/explorer (Ctrl+T)."""
        try:
            pyautogui.hotkey('ctrl', 't')
            return True, "New tab opened"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def close_tab() -> Tuple[bool, str]:
        """Closes the current tab in browser/editor (Ctrl+W)."""
        try:
            pyautogui.hotkey('ctrl', 'w')
            return True, "Tab closed"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def reopen_tab() -> Tuple[bool, str]:
        """Reopens the last closed tab (Ctrl+Shift+T)."""
        try:
            pyautogui.hotkey('ctrl', 'shift', 't')
            return True, "Reopened closed tab"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def refresh_page() -> Tuple[bool, str]:
        """Refreshes the active webpage/window (F5)."""
        try:
            pyautogui.press('f5')
            return True, "Page refreshed"
        except Exception as e:
            return False, str(e)

    # ---------------- Clipboard & Typing Automation ----------------
    @staticmethod
    def type_text(text: str) -> Tuple[bool, str]:
        """Types text into the active focused window."""
        try:
            # Short sleep to allow focus
            time.sleep(0.1)
            pyautogui.write(text, interval=0.015)
            return True, f"Typed: {text}"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def press_key(key: str) -> Tuple[bool, str]:
        """Presses a single key (enter, space, esc, backspace, etc.)."""
        try:
            pyautogui.press(key)
            return True, f"Pressed {key}"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def copy_selection() -> Tuple[bool, str]:
        """Copies selection to clipboard (Ctrl+C)."""
        try:
            pyautogui.hotkey('ctrl', 'c')
            return True, "Copied to clipboard"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def paste_clipboard() -> Tuple[bool, str]:
        """Pastes from clipboard (Ctrl+V)."""
        try:
            pyautogui.hotkey('ctrl', 'v')
            return True, "Pasted from clipboard"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def select_all() -> Tuple[bool, str]:
        """Selects all content (Ctrl+A)."""
        try:
            pyautogui.hotkey('ctrl', 'a')
            return True, "Selected all"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def save_file() -> Tuple[bool, str]:
        """Saves current document/code (Ctrl+S)."""
        try:
            pyautogui.hotkey('ctrl', 's')
            return True, "Saved file"
        except Exception as e:
            return False, str(e)

    # ---------------- Mouse Automation ----------------
    @staticmethod
    def mouse_click(button: str = 'left') -> Tuple[bool, str]:
        """Performs a mouse click at current cursor position."""
        try:
            pyautogui.click(button=button)
            return True, f"{button.capitalize()} click performed"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def mouse_double_click() -> Tuple[bool, str]:
        """Performs a double click at current cursor position."""
        try:
            pyautogui.doubleClick()
            return True, "Double click performed"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def mouse_scroll(direction: str = 'down') -> Tuple[bool, str]:
        """Scrolls up or down."""
        try:
            clicks = -450 if direction.lower() == 'down' else 450
            pyautogui.scroll(clicks)
            return True, f"Scrolled {direction}"
        except Exception as e:
            return False, str(e)

    # ---------------- File System Operations ----------------
    @staticmethod
    def create_folder(folder_name: str, location: str = "desktop") -> Tuple[bool, str]:
        """Creates a new folder on the Desktop or in Documents."""
        try:
            clean_name = folder_name.strip()
            if not clean_name:
                clean_name = "New Folder"
            base_dir = os.path.expanduser(r"~\Desktop") if location == "desktop" else os.path.expanduser(r"~\Documents")
            target = os.path.join(base_dir, clean_name)
            os.makedirs(target, exist_ok=True)
            return True, target
        except Exception as e:
            return False, str(e)

    @staticmethod
    def empty_recycle_bin() -> Tuple[bool, str]:
        """Empties the Windows Recycle Bin silently."""
        try:
            import ctypes
            # SHERB_NOCONFIRMATION = 0x00000001
            # SHERB_NOPROGRESSUI = 0x00000002
            # SHERB_NOSOUND = 0x00000004
            flags = 0x00000001 | 0x00000002 | 0x00000004
            res = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, flags)
            return True, "Recycle Bin emptied"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def open_system_utility(utility: str) -> Tuple[bool, str]:
        """Opens common Windows utilities."""
        util_map = {
            "task_manager": "taskmgr.exe",
            "control_panel": "control.exe",
            "device_manager": "devmgmt.msc",
            "disk_management": "diskmgmt.msc",
            "network_settings": "ms-settings:network",
            "bluetooth_settings": "ms-settings:bluetooth",
            "display_settings": "ms-settings:display",
            "sound_settings": "ms-settings:sound",
            "windows_update": "ms-settings:windowsupdate"
        }
        cmd = util_map.get(utility.lower().strip())
        if not cmd:
            return False, f"Unknown utility: {utility}"
        try:
            if cmd.startswith("ms-settings:") or cmd.endswith(".msc"):
                os.startfile(cmd)
            else:
                subprocess.Popen([cmd], shell=False)
            return True, f"Opened {utility}"
        except Exception as e:
            return False, str(e)
