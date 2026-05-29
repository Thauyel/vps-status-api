#!/home/ubuntu/iris/venv/bin/python3
"""
VPS Status API — game server status via screen sessions + system metrics via psutil.
Replaces the standalone glances approach with direct polling.
"""
import subprocess
import socket
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import psutil

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def check_screen(name: str) -> bool:
    result = subprocess.run(["screen", "-ls"], capture_output=True, text=True)
    return name in result.stdout


def check_process(name: str) -> bool:
    result = subprocess.run(["pgrep", "-f", name], capture_output=True, text=True)
    return len(result.stdout) > 0


def get_system_stats() -> dict:
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    cpu_load = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
    boot_time = psutil.boot_time()
    import time
    uptime_seconds = time.time() - boot_time

    # Top 5 CPU processes
    top_cpu = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            cpu = proc.info['cpu_percent']
            if cpu is not None and cpu > 0:
                top_cpu.append({
                    "name": proc.info['name'],
                    "cpu": round(cpu, 1),
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    top_cpu = sorted(top_cpu, key=lambda x: x['cpu'], reverse=True)[:5]

    # Top 5 RAM processes
    top_ram = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
        try:
            mp = proc.info['memory_percent']
            if mp is not None and mp > 0:
                top_ram.append({
                    "name": proc.info['name'],
                    "ram_pct": round(mp, 1),
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    top_ram = sorted(top_ram, key=lambda x: x['ram_pct'], reverse=True)[:5]

    return {
        "ram_used_gb": round(mem.used / (1024**3), 1),
        "ram_total_gb": round(mem.total / (1024**3), 1),
        "ram_pct": mem.percent,
        "disk_used_gb": round(disk.used / (1024**3), 1),
        "disk_total_gb": round(disk.total / (1024**3), 1),
        "disk_pct": disk.percent,
        "cpu_pct": psutil.cpu_percent(interval=0.5),
        "load_1m": round(cpu_load[0], 2),
        "load_5m": round(cpu_load[1], 2),
        "load_15m": round(cpu_load[2], 2),
        "uptime_seconds": int(uptime_seconds),
        "uptime_days": int(uptime_seconds // 86400),
        "uptime_hours": int((uptime_seconds % 86400) // 3600),
        "top_cpu": top_cpu,
        "top_ram": top_ram,
    }


@app.get("/status")
def status():
    return {
        "minecraft": {"online": check_screen("polimc")},
        "gmod": {"online": check_screen("gmod")},
        "terraria": {"online": check_screen("terraria")},
        "pqr": {"online": check_process("server.py")},
        "dcbot": {"online": check_process("main.py")},
        "system": get_system_stats(),
    }


@app.get("/health")
def health():
    return {"ok": True}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5002, log_level="error")