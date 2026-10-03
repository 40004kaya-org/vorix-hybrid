#!/usr/bin/env python3
"""L-Quarantine — قرنطینه فایل‌های مشکوک"""
import os, sys, json, time, hashlib, subprocess, threading
from datetime import datetime

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
LOGS = os.path.join(BASE, "logs")
STATE = os.path.join(BASE, "layer_quarantine_state.json")
TOKEN = open(os.path.join(HOME, "vorix/.tg-token")).read().strip() if os.path.exists(os.path.join(HOME, "vorix/.tg-token")) else ""
CHAT = "175160049"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(os.path.join(LOGS, "layer_quarantine.log"), "a") as f:
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


QUAR = os.path.join(BASE, "quarantine_locked")
TRIGGER = os.path.join(BASE, "quarantine_trigger.jsonl")

def init():
    os.makedirs(QUAR, exist_ok=True)

def quarantine(fpath, reason):
    init()
    if not os.path.exists(fpath):
        log("❌ file not exists: " + fpath)
        return False
    try:
        name = os.path.basename(fpath)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        dest = os.path.join(QUAR, ts + "_" + name)
        h = hash_file(fpath)
        subprocess.run(["mv", fpath, dest], timeout=5)
        with open(os.path.join(QUAR, "index.jsonl"), "a") as f:
            f.write(json.dumps({
                "ts": ts, "from": fpath, "to": dest,
                "hash": h, "reason": reason
            }) + "\n")
        log("🔒 Quarantined: " + name)
        alert("🔒 <b>Quarantined</b>\nFile: <code>" + name + "</code>\nReason: " + reason)
        return True
    except Exception as e:
        log("ERR: " + str(e))
        return False

def hash_file(p):
    try:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for c in iter(lambda: f.read(8192), b""): h.update(c)
        return h.hexdigest()
    except: return None

def watch():
    log("🔒 Quarantine started")
    init()
    last = 0
    while True:
        try:
            if os.path.exists(TRIGGER):
                size = os.path.getsize(TRIGGER)
                if size > last:
                    with open(TRIGGER) as f:
                        f.seek(last)
                        for line in f.readlines():
                            try:
                                item = json.loads(line)
                                quarantine(item["path"], item.get("reason","?"))
                            except: pass
                        last = f.tell()
        except: pass
        time.sleep(5)

def status():
    init()
    files = [f for f in os.listdir(QUAR) if not f.endswith(".jsonl")]
    print("Quarantined: " + str(len(files)))
    for f in files[:10]: print("  " + f)

def test():
    init()
    print("Quarantine dir: " + QUAR)


def main():
    if len(sys.argv) < 2:
        print("Usage: layer_quarantine.py {watch|status|test}")
        return
    cmd = sys.argv[1]
    if cmd == "watch": watch()
    elif cmd == "status": status()
    elif cmd == "test": test()

if __name__ == "__main__":
    main()
