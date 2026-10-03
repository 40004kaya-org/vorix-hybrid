#!/usr/bin/env python3
"""L-Resurrect — خودترمیمی"""
import os, sys, json, time, hashlib, subprocess, threading
from datetime import datetime

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
LOGS = os.path.join(BASE, "logs")
STATE = os.path.join(BASE, "layer_resurrect_state.json")
TOKEN = open(os.path.join(HOME, "vorix/.tg-token")).read().strip() if os.path.exists(os.path.join(HOME, "vorix/.tg-token")) else ""
CHAT = "175160049"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(os.path.join(LOGS, "layer_resurrect.log"), "a") as f:
            f.write(line + "\n")
    except: pass

def alert(msg):
    if not TOKEN: return
    try:
        import requests
        requests.post(
            "https://api.telegram.org/bot" + TOKEN + "/sendMessage",
            json={"chat_id": CHAT, "text": msg, "parse_mode": "HTML"},
            timeout=10
        )
    except: pass

def save_state(d):
    try:
        with open(STATE, "w") as f:
            json.dump(d, f, indent=2)
    except: pass

def load_state():
    try:
        with open(STATE) as f:
            return json.load(f)
    except:
        return {}

def pgrep(pattern):
    try:
        r = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True, timeout=2)
        return [p for p in r.stdout.strip().split("\n") if p]
    except:
        return []


WATCH = {
    "layer01_selfdefense.py": "watch",
    "layer03_behavioral.py": "watch",
    "layer04_auto_block.py": "watch",
    "layer06_geoip_block.py": "watch",
    "layer08_network_monitor.py": "watch",
    "layer09_rate_limiter.py": "watch",
    "layer10_red_alert.py": "watch",
    "layer17_watchdog.py": "watch",
    "layer19_password_leak.py": "watch",
    "layer21_ml_anomaly.py": "watch",
    "layer25_ssl_monitor.py": "watch",
    "layer29_30_identity.py": "watch",
    "layer_fim.py": "watch",
    "layer_rootkit.py": "watch",
    "layer_multichannel.py": "watch",
}

def restart(fname, sub):
    base = fname.replace(".py", "")
    try:
        subprocess.Popen(["python", fname, sub], cwd=BASE,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log("♻️ Restarted: " + fname)
        return True
    except Exception as e:
        log("ERR: " + str(e))
        return False

def watch():
    log("♻️ Resurrect started")
    attempts = {}
    while True:
        try:
            for fname, sub in WATCH.items():
                base = fname.replace(".py", "")
                if not pgrep(base):
                    n = attempts.get(fname, 0)
                    if n < 10:
                        restart(fname, sub)
                        attempts[fname] = n + 1
                    else:
                        log("❌ Gave up on " + fname)
                else:
                    attempts[fname] = 0
        except Exception as e:
            log("ERR: " + str(e))
        time.sleep(30)

def status():
    for f in WATCH:
        base = f.replace(".py", "")
        print(("✅" if pgrep(base) else "❌") + " " + f)

def test():
    print("Watching " + str(len(WATCH)) + " layers")


def main():
    if len(sys.argv) < 2:
        print("Usage: layer_resurrect.py {watch|status|test}")
        return
    cmd = sys.argv[1]
    if cmd == "watch": watch()
    elif cmd == "status": status()
    elif cmd == "test": test()

if __name__ == "__main__":
    main()
