from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import psutil
import urllib.request
import base64
import time
from skyfield.api import load
from skyfield import almanac

ts = load.timescale()
planets = load("de421.bsp")

from pathlib import Path

def load_env():
    env_path = Path(__file__).resolve().parent / ".env"

    if not env_path.is_file():
        raise FileNotFoundError("Missing .env file")

    for line in env_path.read_text().splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        key, separator, value = line.partition("=")

        if separator:
            os.environ[key.strip()] = value.strip().strip('"').strip("'")

load_env()

def cpu_temp():
     with open("/sys/class/thermal/thermal_zone0/temp") as f:
        return int(f.read()) / 1000

def get_uptime():
    seconds = int(time.time() - psutil.boot_time())

    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes = remainder // 60

    return f"{days}d {hours}h {minutes}m" 

def get_moon_data():
    now = ts.now()

    phase_angle = almanac.moon_phase(planets, now).degrees
    illumination = almanac.fraction_illuminated(
        planets, "moon", now
    ) * 100

    if phase_angle < 22.5 or phase_angle >= 337.5:
        phase_name = "New Moon"
    elif phase_angle < 67.5:
        phase_name = "Waxing Crescent"
    elif phase_angle < 112.5:
        phase_name = "First Quarter"
    elif phase_angle < 157.5:
        phase_name = "Waxing Gibbous"
    elif phase_angle < 202.5:
        phase_name = "Full Moon"
    elif phase_angle < 247.5:
        phase_name = "Waning Gibbous"
    elif phase_angle < 292.5:
        phase_name = "Last Quarter"
    else:
        phase_name = "Waning Crescent"

    return {
        "phase": phase_name,
        "illumination": round(illumination, 1)
    }

def get_pc_stats():
    url = os.environ["PC_MONITOR_URL"]

    username = "pi-monitor"
    password = os.environ["PC_MONITOR_PASSWORD"]

    credentials = base64.b64encode(
        f"{username}:{password}".encode()
    ).decode()

    request = urllib.request.Request(url)
    request.add_header(
        "Authorization", f"Basic {credentials}"
    )

    with urllib.request.urlopen(request, timeout=5) as response:
        data = json.load(response)

    sensors = {}

    def walk(node):
        sensor_id = node.get("SensorId")

        if sensor_id:
            sensors[sensor_id] = node.get("Value")

        for child in node.get("Children", []):
            walk(child)

    walk(data)

    return {
        "cpu_temp": sensors.get("/intelcpu/0/temperature/22"),
        "cpu_usage": sensors.get("/intelcpu/0/load/0"),
        "gpu_temp": sensors.get("/gpu-nvidia/0/temperature/0"),
        "gpu_usage": sensors.get("/gpu-nvidia/0/load/0"),
        "vram_temp": sensors.get("/gpu-nvidia/0/temperature/3")
    }
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/temp":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(str(cpu_temp()).encode())
        elif self.path == "/pc-stats":
            try:
                pc_stats = get_pc_stats()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(pc_stats).encode())
            except Exception:
                self.send_response(503)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(
                    json.dumps({
                        "error": "PC telemetry temporarily unavailable"
                    }).encode()
                )
        elif self.path == "/stats":

            stats = {
                "cpu_usage": psutil.cpu_percent(interval=0.1),
                "cpu_temp": cpu_temp(),
                "ram_usage": psutil.virtual_memory().percent,
                "ram_total": round(psutil.virtual_memory().total / (1024**3), 1),
                "storage_usage": psutil.disk_usage("/").percent,
                "storage_total": round(psutil.disk_usage("/").total / (1024**3), 1),
                "uptime": get_uptime(),
                "moon": get_moon_data()
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(stats).encode())
        elif self.path == "/stars.css":
            self.send_response(200)
            self.send_header("Content-Type", "text/css")
            self.end_headers()
            with open("stars.css", "rb") as f:
                self.wfile.write(f.read())
        elif self.path == "/space.js":
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript")
            self.end_headers()
            with open("space.js", "rb") as f:
                self.wfile.write(f.read())
       
        elif self.path == "/assets/backgrounds/home.png":
             self.send_response(200)
             self.send_header("Content-Type", "image/png")
             self.end_headers()
             with open("assets/backgrounds/home.png", "rb") as f:
               self.wfile.write(f.read())        
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            with open("index.html", "rb") as f:
                self.wfile.write(f.read())

if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    server.serve_forever()
