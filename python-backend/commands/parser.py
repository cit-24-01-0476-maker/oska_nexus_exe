import re
import urllib.parse
from typing import Dict, Any

class CommandParser:
    @staticmethod
    def parse(text: str) -> Dict[str, Any]:
        result = CommandParser._parse_internal(text)
        is_sin = bool(re.search(r'[\u0D80-\u0DFF]', text)) or bool(re.search(r'\b(welawa|karanna|karapan|arinna|danna|yanna|kiyada|mokakda|oyata|kohomada|sadda|wadi|adu|ada|balanna|play|krnn|dhan)\b', text.lower()))
        if "args" not in result:
            result["args"] = {}
        result["args"]["is_sinhala"] = is_sin
        return result

    @staticmethod
    def _parse_internal(text: str) -> Dict[str, Any]:
        """
        Parses spoken or typed user input in English, Singlish, and Sinhala.
        """
        clean = text.lower().strip()
        # Remove common conversational prefixes
        clean = re.sub(
            r"^(hey\s+oska|oska|friday|please|karunakarala|ane|mata|can\s+you|could\s+you|කරුණාකරලා|අනේ|මට|හේ\s+ඔස්කා|ඔස්කා)\s*,?\s*",
            "",
            clean
        )

        if "මතක් කරන්න" in clean or re.search(r"\b(remind me to|create reminder to|mathak karanna|remind karanna)\b", clean):
            remind_match = re.search(r"(remind me to|create reminder to|mathak karanna|remind karanna|මතක් කරන්න)\s+(.+)$", clean)
            if remind_match:
                title = remind_match.group(2).strip()
                return {"intent": "create_reminder", "args": {"title": title}}

        if "සටහන් කරන්න" in clean or re.search(r"\b(create note|take note|note down|note karaganna|liyaganna)\b", clean):
            note_match = re.search(r"(create note|take note|note down|note karaganna|liyaganna|සටහන් කරන්න)\s+(.+)$", clean)
            if note_match:
                content = note_match.group(2).strip()
                return {"intent": "create_note", "args": {"content": content}}


        # -------------------------------------------------------------
        # 1. System Time & Date (English, Singlish & Sinhala)
        # -------------------------------------------------------------
        if ("වෙලාව" in clean or "දැන් වෙලාව" in clean or re.search(r"\b(welawa|welaawa|time|current time|dan welawa|dhan welawa)\b", clean)) and \
           ("කීයද" in clean or "මොකක්ද" in clean or "කියන්න" in clean or re.search(r"\b(kiyada|mokakda|what|is|it|tell|kiyanna)\b", clean)):
            return {"intent": "get_time", "args": {}}
        if "වෙලාව කීයද" in clean or re.search(r"\b(what('s| is) the time|what time is it|time please|time eka)\b", clean):
            return {"intent": "get_time", "args": {}}

        # Date
        if ("දිනය" in clean or "දවස" in clean or re.search(r"\b(date|dinaya|dawasa|day)\b", clean)) and \
           ("අද" in clean or "මොකක්ද" in clean or re.search(r"\b(ada|today|what|is|kiyanna|mokakda)\b", clean)):
            return {"intent": "get_date", "args": {}}

        # Questions about an application or requests for a plan are conversation,
        # even when they mention words also used by desktop automation rules.
        asks_for_explanation = re.search(
            r"\b(explain|describe|plan|tell me about|what is|what are|how does|how do|help me understand)\b|සැලැස්ම|පැහැදිලි|කියන්නේ|පිළිබඳ|ගැන", clean
        )
        explicit_search = re.search(r"\b(search|hoyanna|look up)\b|හොයන්න|සොයන්න", clean)
        metrics_question = re.search(r"\b(ram|cpu|memory|battery)\b|රැම්|බැටරි", clean) and re.search(
            r"\b(usage|used|stats|level|check|show|kiyada)\b|කීයද|පෙන්වන්න", clean
        )
        if asks_for_explanation and not explicit_search and not metrics_question:
            return {"intent": "conversation", "args": {"query": text}}

        # -------------------------------------------------------------
        # 1.5 Desktop Automation (Windows OS & PyAutoGUI Control)
        # -------------------------------------------------------------

        # Screenshot capture
        if "ස්ක්‍රීන්ෂොට්" in clean or "ස්ක්‍රීන් ෂොට්" in clean or re.search(r"\b(screenshot|screen shot|capture screen|screenshot ganna|screenshot ekak)\b", clean):
            return {"intent": "take_screenshot", "args": {}}

        # Show desktop / minimize all windows
        if "ඩෙස්ක්ටොප් එක පෙන්වන්න" in clean or "ඩෙස්ක්ටොප් එකට යන්න" in clean or re.search(r"\b(show desktop|display desktop|desktop eka pennanna|desktop pennanna|desktop ekata yanna|minimize all|hide all windows)\b", clean):
            return {"intent": "show_desktop", "args": {}}

        # Window management: Minimize, Maximize, Close, Switch
        if "මිනිමයිස්" in clean or re.search(r"\b(minimize|minimize karanna|minimize karapan|window eka minimize|minimize window)\b", clean):
            return {"intent": "minimize_window", "args": {}}

        if "මැක්සිමයිස්" in clean or re.search(r"\b(maximize|maximize karanna|maximize karapan|fullscreen karanna|full screen|maximize window)\b", clean):
            return {"intent": "maximize_window", "args": {}}

        if ("වින්ඩෝ එක වහන්න" in clean or "මේක වහන්න" in clean or "ඇප් එක වහන්න" in clean or 
            re.search(r"\b(close window|close active window|close current window|close application|close karanna|window eka wahanna|app eka wahanna|meka wahanna)\b", clean)):
            return {"intent": "close_window", "args": {}}

        if ("වින්ඩෝ එක මාරු" in clean or "වෙන වින්ඩෝ" in clean or 
            re.search(r"\b(switch window|alt tab|window eka maru|next window|previous window)\b", clean)):
            return {"intent": "switch_window", "args": {}}

        # Browser tab controls
        if "ටැබ් එක වහන්න" in clean or "මේ ටැබ් එක වහන්න" in clean or re.search(r"\b(close tab|tab eka wahanna|close this tab)\b", clean):
            return {"intent": "close_tab", "args": {}}

        if "අලුත් ටැබ්" in clean or re.search(r"\b(new tab|aluth tab|tab ekak open|open new tab|create tab)\b", clean):
            return {"intent": "new_tab", "args": {}}

        if "කලින් ටැබ්" in clean or re.search(r"\b(reopen tab|kalin tab|restore tab|undo close tab)\b", clean):
            return {"intent": "reopen_tab", "args": {}}

        if "රිෆ්‍රෙෂ්" in clean or re.search(r"\b(refresh|refresh page|reload|page eka refresh|reload karanna)\b", clean):
            return {"intent": "refresh_page", "args": {}}

        # Keyboard typing
        type_match = re.search(r"^(?:type karanna|type out|type|ලියන්න|ටයිප් කරන්න)\s+(.+)$", text, re.IGNORECASE)
        if type_match:
            text_to_type = type_match.group(1).strip()
            text_to_type = re.sub(r"\s*(kiyala|කියලා)$", "", text_to_type, flags=re.IGNORECASE).strip()
            if text_to_type:
                return {"intent": "type_text", "args": {"text": text_to_type}}

        # Key presses
        if "එන්ටර්" in clean or re.search(r"\b(press enter|hit enter|enter obanna|enter press|enter gahanna)\b", clean):
            return {"intent": "press_key", "args": {"key": "enter"}}
        if "එස්කේප්" in clean or re.search(r"\b(press escape|hit escape|esc obanna|escape obanna|press esc)\b", clean):
            return {"intent": "press_key", "args": {"key": "esc"}}
        if "ස්පේස්" in clean or re.search(r"\b(press space|space obanna|space bar)\b", clean):
            return {"intent": "press_key", "args": {"key": "space"}}
        if "බැක්ස්පේස්" in clean or re.search(r"\b(press backspace|backspace obanna)\b", clean):
            return {"intent": "press_key", "args": {"key": "backspace"}}

        # Clipboard operations: Copy, Paste, Select All, Save
        if "කොපි කරන්න" in clean or re.search(r"\b(copy karanna|copy this|copy selection|copy karapan)\b", clean):
            return {"intent": "copy_selection", "args": {}}

        if "පේස්ට් කරන්න" in clean or re.search(r"\b(paste karanna|paste this|paste here|paste karapan)\b", clean):
            return {"intent": "paste_clipboard", "args": {}}

        if "ඔක්කොම සිලෙක්ට්" in clean or "සියල්ල තෝරන්න" in clean or re.search(r"\b(select all|okkoma select|highlight all)\b", clean):
            return {"intent": "select_all", "args": {}}

        if "සේව් කරන්න" in clean or re.search(r"\b(save karanna|save file|save document|save this)\b", clean):
            return {"intent": "save_file", "args": {}}

        # Mouse clicks & scroll
        if "ඩබල් ක්ලික්" in clean or re.search(r"\b(double click|double click karanna)\b", clean):
            return {"intent": "mouse_double_click", "args": {}}

        if "රයිට් ක්ලික්" in clean or re.search(r"\b(right click|right click karanna)\b", clean):
            return {"intent": "mouse_right_click", "args": {}}

        if "ක්ලික් කරන්න" in clean or re.search(r"\b(click karanna|mouse click|left click)\b", clean):
            return {"intent": "mouse_click", "args": {}}

        if "පහළට ස්ක්‍රෝල්" in clean or re.search(r"\b(scroll down|pahallata scroll|scroll down karanna)\b", clean):
            return {"intent": "mouse_scroll", "args": {"direction": "down"}}

        if "ඉහළට ස්ක්‍රෝල්" in clean or re.search(r"\b(scroll up|udata scroll|scroll up karanna)\b", clean):
            return {"intent": "mouse_scroll", "args": {"direction": "up"}}

        # File system & Utilities
        if "රීසයිකල් බින්" in clean or re.search(r"\b(empty recycle bin|clear recycle bin|recycle bin (?:eka\s+)?(?:as|empty|clear)|empty trash)\b", clean):
            return {"intent": "empty_recycle_bin", "args": {}}

        create_folder_match = re.search(r"(?:desktop eke|desktop\s+වල|folder ekak hadanna|create folder|make folder|new folder|ෆෝල්ඩර් එකක් හදන්න)\s*([a-zA-Z0-9_\-\s]*)(?:folder ekak|කියලා)?", clean)
        if create_folder_match and ("folder" in clean or "ෆෝල්ඩර්" in clean) and any(w in clean for w in ["hadanna", "create", "make", "new", "හදන්න"]):
            folder_target = re.sub(r"(?i)(?:desktop eke|desktop\s+වල|folder ekak hadanna|create folder|make folder|new folder|ෆෝල්ඩර් එකක් හදන්න|folder|ekak|hadanna|හදන්න)", "", text).strip()
            folder_target = folder_target if folder_target else "New Folder"
            return {"intent": "create_folder", "args": {"folder_name": folder_target, "location": "desktop"}}

        # Windows Utilities
        if "ටාස්ක් මැනේජර්" in clean or re.search(r"\b(task manager|taskmgr|task manager open)\b", clean):
            return {"intent": "open_system_utility", "args": {"utility": "task_manager"}}

        if "කොන්ට්‍රෝල් පැනල්" in clean or re.search(r"\b(control panel|control panel open)\b", clean):
            return {"intent": "open_system_utility", "args": {"utility": "control_panel"}}

        if "ඩිවයිස් මැනේජර්" in clean or re.search(r"\b(device manager|devmgmt)\b", clean):
            return {"intent": "open_system_utility", "args": {"utility": "device_manager"}}

        if "වයිෆයි" in clean or "නෙට්වර්ක්" in clean or re.search(r"\b(wifi settings|network settings|wifi open|network open)\b", clean):
            return {"intent": "open_system_utility", "args": {"utility": "network_settings"}}

        if "බ්ලූටූත්" in clean or re.search(r"\b(bluetooth settings|bluetooth open)\b", clean):
            return {"intent": "open_system_utility", "args": {"utility": "bluetooth_settings"}}

        if "ඩිස්ප්ලේ" in clean or re.search(r"\b(display settings|screen settings)\b", clean):
            return {"intent": "open_system_utility", "args": {"utility": "display_settings"}}

        if "වින්ඩෝස් අප්ඩේට්" in clean or re.search(r"\b(windows update|check updates)\b", clean):
            return {"intent": "open_system_utility", "args": {"utility": "windows_update"}}


        # -------------------------------------------------------------
        # 2. YouTube Control (Dedicated robust matching for open & play)
        # Handles: "youtube open karanna", "open youtube", "යූටියුබ් අරින්න", "යූටියුබ් ඕපන් කරන්න", "mama dan youtuibe opne krnn kiwwoth"
        # -------------------------------------------------------------
        if "යූටියුබ්" in clean or "යුටියුබ්" in clean or re.search(r"\b(youtube|youtuibe|youtub|yotube|youtyub)\b", clean):
            # Check if there is a specific video/song search query
            eke_match = re.search(r"(youtube|youtuibe|youtub|yotube|youtyub|යූටියුබ්|යුටියුබ්)\s+(eke|ගිහින්|වල|වලින්|in)\s+(.+)$", clean)
            if eke_match:
                q = eke_match.group(3).strip()
                q = re.sub(r"\s*(play karanna|search karanna|hoyanna|balanna|open karanna|දාලා දෙන්න|දාන්න|බලන්න|play|search)$", "", q).strip()
                if q:
                    encoded = urllib.parse.quote_plus(q)
                    return {"intent": "open_url", "args": {"url": f"https://www.youtube.com/results?search_query={encoded}"}}
            return {"intent": "open_url", "args": {"url": "https://youtube.com"}}

        # -------------------------------------------------------------
        # 3. Media Playback Control (Play / Pause toggle on PC)
        # "pause karanna", "play karanna", "music nawaththanna", "නවත්ත්වන්න"
        # -------------------------------------------------------------
        if "නවත්ත්වන්න" in clean or "නවතන්න" in clean or "ප්ලේ" in clean or re.search(r"\b(pause|play|resume|stop music|music play|music pause)\b", clean):
            return {"intent": "media_play_pause", "args": {}}

        # -------------------------------------------------------------
        # 4. Audio Controls (English, Singlish & Sinhala)
        # -------------------------------------------------------------
        vol_set_match = re.search(r"\b(set volume to|volume|sound|වොලියුම්|ශබ්දය)\s*(?:eka|ekak|එක)?\s*(\d{1,3})\s*(%|percent)?\b", clean)
        if vol_set_match:
            return {"intent": "set_volume", "args": {"level": int(vol_set_match.group(2))}}

        if "වැඩි කරන්න" in clean or "සද්දෙ වැඩි" in clean or "වොලියුම් වැඩි" in clean or re.search(r"\b(volume wadi|sound wadi|sadda wadi|louder|volume up|increase volume|turn up)\b", clean):
            return {"intent": "adjust_volume", "args": {"delta": 15}}
        if "අඩු කරන්න" in clean or "සද්දෙ අඩු" in clean or "වොලියුම් අඩු" in clean or re.search(r"\b(volume adu|sound adu|sadda adu|quieter|volume down|decrease volume|lower volume|turn down)\b", clean):
            return {"intent": "adjust_volume", "args": {"delta": -15}}

        if "නිශ්ශබ්ද" in clean or "නිශ්ශබ්ද කරන්න" in clean or "මියුට් කරන්න" in clean or re.search(r"\b(mute|sadda nawaththanna|mute karanna)\b", clean):
            return {"intent": "set_mute", "args": {"mute": True}}
        if "ශබ්දය දාන්න" in clean or re.search(r"\b(unmute|unmute karanna|sound danna)\b", clean):
            return {"intent": "set_mute", "args": {"mute": False}}

        # -------------------------------------------------------------
        # 5. Routines (Modes)
        # -------------------------------------------------------------
        if "කෝඩින් මෝඩ්" in clean or "කෝඩින් කරන්න" in clean or re.search(r"\b(coding mode|code mode|dev mode|coding patan|code karanna)\b", clean):
            return {"intent": "trigger_routine", "args": {"routine_id": "routine-coding"}}
        if "ස්ටඩි මෝඩ්" in clean or "පාඩම් කරන්න" in clean or re.search(r"\b(study mode|padam karanna|study patan|learning mode)\b", clean):
            return {"intent": "trigger_routine", "args": {"routine_id": "routine-study"}}
        if "මීටින් මෝඩ්" in clean or re.search(r"\b(meeting mode|meeting ekak|start meeting)\b", clean):
            return {"intent": "trigger_routine", "args": {"routine_id": "routine-meeting"}}
        if "සුබ උදෑසනක්" in clean or "දවස පටන්" in clean or re.search(r"\b(start my day|dawasa patan|good morning|subha udasanak|daily start)\b", clean):
            return {"intent": "trigger_routine", "args": {"routine_id": "routine-daily"}}

        # -------------------------------------------------------------
        # 6. Popular Applications (Direct detection)
        # -------------------------------------------------------------
        if "ක්‍රෝම්" in clean or re.search(r"\b(chrome|crome|chrme)\b", clean):
            return {"intent": "open_app", "args": {"app_name": "chrome"}}

        if "වට්ස්ඇප්" in clean or "වට්සැප්" in clean or re.search(r"\b(whatsapp|watsapp|whatsap|watsap)\b", clean):
            return {"intent": "open_app", "args": {"app_name": "whatsapp"}}

        if "කැල්කියුලේටරය" in clean or "කැල්කියුලේටර්" in clean or re.search(r"\b(calculator|calc)\b", clean):
            return {"intent": "open_app", "args": {"app_name": "calculator"}}

        if "නෝට්පෑඩ්" in clean or re.search(r"\b(notepad)\b", clean):
            return {"intent": "open_app", "args": {"app_name": "notepad"}}

        if "කෝඩ්" in clean or re.search(r"\b(vs code|vscode|code|visual studio code)\b", clean):
            return {"intent": "open_app", "args": {"app_name": "vs code"}}

        if "ස්පොටිෆයි" in clean or re.search(r"\b(spotify)\b", clean):
            return {"intent": "open_app", "args": {"app_name": "spotify"}}

        # -------------------------------------------------------------
        # 7. Popular Websites
        # -------------------------------------------------------------
        clean_web = clean
        clean_web = clean_web.replace("ගූගල්", "google").replace("ගිට්හබ්", "github").replace("ෆේස්බුක්", "facebook")
        web_match = re.search(r"\b(github|google|gmail|reddit|twitter|x|chatgpt|netflix|facebook|instagram)\b", clean_web)
        if web_match:
            site = web_match.group(1)
            # If Google with search query:
            if site == "google":
                search_q = re.search(r"google( eke)?\s+(.+?)\s*(hoyanna|search|balanna)?$", clean_web)
                if search_q and search_q.group(2) not in ["open", "yanna", "danna", "arinna"]:
                    q = search_q.group(2).strip()
                    return {"intent": "web_search", "args": {"query": q}}
            urls = {
                "github": "https://github.com",
                "google": "https://google.com",
                "gmail": "https://mail.google.com",
                "reddit": "https://reddit.com",
                "twitter": "https://twitter.com",
                "x": "https://x.com",
                "chatgpt": "https://chatgpt.com",
                "netflix": "https://netflix.com",
                "facebook": "https://facebook.com",
                "instagram": "https://instagram.com"
            }
            return {"intent": "open_url", "args": {"url": urls.get(site, f"https://{site}.com")}}

        # -------------------------------------------------------------
        # 8. Hardware System Metrics
        # -------------------------------------------------------------
        if ("රැම්" in clean or "බැටරි" in clean or re.search(r"\b(ram|memory|cpu|battery|system stats|performance|usage)\b", clean)) and \
           ("කොහොමද" in clean or "කීයද" in clean or "පෙන්වන්න" in clean or re.search(r"\b(kiyada|balanna|how much|show|check|usage|level|stats)\b", clean)):
            return {"intent": "get_system_metrics", "args": {}}

        # -------------------------------------------------------------
        # 9. Power Actions
        # -------------------------------------------------------------
        if ("ලොක්" in clean or "ලොක් කරන්න" in clean or re.search(r"\b(lock)\b", clean)) and "clock" not in clean:
            return {"intent": "lock_screen", "args": {}}

        if "රිස්ටාර්ට්" in clean or "නැවත ආරම්භ" in clean or re.search(r"\b(restart)\b", clean):
            return {"intent": "request_restart", "args": {"requires_confirmation": True}}
        if "ඕෆ් කරන්න" in clean or "ක්‍රියා විරහිත" in clean or re.search(r"\b(shutdown|shut down|power off|off karanna)\b", clean):
            return {"intent": "request_shutdown", "args": {"requires_confirmation": True}}

        # -------------------------------------------------------------
        # 10. General Web Search
        # -------------------------------------------------------------
        search_match = re.search(r"\b(search( for| karanna| karapan)?|look up|hoyanna|සර්ච් කරන්න|හොයන්න)\s+(.+)$", clean)
        if search_match:
            query = search_match.group(3).strip()
            query = re.sub(r"\s*(kiyala|ekak|gane|කියලා|එකක්)$", "", query)
            if query:
                return {"intent": "web_search", "args": {"query": query}}

        # -------------------------------------------------------------
        # 11. User Folders
        # -------------------------------------------------------------
        folder_match = re.search(r"\b(documents|downloads|desktop|pictures|music|videos)\s*(folder)?\b", clean)
        if folder_match and (re.search(r"\b(open|arinna|danna|yanna|balanna)\b", clean) or any(w in clean for w in ["අරින්න", "දාන්න", "යන්න", "බලන්න"])):
            folder_name = folder_match.group(1)
            return {"intent": "open_folder", "args": {"folder": folder_name}}

        # -------------------------------------------------------------
        # 12. Generic Application Launching
        # -------------------------------------------------------------
        app_match = re.search(r"^(open|launch|start|run|අරින්න|ඕපන් කරන්න)\s+([a-zA-Z0-9\s]+)$", clean)
        if app_match:
            app_name = app_match.group(2).strip()
            app_name = re.sub(r"\s*(eka|ekak|karanna|karapan|එක|එකක්|කරන්න)$", "", app_name).strip()
            if app_name not in ["the", "a", "my", "settings", "it"]:
                return {"intent": "open_app", "args": {"app_name": app_name}}

        # -------------------------------------------------------------
        # 13. Notes & Reminders
        # -------------------------------------------------------------
        # Conversational fallback (will go to LLM or smart response)
        return {"intent": "conversation", "args": {"query": text}}
