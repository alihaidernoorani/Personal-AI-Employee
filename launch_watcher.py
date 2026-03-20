"""
Launches the WhatsApp watcher as a clean Windows process,
stripped of any WSL/Linux env vars that cause Playwright to crash.

Usage:
    python launch_watcher.py              # run indefinitely
    python launch_watcher.py --test 180   # run for N seconds then exit
"""
import subprocess
import sys
import os
import time
import argparse
from pathlib import Path

BASE = Path(__file__).parent
LOG_FILE = BASE / "wa_watcher.log"

parser = argparse.ArgumentParser()
parser.add_argument("--test", type=int, default=0, help="Run for N seconds then exit (0=forever)")
args = parser.parse_args()

env = os.environ.copy()
env["VAULT_PATH"] = str(BASE / "AI_Employee_Vault")
# Remove Linux env vars that make Playwright add --no-sandbox / SwiftShader flags
for key in ("DISPLAY", "WAYLAND_DISPLAY", "XDG_SESSION_TYPE", "DBUS_SESSION_BUS_ADDRESS", "TERM"):
    env.pop(key, None)

python = sys.executable

with open(LOG_FILE, "w") as log:
    proc = subprocess.Popen(
        [python, "orchestrator.py", "--watcher", "whatsapp"],
        cwd=str(BASE),
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    )

print(f"WhatsApp Watcher started — PID={proc.pid}")
print(f"Log: {LOG_FILE}")
print("A browser window will open. Scan the QR code if prompted.")
print("Press Ctrl+C to stop.\n")

try:
    if args.test > 0:
        print(f"Test mode: running for {args.test}s...")
        proc.wait(timeout=args.test)
    else:
        proc.wait()
except subprocess.TimeoutExpired:
    proc.terminate()
    print(f"\nTest complete ({args.test}s).")
except KeyboardInterrupt:
    proc.terminate()
    print("\nStopped by user.")

print("\n--- Log ---")
print(LOG_FILE.read_text(errors="replace"))
