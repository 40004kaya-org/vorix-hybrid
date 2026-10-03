#!/usr/bin/env python3
"""L-Watchtower — برج دیده‌بانی"""
import os, sys, json, time, hashlib, subprocess, threading
from datetime import datetime

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
LOGS = os.path.join(BASE, "logs")
STATE = os.path.join(BASE, "layer_watchtower_state.json")
TOKEN = open(os.path.join(HOME, "vorix/.tg-token")).read().strip() if os.path.exists(os.path.join(HOME, "vorix/.tg-token")) else ""
CHAT = "175160049"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(os.path.join(LOGS, "layer_watchtower.log"), "a") as f:
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


WT_LOG = os.path.join(BASE, "watchtower.jsonl")
SOURCES = ["hash_chain.jsonl", "playbooks.jsonl", "layer10_events.jsonl"]

def ingest():
    last = load_state().get("offsets", {})
    count = 0
    for src in SOURCES:
        p = os.path.join(BASE, src)
        if not os.path.exists(p): continue
        size = os.path.getsize(p)
        pos = last.get(src, 0)
        if size < pos: pos = 0
        if size == pos: continue
        try:
            with open(p) as f:
                f.seek(pos)
                for line in f.readlines():
                    try:
                        ev = json.loads(line)
                        ev["_src"] = src
                        ev["_ts"] = datetime.now().isoformat()
                        with open(WT_LOG, "a") as out:
                            out.write(json.dumps(ev) + "\n")
                        count += 1
                    except: pass
                last[src] = f.tell()
        except: pass
    save_state({"offsets": last})
    return count

def watch():
    log("🗼 Watchtower started")
    while True:
        try:
            n = ingest()
            if n: log("🗼 Ingested " + str(n))
        except Exception as e:
            log("ERR: " + str(e))
        time.sleep(10)

def status():
    if os.path.exists(WT_LOG):
        size = os.path.getsize(WT_LOG)
        print("Watchtower log: " + str(size) + " bytes")

def test():
    n = ingest()
    print("Test: ingested " + str(n))


def main():
    if len(sys.argv) < 2:
        print("Usage: layer_watchtower.py {watch|status|test}")
        return
    cmd = sys.argv[1]
    if cmd == "watch": watch()
    elif cmd == "status": status()
    elif cmd == "test": test()

if __name__ == "__main__":
    main()
