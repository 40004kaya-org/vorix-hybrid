#!/usr/bin/env python3
"""L-Whitelist — لیست سفید IP"""
import os, sys, json, time, hashlib, subprocess, threading
from datetime import datetime

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
LOGS = os.path.join(BASE, "logs")
STATE = os.path.join(BASE, "layer_whitelist_state.json")
TOKEN = open(os.path.join(HOME, "vorix/.tg-token")).read().strip() if os.path.exists(os.path.join(HOME, "vorix/.tg-token")) else ""
CHAT = "175160049"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(os.path.join(LOGS, "layer_whitelist.log"), "a") as f:
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


WL_FILE = os.path.join(BASE, "whitelist.json")

DEFAULT = {
    "ips": ["127.0.0.1", "::1"],
    "cidrs": ["192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12"],
    "updated": datetime.now().isoformat()
}

def ensure():
    if not os.path.exists(WL_FILE):
        with open(WL_FILE, "w") as f:
            json.dump(DEFAULT, f, indent=2)

def is_safe(ip):
    ensure()
    try:
        wl = json.load(open(WL_FILE))
        if ip in wl.get("ips", []): return True
        # چک /8 /16 ساده
        for cidr in wl.get("cidrs", []):
            net = cidr.split("/")[0]
            if ip.startswith(net.rsplit(".", 1)[0] + "."):
                return True
    except: pass
    return False

def watch():
    log("✅ Whitelist started")
    ensure()
    log("Loaded " + str(len(json.load(open(WL_FILE)).get("ips", []))) + " IPs")
    while True:
        time.sleep(60)

def status():
    ensure()
    wl = json.load(open(WL_FILE))
    print("IPs:   " + str(len(wl.get("ips", []))))
    print("CIDRs: " + str(len(wl.get("cidrs", []))))

def test():
    print("127.0.0.1: " + str(is_safe("127.0.0.1")))
    print("8.8.8.8:   " + str(is_safe("8.8.8.8")))
    print("192.168.1.5: " + str(is_safe("192.168.1.5")))


def main():
    if len(sys.argv) < 2:
        print("Usage: layer_whitelist.py {watch|status|test}")
        return
    cmd = sys.argv[1]
    if cmd == "watch": watch()
    elif cmd == "status": status()
    elif cmd == "test": test()

if __name__ == "__main__":
    main()
