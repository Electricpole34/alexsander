"""
ALEX-SENDER dashboard backend
------------------------------
Serves an ASCII-styled system dashboard for a Raspberry Pi 5 home server:
  - CPU usage, temperature, RAM usage, uptime
  - SSD (boot/root drive) and HDD (WD My Book) storage usage

Run directly with `python3 app.py`, or install as a systemd service
(see alex-sender.service / README.md).
"""

import time
import subprocess
from pathlib import Path

import psutil
from flask import Flask, jsonify, render_template

app = Flask(__name__)

# ---------------------------------------------------------------------------
# CONFIG — adjust HDD_MOUNT to wherever the WD My Book is mounted.
# Check with `lsblk` or `df -h` on the Pi. Common defaults after adding a
# line to /etc/fstab: /mnt/storage, /media/wdmybook, /mnt/hdd, etc.
# ---------------------------------------------------------------------------
HDD_MOUNT = "/mnt/storage"
SSD_MOUNT = "/"           # Raspberry Pi OS boots and lives on the SSD
SERVER_NAME = "ALEX-SENDER"


def get_cpu_temp():
    """Read SoC temperature. Works on Raspberry Pi OS (Bookworm/Bullseye)."""
    thermal_path = Path("/sys/class/thermal/thermal_zone0/temp")
    try:
        raw = thermal_path.read_text().strip()
        return round(int(raw) / 1000.0, 1)
    except Exception:
        pass
    # Fallback to vcgencmd if the sysfs path isn't available
    try:
        out = subprocess.check_output(["vcgencmd", "measure_temp"], text=True)
        return round(float(out.strip().replace("temp=", "").replace("'C", "")), 1)
    except Exception:
        return None


def format_uptime(seconds):
    days, rem = divmod(int(seconds), 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)


def disk_stats(mount_path):
    try:
        usage = psutil.disk_usage(mount_path)
        return {
            "available": True,
            "total_gb": round(usage.total / (1024 ** 3), 1),
            "used_gb": round(usage.used / (1024 ** 3), 1),
            "free_gb": round(usage.free / (1024 ** 3), 1),
            "percent": usage.percent,
        }
    except Exception:
        return {"available": False}


@app.route("/")
def index():
    return render_template("index.html", server_name=SERVER_NAME)


@app.route("/api/stats")
def api_stats():
    vm = psutil.virtual_memory()
    uptime_seconds = time.time() - psutil.boot_time()

    return jsonify({
        "server_name": SERVER_NAME,
        "cpu": {
            "percent": psutil.cpu_percent(interval=0.3),
            "temp_c": get_cpu_temp(),
            "cores": psutil.cpu_count(logical=True),
        },
        "ram": {
            "total_gb": round(vm.total / (1024 ** 3), 2),
            "used_gb": round(vm.used / (1024 ** 3), 2),
            "percent": vm.percent,
        },
        "uptime": format_uptime(uptime_seconds),
        "ssd": disk_stats(SSD_MOUNT),
        "hdd": disk_stats(HDD_MOUNT),
    })


if __name__ == "__main__":
    # host="0.0.0.0" so it's reachable from other devices on the network
    app.run(host="0.0.0.0", port=5000)
