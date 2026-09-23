"""
Launcher script for ResumeMatch AI.
Runs on 0.0.0.0 so other devices on the same Wi-Fi / LAN can connect.

Usage:
    python run.py
"""
import sys
import socket
import uvicorn
from app.config import HOST, PORT

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def get_local_ip():
    """Detects the computer's local Wi-Fi / LAN IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

if __name__ == "__main__":
    local_ip = get_local_ip()
    print("=" * 65)
    print(">> Starting ResumeMatch AI Web Application")
    print(f">> On THIS Computer:          http://localhost:{PORT}")
    print(f">> On ANOTHER Device (Wi-Fi): http://{local_ip}:{PORT}")
    print("=" * 65)
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=False)

