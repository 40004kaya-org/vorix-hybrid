#!/usr/bin/env python3
"""L-Chaos — تست خودکار حمله"""
import os, sys, json, time, hashlib, subprocess, threading
from datetime import datetime

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
LOGS = os.path.join(BASE, "logs")
STATE = os.path.join(BASE, "layer_chaos_state.json")
TOKEN = open(os.path.join(HOME, "vorix/.tg-token")).read().strip() if os.path.exists(os.path.join(HOME, "vorix/.tg-token")) else ""
CHAT = "175160049"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(os.path.join(LOGS, "layer_chaos.log"), "a") as f:
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


TESTS = [
    {"name": "sql_injection", "event": {"severity":"CRITICAL","event_type":"SQL_INJECTION","src_ip":"127.0.0.1","message":"chaos test"},
    {"name": "brute_force",   "event": {"severity":"CRITICAL","event_type":"BRUTE_FORCE","src_ip":"127.0.0.1","message":"50 attempts"},
    {"name": "port_scan",     "event": {"severity":"WARN","event_type":"PORT_SCAN","src_ip":"127.0.0.1","message":"nmap"},
]

def fire(ev):
    q = os.path.join(BASE, "queue.jsonl")
    with open(q, "a") as f:
        f.write(json.dumps(ev) + "\n")

def watch():
    log("🎲 Chaos started")
    while True:
        try:
            # هر ۱ ساعت
            time.sleep(3600)
            for t in TESTS:
                log("🎲 Firing: " + t["name"])
                fire(t["event"])
                time.sleep(2)
        except: time.sleep(600)

def status():
    print("Tests: " + str(len(TESTS)))
    for t in TESTS: print("  " + t["name"])

def test():
    for t in TESTS:
        fire(t["event"])
        log("🎲 fired: " + t["name"])
    print("Fired " + str(len(TESTS)) + " test events")


def main():
    if len(sys.argv) < 2:
        print("Usage: layer_chaos.py {watch|status|test}")
        return
    cmd = sys.argv[1]
    if cmd == "watch": watch()
    elif cmd == "status": status()
    elif cmd == "test": test()

if __name__ == "__main__":
    main()
