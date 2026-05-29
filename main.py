#!/home/ubuntu/iris/venv/bin/python3
"""
Server status API — queries Minecraft, GMod, and Terraria.
"""
import json
import socket
import subprocess
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def mc_query(host: str, port: int, timeout: float = 3.0) -> dict:
    """Query Minecraft server via raw socket (bedrock/protocol)."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        # Handshake
        handshake = b"\x00\x00"
        handshake += b"\x00\x00"  # packet ID
        handshake += bytes([1])   # client version
        sock.sendto(handshake, (host, port))
        data, _ = sock.recvfrom(4096)
        sock.close()
        if data:
            return {"online": True, "players": "?"}
    except Exception:
        pass
    return {"online": False, "players": 0}


def check_process(name: str, screen: str = None) -> dict:
    """Check if a process or screen session is running."""
    if screen:
        result = subprocess.run(["screen", "-ls"], capture_output=True, text=True)
        running = screen in result.stdout
        return {"online": running}
    # Fallback: check process
    result = subprocess.run(["pgrep", "-a", name], capture_output=True, text=True)
    return {"online": len(result.stdout) > 0}


@app.get("/status")
def status():
    mc = mc_query("127.0.0.1", 25565)
    gmod = check_process("srcds_linux", "gmod")
    terraria = check_process("TerrariaServer", "terraria")
    polimc = check_process("paper", "polimc")
    pqr_online = check_process("python", None)

    # System stats
    disk_used = subprocess.check_output(
        "df -h / | tail -1 | awk '{print $3}'", shell=True
    ).decode().strip()
    ram_used = subprocess.check_output(
        "free -h | grep Mem | awk '{print $3}'", shell=True
    ).decode().strip()
    uptime_str = subprocess.check_output(
        "uptime -p 2>/dev/null || uptime | awk '{print $3,$4}' | tr -d ,",
        shell=True
    ).decode().strip()

    return {
        "minecraft": {"online": polimc["online"], "players": "?"},
        "gmod": {"online": gmod["online"], "players": "?"},
        "terraria": {"online": terraria["online"], "players": "?"},
        "pqr": {"online": pqr_online["online"]},
        "dcbot": check_process("python", None)["online"],
        "system": {
            "disk": disk_used,
            "ram": ram_used,
            "uptime": uptime_str,
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5002, log_level="error")