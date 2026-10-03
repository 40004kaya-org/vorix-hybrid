#!/usr/bin/env python3
"""L-Mirror — آینه زنده State"""
import os, sys, json, time, hashlib, subprocess, threading
from datetime import datetime

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
LOGS = os.path.join(BASE, "logs")
STATE = os.path.join(BASE, "layer_mirror_state.json")
TOKEN = open(os.path.join(HOME, "vorix/.tg-token")).read().strip() if os.path.exists(os.path.join(HOME, "vorix/.tg-token")) else ""
CHAT = "175160049"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(os.path.join(LOGS, "layer_mirror.log"), "a") as f:
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


MIRROR = os.path.join(BASE, "mirror")
FILES = ["hash_chain.jsonl", "blocklist.json", "playbooks.jsonl",
         "layer10_events.jsonl", "fim_baseline.json"]

def init():
    os.makedirs(MIRROR, exist_ok=True)

def sync():
    init()
    for f in FILES:
        src = os.path.join(BASE, f)
        if os.path.exists(src):
            dst = os.path.join(MIRROR, f)
            try:
                subprocess.run(["cp", src, dst], timeout=5)
            except: pass
    # بک‌آپ تاریخ‌دار
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    try:
        arc = os.path.join(MIRROR, "snap_" + ts + ".tar.gz")
        subprocess.run(["tar","czf",arc,"-C",BASE] + FILES,
                     timeout=15, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log("📦 Mirror snapshot: " + os.path.basename(arc))
    except: pass

def watch():
    log("🪞 Mirror started")
    while True:
        try:
            sync()
        except Exception as e:
            log("ERR: " + str(e))
        time.sleep(300)  # هر ۵ دقیقه

def status():
    init()
    snaps = [f for f in os.listdir(MIRROR) if f.startswith("snap_")]
    print("Mirror: " + MIRROR)
    print("Snapshots: " + str(len(snaps)))

def test():
    sync()
    print("Synced " + str(len(FILES)) + " files")


def main():
    if len(sys.argv) < 2:
        print("Usage: layer_mirror.py {watch|status|test}")
        return
    cmd = sys.argv[1]
    if cmd == "watch": watch()
    elif cmd == "status": status()
    elif cmd == "test": test()

if __name__ == "__main__":
    main()
