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