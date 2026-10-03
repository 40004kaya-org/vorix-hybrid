#!/usr/bin/env python3
"""L-Honeytoken — رمزهای طعمه"""
import os, sys, json, time, hashlib, subprocess, threading
from datetime import datetime

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
LOGS = os.path.join(BASE, "logs")
STATE = os.path.join(BASE, "layer_honeytoken_state.json")
TOKEN = open(os.path.join(HOME, "vorix/.tg-token")).read().strip() if os.path.exists(os.path.join(HOME, "vorix/.tg-token")) else ""
CHAT = "175160049"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(os.path.join(LOGS, "layer_honeytoken.log"), "a") as f:
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


TOKENS = os.path.join(BASE, "honey_tokens")
TRAPS = {
    "credentials.txt": """# PRODUCTION CREDENTIALS
DB_PASSWORD=Admin@Prod2026!
API_KEY=sk_live_honeypot_trap_xxxxx
AWS_ACCESS=AKIAHONEYTRAP
""",
    "ssh_keys/id_rsa": "# SSH Private Key (honeypot)\n",
    "wallet.txt": "BTC: bc1qHoneypotAddressxxxxx\nETH: 0xHoneypotAddressxxxxx\n",
}

def init():
    os.makedirs(TOKENS, exist_ok=True)
    for name, content in TRAPS.items():
        p = os.path.join(TOKENS, name)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if not os.path.exists(p):
            with open(p, "w") as f:
                f.write(content)

def get_mtimes():
    m = {}
    for name in TRAPS:
        p = os.path.join(TOKENS, name)
        if os.path.exists(p):
            m[name] = os.path.getmtime(p)
    return m

def watch():
    log("🍯 Honeytokens started")
    init()
    base = get_mtimes()
    while True:
        try:
            cur = get_mtimes()
            for k in cur:
                if k in base and cur[k] != base[k]:
                    log("🍯 HONEYTOKEN TRIGGERED: " + k)
                    alert("🍯 <b>Honeytoken triggered!</b>\nFile: <code>" + k + "</code>")
            base = cur
        except: pass
        time.sleep(5)

def status():
    init()
    print("Tokens: " + str(len(TRAPS)))

def test():
    init()
    for n in TRAPS:
        p = os.path.join(TOKENS, n)
        print("  " + ("✅" if os.path.exists(p) else "❌") + " " + n)


def main():
    if len(sys.argv) < 2:
        print("Usage: layer_honeytoken.py {watch|status|test}")
        return
    cmd = sys.argv[1]
    if cmd == "watch": watch()
    elif cmd == "status": status()
    elif cmd == "test": test()

if __name__ == "__main__":
    main()
