import psutil
import platform
import time
from typing import Dict, Any

def get_system_metrics() -> Dict[str, Any]:
    # CPU
    cpu_percent = psutil.cpu_percent(interval=None)
    cpu_cores = psutil.cpu_count(logical=True)
    
    # RAM
    ram = psutil.virtual_memory()
    ram_percent = ram.percent
    ram_used_gb = round(ram.used / (1024 ** 3), 2)
    ram_total_gb = round(ram.total / (1024 ** 3), 2)

    # Battery
    battery = psutil.sensors_battery()
    battery_info = {
        "has_battery": battery is not None,
        "percent": battery.percent if battery else None,
        "power_plugged": battery.power_plugged if battery else None
    }

    # Disk
    disk = psutil.disk_usage("C:\\")
    disk_info = {
        "percent": disk.percent,
        "free_gb": round(disk.free / (1024 ** 3), 2),
        "total_gb": round(disk.total / (1024 ** 3), 2)
    }

    # Uptime
    boot_time = psutil.boot_time()
    uptime_seconds = int(time.time() - boot_time)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    return {
        "os": f"Windows {platform.version()}",
        "cpu": {
            "percent": cpu_percent,
            "cores": cpu_cores
        },
        "ram": {
            "percent": ram_percent,
            "used_gb": ram_used_gb,
            "total_gb": ram_total_gb
        },
        "battery": battery_info,
        "disk": disk_info,
        "uptime": f"{hours}h {minutes}m"
    }
