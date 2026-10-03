#!/usr/bin/env python3
"""L-Tarpit — کند کردن هکر"""
import os, sys, json, time, hashlib, subprocess, threading
from datetime import datetime

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
LOGS = os.path.join(BASE, "logs")
STATE = os.path.join(BASE, "layer_tarpit_state.json")
TOKEN = open(os.path.join(HOME, "vorix/.tg-token")).read().strip() if os.path.exists(os.path.join(HOME, "vorix/.tg-token")) else ""
CHAT = "175160049"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(os.path.join(LOGS, "layer_tarpit.log"), "a") as f:
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


import socket, threading

PORT = 9999
SLOW = 30  # ثانیه

def handle(conn, addr):
    log("🕸️ Tarpit: connection from " + addr[0])
    try:
        conn.settimeout(2)
        try: conn.recv(1024)
        except: pass
        # فقط نگه‌دار
        time.sleep(SLOW)
        conn.close()
    except: pass
    log("🕸️ Tarpit: released " + addr[0])

def server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("0.0.0.0", PORT))
        s.listen(50)
        log("🕸️ Tarpit listening on " + str(PORT))
        while True:
            try:
                conn, addr = s.accept()
                threading.Thread(target=handle, args=(conn, addr), daemon=True).start()
            except: pass
    except Exception as e:
        log("ERR: " + str(e))

def watch():
    server()

def status():
    print("Port: " + str(PORT))
    print("Delay: " + str(SLOW) + "s")

def test():
    print("Tarpit would listen on port " + str(PORT))


def main():
    if len(sys.argv) < 2:
        print("Usage: layer_tarpit.py {watch|status|test}")
        return
    cmd = sys.argv[1]
    if cmd == "watch": watch()
    elif cmd == "status": status()
    elif cmd == "test": test()

if __name__ == "__main__":
    main()
