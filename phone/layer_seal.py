#!/usr/bin/env python3
"""L-Seal — مهر اصالت فایل‌ها"""
import os, sys, json, time, hashlib, subprocess, threading
from datetime import datetime

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
LOGS = os.path.join(BASE, "logs")
STATE = os.path.join(BASE, "layer_seal_state.json")
TOKEN = open(os.path.join(HOME, "vorix/.tg-token")).read().strip() if os.path.exists(os.path.join(HOME, "vorix/.tg-token")) else ""
CHAT = "175160049"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(os.path.join(LOGS, "layer_seal.log"), "a") as f:
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


SEAL_FILE = os.path.join(BASE, "seal_hashes.json")

def hash_file(p):
    try:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except: return None

def collect():
    result = {}
    for f in os.listdir(BASE):
        if f.endswith(".py"):
            p = os.path.join(BASE, f)
            h = hash_file(p)
            if h: result[f] = h
    return result

def seal():
    result = collect()
    with open(SEAL_FILE, "w") as f:
        json.dump({"ts": datetime.now().isoformat(), "files": result}, f, indent=2)
    log("🔒 Sealed " + str(len(result)) + " files")
    return result

def watch():
    log("🔒 Seal started")
    if not os.path.exists(SEAL_FILE):
        base = seal()
    else:
        base = json.load(open(SEAL_FILE)).get("files", {})
    
    while True:
        try:
            cur = collect()
            for f, h in cur.items():
                if f in base and base[f] != h:
                    log("⚠ SEAL BROKEN: " + f)
                    alert("🔒 <b>Seal broken!</b>\nFile: <code>" + f + "</code>")
                elif f not in base:
                    log("➕ new file: " + f)
            for f in base:
                if f not in cur:
                    log("➖ missing: " + f)
            base = cur
        except Exception as e:
            log("ERR: " + str(e))
        time.sleep(30)

def status():
    if os.path.exists(SEAL_FILE):
        d = json.load(open(SEAL_FILE))
        print("Sealed: " + d.get("ts","?"))
        print("Files:  " + str(len(d.get("files", {}))))
    else:
        print("Not sealed yet")

def test():
    r = seal()
    print("Sealed " + str(len(r)) + " files")


def main():
    if len(sys.argv) < 2:
        print("Usage: layer_seal.py {watch|status|test}")
        return
    cmd = sys.argv[1]
    if cmd == "watch": watch()
    elif cmd == "status": status()
    elif cmd == "test": test()

if __name__ == "__main__":
    main()
