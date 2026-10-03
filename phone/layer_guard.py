#!/usr/bin/env python3
"""L-Guard — محافظ درخواست"""
import os, sys, json, time, hashlib, subprocess, threading
from datetime import datetime

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
LOGS = os.path.join(BASE, "logs")
STATE = os.path.join(BASE, "layer_guard_state.json")
TOKEN = open(os.path.join(HOME, "vorix/.tg-token")).read().strip() if os.path.exists(os.path.join(HOME, "vorix/.tg-token")) else ""
CHAT = "175160049"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(os.path.join(LOGS, "layer_guard.log"), "a") as f:
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


QUEUE = os.path.join(BASE, "guard_queue.jsonl")
SECRET = os.path.join(BASE, ".guard_secret")

def get_secret():
    if not os.path.exists(SECRET):
        with open(SECRET, "w") as f:
            f.write(hashlib.sha256(str(time.time()).encode()).hexdigest())
    return open(SECRET).read().strip()

def sign(cmd):
    s = get_secret()
    return hashlib.sha256((cmd + s).encode()).hexdigest()[:16]

def verify(cmd, sig):
    return sign(cmd) == sig

def watch():
    log("🛡️ Guard started")
    secret = get_secret()
    log("Secret: " + secret[:8] + "...")
    last_pos = 0
    while True:
        try:
            if not os.path.exists(QUEUE):
                time.sleep(2); continue
            size = os.path.getsize(QUEUE)
            if size < last_pos: last_pos = 0
            if size == last_pos:
                time.sleep(2); continue
            with open(QUEUE) as f:
                f.seek(last_pos)
                for line in f.readlines():
                    try:
                        item = json.loads(line)
                        cmd = item.get("cmd","")
                        sig = item.get("sig","")
                        if verify(cmd, sig):
                            log("✅ valid: " + cmd[:30])
                        else:
                            log("❌ INVALID signature: " + cmd[:30])
                            alert("🛡️ Guard: invalid signature\n<code>" + cmd[:100] + "</code>")
                    except: pass
                last_pos = f.tell()
        except: pass
        time.sleep(3)

def status():
    print("Queue: " + QUEUE)
    print("Secret set: " + str(os.path.exists(SECRET)))

def test():
    s = get_secret()
    cmd = "test_command"
    sig = sign(cmd)
    print("Sign: " + sig)
    print("Verify valid: " + str(verify(cmd, sig)))
    print("Verify bad:   " + str(verify(cmd, "bad")))


def main():
    if len(sys.argv) < 2:
        print("Usage: layer_guard.py {watch|status|test}")
        return
    cmd = sys.argv[1]
    if cmd == "watch": watch()
    elif cmd == "status": status()
    elif cmd == "test": test()

if __name__ == "__main__":
    main()
