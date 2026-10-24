import ctypes
import subprocess
from typing import Tuple

def lock_workstation() -> Tuple[bool, str]:
    """Instantly locks the Windows workstation safely using user32.dll."""
    try:
        user32 = ctypes.windll.User32
        res = user32.LockWorkStation()
        if res:
            return True, "Workstation locked successfully."
        else:
            return False, "Failed to lock workstation."
    except Exception as e:
        return False, f"Lock workstation error: {e}"

def execute_shutdown(confirmed: bool = False) -> Tuple[bool, str]:
    """Executes shutdown only if confirmed."""
    if not confirmed:
        return False, "Shutdown requires explicit user confirmation."
    try:
        subprocess.Popen(["shutdown", "/s", "/t", "10"], shell=False)
        return True, "Computer will shut down in 10 seconds. Type 'shutdown /a' in command prompt to cancel."
    except Exception as e:
        return False, f"Failed to initiate shutdown: {e}"

def execute_restart(confirmed: bool = False) -> Tuple[bool, str]:
    """Executes restart only if confirmed."""
    if not confirmed:
        return False, "Restart requires explicit user confirmation."
    try:
        subprocess.Popen(["shutdown", "/r", "/t", "10"], shell=False)
        return True, "Computer will restart in 10 seconds."
    except Exception as e:
        return False, f"Failed to initiate restart: {e}"
