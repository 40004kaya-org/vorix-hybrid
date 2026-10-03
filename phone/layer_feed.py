#!/usr/bin/env python3
"""L-Feed — تغذیه تهدید (Threat Intel)"""
import os, sys, json, time, hashlib, subprocess, threading
from datetime import datetime

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
LOGS = os.path.join(BASE, "logs")
STATE = os.path.join(BASE, "layer_feed_state.json")
TOKEN = open(os.path.join(HOME, "vorix/.tg-token")).read().strip() if os.path.exists(os.path.join(HOME, "vorix/.tg-token")) else ""
CHAT = "175160049"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(os.path.join(LOGS, "layer_feed.log"), "a") as f:
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


FEED_FILE = os.path.join(BASE, "threat_feed.json")
BL_FILE = os.path.join(BASE, "blocklist.json")
FEEDS = [
    "https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt",
]

def download(url):
    try:
        import requests
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            return r.text
    except: pass
    return None

def parse(text):
    ips = []
    if not text: return ips
    for line in text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"): continue
        parts = line.split("\t")
        if parts and parts[0].count(".") == 3:
            ips.append(parts[0])
    return ips[:5000]

def update():
    log("🌐 Feed: downloading...")
    all_ips = []
    for url in FEEDS:
        text = download(url)
        ips = parse(text)
        all_ips.extend(ips)
        log("  " + str(len(ips)) + " from " + url.split("/")[-1])
    
    with open(FEED_FILE, "w") as f:
        json.dump({"ts": datetime.now().isoformat(), "count": len(all_ips), "ips": all_ips}, f)
    log("🌐 Feed updated: " + str(len(all_ips)) + " IPs")

def watch():
    log("🌐 Feed started")
    update()
    while True:
        try:
            time.sleep(6 * 3600)
            update()
        except: time.sleep(600)

def status():
    if os.path.exists(FEED_FILE):
        d = json.load(open(FEED_FILE))
        print("IPs: " + str(d.get("count", 0)))
        print("Ts:  " + d.get("ts", "?"))
    else:
        print("Not downloaded")

def test():
    text = "1.2.3.4\t1\n5.6.7.8\t2"
    ips = parse(text)
    print("Parse test: " + str(ips))


def main():
    if len(sys.argv) < 2:
        print("Usage: layer_feed.py {watch|status|test}")
        return
    cmd = sys.argv[1]
    if cmd == "watch": watch()
    elif cmd == "status": status()
    elif cmd == "test": test()

if __name__ == "__main__":
    main()
