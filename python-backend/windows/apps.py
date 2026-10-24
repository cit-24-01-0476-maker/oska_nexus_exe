import os
import subprocess
import webbrowser
import shutil
from typing import Dict, Optional, Tuple

# Known safe standard Windows application mappings
APP_REGISTRY: Dict[str, Dict[str, str]] = {
    "notepad": {
        "exe": "notepad.exe",
        "name": "Notepad"
    },
    "calculator": {
        "exe": "calc.exe",
        "name": "Calculator"
    },
    "calc": {
        "exe": "calc.exe",
        "name": "Calculator"
    },
    "cmd": {
        "exe": "cmd.exe",
        "name": "Command Prompt"
    },
    "terminal": {
        "exe": "wt.exe",
        "fallback": "powershell.exe",
        "name": "Windows Terminal"
    },
    "powershell": {
        "exe": "powershell.exe",
        "name": "PowerShell"
    },
    "explorer": {
        "exe": "explorer.exe",
        "name": "File Explorer"
    },
    "file explorer": {
        "exe": "explorer.exe",
        "name": "File Explorer"
    },
    "task manager": {
        "exe": "taskmgr.exe",
        "name": "Task Manager"
    },
    "taskmgr": {
        "exe": "taskmgr.exe",
        "name": "Task Manager"
    },
    "settings": {
        "uri": "ms-settings:",
        "name": "Windows Settings"
    },
    "paint": {
        "exe": "mspaint.exe",
        "name": "Paint"
    },
    "code": {
        "exe": "code",
        "alt_paths": [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
            r"C:\Program Files\Microsoft VS Code\Code.exe"
        ],
        "name": "Visual Studio Code"
    },
    "vs code": {
        "exe": "code",
        "alt_paths": [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
            r"C:\Program Files\Microsoft VS Code\Code.exe"
        ],
        "name": "Visual Studio Code"
    },
    "chrome": {
        "exe": "chrome.exe",
        "alt_paths": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        ],
        "name": "Google Chrome"
    },
    "edge": {
        "exe": "msedge.exe",
        "alt_paths": [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        ],
        "name": "Microsoft Edge"
    },
    "spotify": {
        "uri": "spotify:",
        "exe": "spotify.exe",
        "alt_paths": [
            os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe")
        ],
        "name": "Spotify"
    },
    "youtube": {
        "uri": "https://youtube.com",
        "name": "YouTube"
    },
    "whatsapp": {
        "uri": "whatsapp:",
        "fallback_url": "https://web.whatsapp.com",
        "name": "WhatsApp"
    },
    "discord": {
        "uri": "discord:",
        "fallback_url": "https://discord.com/app",
        "name": "Discord"
    },
    "telegram": {
        "uri": "tg:",
        "fallback_url": "https://web.telegram.org",
        "name": "Telegram"
    },
    "word": {
        "exe": "winword.exe",
        "alt_paths": [
            r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
            r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE"
        ],
        "name": "Microsoft Word"
    },
    "excel": {
        "exe": "excel.exe",
        "alt_paths": [
            r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
            r"C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE"
        ],
        "name": "Microsoft Excel"
    },
    "powerpoint": {
        "exe": "powerpnt.exe",
        "alt_paths": [
            r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
            r"C:\Program Files (x86)\Microsoft Office\root\Office16\POWERPNT.EXE"
        ],
        "name": "Microsoft PowerPoint"
    },
    "brave": {
        "exe": "brave.exe",
        "alt_paths": [
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe")
        ],
        "name": "Brave Browser"
    },
    "firefox": {
        "exe": "firefox.exe",
        "alt_paths": [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"
        ],
        "name": "Mozilla Firefox"
    }
}

def resolve_application(app_name: str) -> Optional[Dict[str, str]]:
    clean = app_name.lower().strip()
    if clean in APP_REGISTRY:
        return APP_REGISTRY[clean]
    
    # Partial match
    for key, val in APP_REGISTRY.items():
        if key in clean or clean in key:
            return val
    return None

def launch_application(app_name: str) -> Tuple[bool, str]:
    app_info = resolve_application(app_name)
    if not app_info:
        # Check if the app exists directly on PATH
        which_path = shutil.which(app_name)
        if which_path:
            try:
                subprocess.Popen([which_path], shell=False)
                return True, f"Launched {app_name}"
            except Exception as e:
                return False, f"Failed to launch {app_name}: {e}"
        return False, f"Application '{app_name}' not found or not recognized."

    # Handle URI protocols like ms-settings:, spotify:, or web URLs
    if "uri" in app_info:
        uri = app_info["uri"]
        if uri.startswith("http://") or uri.startswith("https://"):
            webbrowser.open(uri)
            return True, f"Opened {app_info['name']}"
        try:
            os.startfile(uri)
            return True, f"Opened {app_info['name']}"
        except Exception:
            if "fallback_url" in app_info:
                webbrowser.open(app_info["fallback_url"])
                return True, f"Opened {app_info['name']} (Web)"

    # Handle executable
    exe = app_info.get("exe")
    if exe and shutil.which(exe):
        try:
            subprocess.Popen([exe], shell=False)
            return True, f"Launched {app_info['name']}"
        except Exception as e:
            return False, f"Failed to launch {app_info['name']}: {e}"

    # Check alternate paths
    for path in app_info.get("alt_paths", []):
        if os.path.exists(path):
            try:
                subprocess.Popen([path], shell=False)
                return True, f"Launched {app_info['name']}"
            except Exception as e:
                return False, f"Failed to launch {app_info['name']}: {e}"

    # Check fallback
    fallback = app_info.get("fallback")
    if fallback and shutil.which(fallback):
        try:
            subprocess.Popen([fallback], shell=False)
            return True, f"Launched {app_info['name']} (fallback)"
        except Exception as e:
            return False, f"Failed to launch fallback for {app_info['name']}: {e}"

    return False, f"{app_info['name']} is not installed on this system."

def open_url(url: str) -> Tuple[bool, str]:
    """Safely opens an authorized HTTP or HTTPS URL in the default browser."""
    clean_url = url.strip()
    if not (clean_url.startswith("http://") or clean_url.startswith("https://")):
        clean_url = "https://" + clean_url
    
    try:
        webbrowser.open(clean_url)
        return True, f"Opening {clean_url}"
    except Exception as e:
        return False, f"Failed to open URL: {e}"

def open_folder(folder_path: str) -> Tuple[bool, str]:
    """Safely opens standard user folders."""
    path_map = {
        "documents": os.path.expanduser(r"~\Documents"),
        "downloads": os.path.expanduser(r"~\Downloads"),
        "desktop": os.path.expanduser(r"~\Desktop"),
        "pictures": os.path.expanduser(r"~\Pictures"),
        "music": os.path.expanduser(r"~\Music"),
        "videos": os.path.expanduser(r"~\Videos")
    }

    target = path_map.get(folder_path.lower().strip(), folder_path)
    if os.path.exists(target) and os.path.isdir(target):
        try:
            os.startfile(target)
            return True, f"Opened {folder_path} folder."
        except Exception as e:
            return False, f"Error opening folder: {e}"
    return False, f"Folder '{folder_path}' does not exist."
