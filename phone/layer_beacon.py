#!/usr/bin/env python3
"""L-Beacon — شکار سیگنال خروجی (C2)"""
import os, sys, json, time, hashlib, subprocess, threading
from datetime import datetime

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
LOGS = os.path.join(BASE, "logs")
STATE = os.path.join(BASE, "layer_beacon_state.json")
TOKEN = open(os.path.join(HOME, "vorix/.tg-token")).read().strip() if os.path.exists(os.path.join(HOME, "vorix/.tg-token")) else ""
CHAT = "175160049"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(os.path.join(LOGS, "layer_beacon.log"), "a") as f:
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


WHITELIST = ["telegram.org", "api.telegram.org", "github.com",
             "api.github.com", "raw.githubusercontent.com",
             "google.com", "cloudflare.com"]

def get_connections():
    try:
        r = subprocess.run(["ss", "-tunap"], capture_output=True, text=True, timeout=5)
        lines = r.stdout.split("\n")
        conns = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 5 and parts[0] in ("tcp","udp"):
                peer = parts[4]
                proc = parts[-1] if len(parts) > 5 else "?"
                conns.append({"peer": peer, "proc": proc})
        return conns
    except: return []

def is_whitelisted(peer):
    for w in WHITELIST:
        if w in peer:
            return True
    return False

def watch():
    log("📡 Beacon started")
    seen = set()
    while True:
        try:
            conns = get_connections()
            for c in conns:
                key = c["peer"] + "|" + c["proc"]
                if key in seen: continue
                seen.add(key)
                if not is_whitelisted(c["peer"]):
                    log("📡 new outbound: " + c["peer"] + " (" + c["proc"] + ")")
                    # فقط اگه پروتکل عجیب بود
                    port = 0
                    try: port = int(c["peer"].split(":")[-1])
                    except: pass
                    if port and port not in (80, 443, 53, 22):
                        alert("📡 <b>Suspicious outbound</b>\nPeer: <code>" + c["peer"] + "</code>\nProc: " + c["proc"] + "\nPort: " + str(port))
            if len(seen) > 1000: seen.clear()
        except Exception as e:
            log("ERR: " + str(e))
        time.sleep(20)

def status():
    conns = get_connections()
    print("Active: " + str(len(conns)))

def test():
    conns = get_connections()
    print("Test OK - " + str(len(conns)) + " connections")


def main():
    if len(sys.argv) < 2:
        print("Usage: layer_beacon.py {watch|status|test}")
        return
    cmd = sys.argv[1]
    if cmd == "watch": watch()
    elif cmd == "status": status()
    elif cmd == "test": test()

if __name__ == "__main__":
    main()
