import time
from datetime import datetime
from typing import Dict, Any, Tuple
from windows.apps import launch_application, open_url, open_folder
from windows.audio import set_system_volume, get_system_volume, set_system_mute
from windows.system_info import get_system_metrics
from windows.power import lock_workstation, execute_shutdown, execute_restart
from windows.desktop_automation import DesktopAutomation
from storage.database import get_connection, log_audit
from storage.reminders import create_reminder
from urllib.parse import quote_plus

class CommandExecutor:
    def __init__(self, routine_runner=None):
        self.routine_runner = routine_runner

    def execute(self, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        intent = intent_data.get("intent", "conversation")
        args = intent_data.get("args", {})

        result = {
            "intent": intent,
            "status": "SUCCESS", # SUCCESS, FAILED, REQUIRES_CONFIRMATION, CANCELLED
            "response": "",
            "spoken_response": "",
            "data": None
        }

        is_sin = args.get("is_sinhala", False)

        # 1. System Time
        if intent == "get_time":
            now = datetime.now()
            time_str = now.strftime("%I:%M %p")
            if is_sin:
                result["response"] = f"දැන් වේලාව {time_str}."
                result["spoken_response"] = f"දැන් වේලාව {time_str}."
            else:
                result["response"] = f"It is currently {time_str}."
                result["spoken_response"] = f"It is {time_str}."
            log_audit("GET_TIME", time_str, "SUCCESS")
            return result

        # 2. System Date
        if intent == "get_date":
            now = datetime.now()
            date_str = now.strftime("%A, %B %d, %Y")
            if is_sin:
                result["response"] = f"අද දිනය {date_str}."
                result["spoken_response"] = f"අද දිනය {date_str}."
            else:
                result["response"] = f"Today is {date_str}."
                result["spoken_response"] = f"Today is {date_str}."
            log_audit("GET_DATE", date_str, "SUCCESS")
            return result

        # -------------------------------------------------------------
        # Desktop Automation (Windows Control & PyAutoGUI)
        # -------------------------------------------------------------
        if intent == "take_screenshot":
            ok, val = DesktopAutomation.take_screenshot()
            if ok:
                result["response"] = f"ස්ක්‍රීන්ෂොට් එක සාර්ථකව ලබාගෙන Pictures ෆෝල්ඩරයේ සේව් කළා: {val}" if is_sin else f"Screenshot saved to {val}."
                result["spoken_response"] = "ස්ක්‍රීන්ෂොට් එකක් ගත්තා." if is_sin else "Screenshot captured."
                result["data"] = {"path": val}
            else:
                result["status"] = "FAILED"
                result["response"] = f"ස්ක්‍රීන්ෂොට් ලබාගැනීමට නොහැකි විය: {val}" if is_sin else f"Screenshot failed: {val}"
                result["spoken_response"] = "Screenshot failed."
            log_audit("TAKE_SCREENSHOT", str(ok), result["status"])
            return result

        if intent == "show_desktop":
            ok, msg = DesktopAutomation.show_desktop()
            result["response"] = "ඩෙස්ක්ටොප් එක පෙන්වනවා." if is_sin else "Showing desktop."
            result["spoken_response"] = result["response"]
            log_audit("SHOW_DESKTOP", "", "SUCCESS")
            return result

        if intent == "minimize_window":
            ok, msg = DesktopAutomation.minimize_active_window()
            result["response"] = "වින්ඩෝ එක මිනිමයිස් කළා." if is_sin else "Minimized active window."
            result["spoken_response"] = result["response"]
            log_audit("MINIMIZE_WINDOW", "", "SUCCESS")
            return result

        if intent == "maximize_window":
            ok, msg = DesktopAutomation.maximize_active_window()
            result["response"] = "වින්ඩෝ එක මැක්සිමයිස් කළා." if is_sin else "Maximized active window."
            result["spoken_response"] = result["response"]
            log_audit("MAXIMIZE_WINDOW", "", "SUCCESS")
            return result

        if intent == "close_window":
            ok, msg = DesktopAutomation.close_active_window()
            result["response"] = "වින්ඩෝ එක වැසුවා." if is_sin else "Closed active window."
            result["spoken_response"] = result["response"]
            log_audit("CLOSE_WINDOW", "", "SUCCESS")
            return result

        if intent == "switch_window":
            ok, msg = DesktopAutomation.switch_window()
            result["response"] = "වින්ඩෝ මාරු කළා." if is_sin else "Switched window."
            result["spoken_response"] = result["response"]
            log_audit("SWITCH_WINDOW", "", "SUCCESS")
            return result

        if intent == "new_tab":
            ok, msg = DesktopAutomation.new_tab()
            result["response"] = "අලුත් ටැබ් එකක් විවෘත කළා." if is_sin else "Opened new tab."
            result["spoken_response"] = result["response"]
            log_audit("NEW_TAB", "", "SUCCESS")
            return result

        if intent == "close_tab":
            ok, msg = DesktopAutomation.close_tab()
            result["response"] = "ටැබ් එක වැසුවා." if is_sin else "Closed tab."
            result["spoken_response"] = result["response"]
            log_audit("CLOSE_TAB", "", "SUCCESS")
            return result

        if intent == "reopen_tab":
            ok, msg = DesktopAutomation.reopen_tab()
            result["response"] = "කලින් වැසූ ටැබ් එක නැවත විවෘත කළා." if is_sin else "Reopened closed tab."
            result["spoken_response"] = result["response"]
            log_audit("REOPEN_TAB", "", "SUCCESS")
            return result

        if intent == "refresh_page":
            ok, msg = DesktopAutomation.refresh_page()
            result["response"] = "පිටුව නැවත ප්‍රබෝධමත් කළා." if is_sin else "Refreshed page."
            result["spoken_response"] = result["response"]
            log_audit("REFRESH_PAGE", "", "SUCCESS")
            return result

        if intent == "type_text":
            text_to_type = args.get("text", "")
            ok, msg = DesktopAutomation.type_text(text_to_type)
            result["response"] = f"'{text_to_type}' ලෙස ටයිප් කළා." if is_sin else f"Typed: '{text_to_type}'"
            result["spoken_response"] = "ටයිප් කළා." if is_sin else f"Typed {text_to_type}."
            log_audit("TYPE_TEXT", text_to_type, "SUCCESS" if ok else "FAILED")
            return result

        if intent == "press_key":
            key_name = args.get("key", "enter")
            ok, msg = DesktopAutomation.press_key(key_name)
            result["response"] = f"{key_name} යතුර එබුවා." if is_sin else f"Pressed {key_name}."
            result["spoken_response"] = result["response"]
            log_audit("PRESS_KEY", key_name, "SUCCESS" if ok else "FAILED")
            return result

        if intent == "copy_selection":
            ok, msg = DesktopAutomation.copy_selection()
            result["response"] = "පිටපත් කරගත්තා." if is_sin else "Copied to clipboard."
            result["spoken_response"] = result["response"]
            log_audit("COPY_SELECTION", "", "SUCCESS")
            return result

        if intent == "paste_clipboard":
            ok, msg = DesktopAutomation.paste_clipboard()
            result["response"] = "අලවනු ලැබුවා." if is_sin else "Pasted from clipboard."
            result["spoken_response"] = result["response"]
            log_audit("PASTE_CLIPBOARD", "", "SUCCESS")
            return result

        if intent == "select_all":
            ok, msg = DesktopAutomation.select_all()
            result["response"] = "සියල්ල තෝරා ගත්තා." if is_sin else "Selected all."
            result["spoken_response"] = result["response"]
            log_audit("SELECT_ALL", "", "SUCCESS")
            return result

        if intent == "save_file":
            ok, msg = DesktopAutomation.save_file()
            result["response"] = "ගොනුව සුරැකුවා." if is_sin else "Saved file."
            result["spoken_response"] = result["response"]
            log_audit("SAVE_FILE", "", "SUCCESS")
            return result

        if intent == "mouse_click":
            ok, msg = DesktopAutomation.mouse_click("left")
            result["response"] = "ක්ලික් කළා." if is_sin else "Clicked."
            result["spoken_response"] = result["response"]
            log_audit("MOUSE_CLICK", "left", "SUCCESS")
            return result

        if intent == "mouse_double_click":
            ok, msg = DesktopAutomation.mouse_double_click()
            result["response"] = "ඩබල් ක්ලික් කළා." if is_sin else "Double clicked."
            result["spoken_response"] = result["response"]
            log_audit("MOUSE_DOUBLE_CLICK", "", "SUCCESS")
            return result

        if intent == "mouse_right_click":
            ok, msg = DesktopAutomation.mouse_click("right")
            result["response"] = "රයිට් ක්ලික් කළා." if is_sin else "Right clicked."
            result["spoken_response"] = result["response"]
            log_audit("MOUSE_RIGHT_CLICK", "right", "SUCCESS")
            return result

        if intent == "mouse_scroll":
            direction = args.get("direction", "down")
            ok, msg = DesktopAutomation.mouse_scroll(direction)
            result["response"] = ("පහළට ස්ක්‍රෝල් කළා." if direction == "down" else "ඉහළට ස්ක්‍රෝල් කළා.") if is_sin else f"Scrolled {direction}."
            result["spoken_response"] = result["response"]
            log_audit("MOUSE_SCROLL", direction, "SUCCESS")
            return result

        if intent == "create_folder":
            folder_name = args.get("folder_name", "New Folder")
            location = args.get("location", "desktop")
            ok, target_path = DesktopAutomation.create_folder(folder_name, location)
            if ok:
                result["response"] = f"ඩෙස්ක්ටොප් එකේ '{folder_name}' නමින් ෆෝල්ඩරය නිර්මාණය කළා." if is_sin else f"Created folder '{folder_name}' on Desktop."
                result["spoken_response"] = "ෆෝල්ඩරය සෑදුවා." if is_sin else f"Folder {folder_name} created."
                result["data"] = {"path": target_path}
            else:
                result["status"] = "FAILED"
                result["response"] = f"Failed to create folder: {target_path}"
                result["spoken_response"] = "Failed to create folder."
            log_audit("CREATE_FOLDER", folder_name, result["status"])
            return result

        if intent == "empty_recycle_bin":
            ok, msg = DesktopAutomation.empty_recycle_bin()
            result["response"] = "රීසයිකල් බින් එක සාර්ථකව හිස් කළා." if is_sin else "Recycle Bin emptied successfully."
            result["spoken_response"] = result["response"]
            log_audit("EMPTY_RECYCLE_BIN", "", "SUCCESS")
            return result

        if intent == "open_system_utility":
            utility = args.get("utility", "")
            ok, msg = DesktopAutomation.open_system_utility(utility)
            nice_name = utility.replace("_", " ").title()
            if ok:
                result["response"] = f"{nice_name} විවෘත කළා." if is_sin else f"Opened {nice_name}."
                result["spoken_response"] = f"{nice_name} විවෘත කරනවා." if is_sin else f"Opening {nice_name}."
            else:
                result["status"] = "FAILED"
                result["response"] = msg
                result["spoken_response"] = "Failed to open utility."
            log_audit("OPEN_UTILITY", utility, result["status"])
            return result


        # 3. Audio Controls
        if intent == "set_volume":
            lvl = max(0, min(100, int(args.get("level", 50))))
            ok = set_system_volume(lvl)
            if ok:
                result["response"] = f"ශබ්දය {lvl}% දක්වා සකස් කළා." if is_sin else f"Master volume set to {lvl}%."
                result["spoken_response"] = f"ශබ්දය සියයට {lvl} කළා." if is_sin else f"Volume set to {lvl} percent."
            else:
                result["status"] = "FAILED"
                result["response"] = "Could not adjust system volume."
                result["spoken_response"] = "Failed to adjust volume."
            log_audit("SET_VOLUME", f"Level: {lvl}", result["status"])
            return result

        if intent == "adjust_volume":
            current = get_system_volume()
            delta = args.get("delta", 10)
            target = max(0, min(100, current + delta))
            ok = set_system_volume(target)
            if ok:
                result["response"] = f"ශබ්දය {target}% දක්වා වෙනස් කළා." if is_sin else f"Volume adjusted to {target}%."
                result["spoken_response"] = f"ශබ්දය සියයට {target} දක්වා වෙනස් කළා." if is_sin else f"Volume is now {target} percent."
            else:
                result["status"] = "FAILED"
                result["response"] = "Failed to change audio volume."
                result["spoken_response"] = "Audio adjustment failed."
            log_audit("ADJUST_VOLUME", f"New level: {target}", result["status"])
            return result

        if intent == "set_mute":
            mute = args.get("mute", True)
            ok = set_system_mute(mute)
            if is_sin:
                msg = "ශබ්දය නිශ්ශබ්ද කළා." if mute else "ශබ්දය නැවත ක්‍රියාත්මක කළා."
            else:
                msg = "System audio muted." if mute else "System audio unmuted."
            result["status"] = "SUCCESS" if ok else "FAILED"
            result["response"] = msg if ok else "Could not change system mute."
            result["spoken_response"] = result["response"]
            log_audit("SET_MUTE", str(mute), "SUCCESS" if ok else "FAILED")
            return result

        # 4. Open Application
        if intent == "open_app":
            app_name = args.get("app_name", "")
            ok, msg = launch_application(app_name)
            result["status"] = "SUCCESS" if ok else "FAILED"
            result["response"] = msg
            result["spoken_response"] = f"{app_name} විවෘත කරනවා." if is_sin else msg
            log_audit("OPEN_APP", app_name, result["status"])
            return result

        # 5. Open URL
        if intent == "open_url":
            url = args.get("url", "")
            ok, msg = open_url(url)
            result["status"] = "SUCCESS" if ok else "FAILED"
            result["response"] = msg
            if "youtube" in url.lower():
                result["spoken_response"] = "YouTube විවෘත කරනවා." if is_sin else "Opening YouTube."
            elif "google" in url.lower():
                result["spoken_response"] = "Google විවෘත කරනවා." if is_sin else "Opening Google."
            elif "github" in url.lower():
                result["spoken_response"] = "GitHub විවෘත කරනවා." if is_sin else "Opening GitHub."
            elif "facebook" in url.lower():
                result["spoken_response"] = "Facebook විවෘත කරනවා." if is_sin else "Opening Facebook."
            else:
                result["spoken_response"] = "වෙබ් පිටුව විවෘත කරනවා." if is_sin else f"Opening {url}."
            log_audit("OPEN_URL", url, result["status"])
            return result

        # 5b. Media Playback Control
        if intent == "media_play_pause":
            import ctypes
            ctypes.windll.user32.keybd_event(0xB3, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0xB3, 0, 2, 0)
            result["response"] = "මාධ්‍ය වාදනය වෙනස් කළා." if is_sin else "Media playback toggled."
            result["spoken_response"] = "මාධ්‍ය වාදනය වෙනස් කළා." if is_sin else "Media toggled."
            log_audit("MEDIA_PLAY_PAUSE", "toggle", "SUCCESS")
            return result

        # 6. Web Search
        if intent == "web_search":
            query = args.get("query", "")
            url = f"https://www.google.com/search?q={quote_plus(query)}"
            ok, msg = open_url(url)
            result["status"] = "SUCCESS" if ok else "FAILED"
            result["response"] = f"Searching web for: {query}"
            result["spoken_response"] = f"Searching for {query}."
            log_audit("WEB_SEARCH", query, result["status"])
            return result

        # 7. Open User Folder
        if intent == "open_folder":
            folder = args.get("folder", "")
            ok, msg = open_folder(folder)
            result["status"] = "SUCCESS" if ok else "FAILED"
            result["response"] = msg
            result["spoken_response"] = msg
            log_audit("OPEN_FOLDER", folder, result["status"])
            return result

        # 8. System Metrics
        if intent == "get_system_metrics":
            metrics = get_system_metrics()
            result["data"] = metrics
            cpu = metrics['cpu']['percent']
            ram = metrics['ram']['percent']
            used_gb = metrics['ram']['used_gb']
            total_gb = metrics['ram']['total_gb']
            result["response"] = f"CPU Usage: {cpu}% | RAM Usage: {ram}% ({used_gb} GB of {total_gb} GB)"
            result["spoken_response"] = f"CPU is at {cpu} percent, and RAM usage is {ram} percent."
            log_audit("GET_METRICS", str(metrics), "SUCCESS")
            return result

        # 9. Lock Workstation
        if intent == "lock_screen":
            ok, msg = lock_workstation()
            result["status"] = "SUCCESS" if ok else "FAILED"
            result["response"] = msg
            result["spoken_response"] = "Locking workstation."
            log_audit("LOCK_SCREEN", "", result["status"])
            return result

        # 10. Shutdown / Restart Confirmation
        if intent in ["request_shutdown", "request_restart"]:
            action = "shut down" if intent == "request_shutdown" else "restart"
            result["status"] = "REQUIRES_CONFIRMATION"
            result["response"] = f"Are you sure you want to {action} your computer?"
            result["spoken_response"] = f"Please confirm if you want to {action} your computer."
            result["data"] = {"pending_action": intent}
            return result

        # 11. Trigger Routine
        if intent == "trigger_routine":
            routine_id = args.get("routine_id", "")
            if self.routine_runner:
                r_result = self.routine_runner.run_routine(routine_id)
                return r_result
            result["status"] = "FAILED"
            result["response"] = "Routine engine not available."
            result["spoken_response"] = "Routine runner unavailable."
            return result

        # 12. Create Reminder
        if intent == "create_reminder":
            title = args.get("title", "New Reminder")
            try:
                reminder = create_reminder(title)
            except ValueError as exc:
                return {"status": "FAILED", "response": str(exc), "spoken_response": str(exc)}
            due = datetime.fromtimestamp(reminder['due_time']).strftime('%d %b, %I:%M %p')
            result["response"] = f"Reminder created: '{title}' — {due}"
            result["data"] = reminder
            result["spoken_response"] = f"Created reminder for {title}."
            log_audit("CREATE_REMINDER", title, "SUCCESS")
            return result

        # 13. Create Note
        if intent == "create_note":
            content = args.get("content", "")
            title = content[:25] + ("..." if len(content) > 25 else "")
            conn = get_connection()
            conn.execute("INSERT INTO notes (title, content, created_at, updated_at) VALUES (?, ?, ?, ?)",
                         (title, content, time.time(), time.time()))
            conn.commit()
            conn.close()
            result["response"] = f"Saved note: '{title}'"
            result["spoken_response"] = "Note saved."
            log_audit("CREATE_NOTE", title, "SUCCESS")
            return result

        # Fallback
        result["status"] = "SUCCESS"
        result["response"] = "I am ready for your next command."
        result["spoken_response"] = "Ready."
        return result
