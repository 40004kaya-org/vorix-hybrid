#!/usr/bin/env python3
"""L-Canary — طعمه هکر"""
import os, sys, json, time, hashlib, subprocess, threading
from datetime import datetime

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
LOGS = os.path.join(BASE, "logs")
STATE = os.path.join(BASE, "layer_canary_state.json")
TOKEN = open(os.path.join(HOME, "vorix/.tg-token")).read().strip() if os.path.exists(os.path.join(HOME, "vorix/.tg-token")) else ""
CHAT = "175160049"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(os.path.join(LOGS, "layer_canary.log"), "a") as f:
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


TRAP_DIR = os.path.join(BASE, "trap")
TRAPS = ["passwords.txt", "api_keys.json", "backup_codes.txt", "config_secret.env"]

def init_traps():
    os.makedirs(TRAP_DIR, exist_ok=True)
    for t in TRAPS:
        p = os.path.join(TRAP_DIR, t)
        if not os.path.exists(p):
            with open(p, "w") as f:
                f.write("# TRAP — DO NOT OPEN\n")
                f.write("honeypot_token=" + hashlib.sha256(t.encode()).hexdigest()[:32] + "\n")

def get_mtimes():
    m = {}
    for t in TRAPS:
        p = os.path.join(TRAP_DIR, t)
        if os.path.exists(p):
            m[t] = os.path.getmtime(p)
    return m

def watch():
    log("🪤 Canary started")
    init_traps()
    base = get_mtimes()
    while True:
        try:
            cur = get_mtimes()
            for t, m in cur.items():
                if t in base and m != base[t]:
                    log("🚨 TRAP TRIGGERED: " + t)
                    alert("🪤 <b>Canary triggered!</b>\nFile: <code>" + t + "</code>\nSomebody opened the trap!")
            base = cur
        except Exception as e:
            log("ERR: " + str(e))
        time.sleep(5)

def status():
    print("Traps: " + str(len(TRAPS)))
    for t in TRAPS:
        p = os.path.join(TRAP_DIR, t)
        print("  " + ("✅" if os.path.exists(p) else "❌") + " " + t)

def test():
    init_traps()
    print("Traps initialized:")
    for t in TRAPS:
        print("  " + t)


def main():
    if len(sys.argv) < 2:
        print("Usage: layer_canary.py {watch|status|test}")
        return
    cmd = sys.argv[1]
    if cmd == "watch": watch()
    elif cmd == "status": status()
    elif cmd == "test": test()

if __name__ == "__main__":
    main()
