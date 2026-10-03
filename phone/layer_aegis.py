#!/usr/bin/env python3
"""L-Aegis — سپر کل سیستم"""
import os, sys, json, time, hashlib, subprocess, threading
from datetime import datetime

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
LOGS = os.path.join(BASE, "logs")
STATE = os.path.join(BASE, "layer_aegis_state.json")
TOKEN = open(os.path.join(HOME, "vorix/.tg-token")).read().strip() if os.path.exists(os.path.join(HOME, "vorix/.tg-token")) else ""
CHAT = "175160049"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(os.path.join(LOGS, "layer_aegis.log"), "a") as f:
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


from collections import deque

HISTORY = deque(maxlen=20)
THRESHOLD = 5  # اگه ۵+ لایه مشکل داشتن → اضطراری

LAYERS = [
    "layer01_selfdefense","layer03_behavioral","layer04_auto_block",
    "layer06_geoip_block","layer08_network_monitor","layer09_rate_limiter",
    "layer10_red_alert","layer17_watchdog","layer19_password_leak",
    "layer21_ml_anomaly","layer25_ssl_monitor","layer29_30_identity",
    "layer_fim","layer_rootkit","layer_multichannel","layer_livefeed",
]

def count_dead():
    dead = 0
    for l in LAYERS:
        if not pgrep(l): dead += 1
    return dead

def trigger_emergency(dead_count):
    log("🚨 AEGIS EMERGENCY: " + str(dead_count) + " layers dead!")
    alert(
        "🚨 <b>AEGIS EMERGENCY</b>\n\n"
        + str(dead_count) + " لایه قطع شده‌اند!\n"
        "سیستم در وضعیت بحرانی"
    )
    # Snapshot
    try:
        snapshot_dir = os.path.join(BASE, "aegis_snapshot")
        os.makedirs(snapshot_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        for f in ["hash_chain.jsonl", "blocklist.json"]:
            p = os.path.join(BASE, f)
            if os.path.exists(p):
                subprocess.run(["cp", p, os.path.join(snapshot_dir, ts + "_" + f)], timeout=5)
        log("📦 Snapshot saved: " + ts)
    except Exception as e:
        log("Snapshot err: " + str(e))

def watch():
    log("🛡️ Aegis started")
    emergency_active = False
    while True:
        try:
            dead = count_dead()
            HISTORY.append(dead)
            log("🛡️ Aegis: " + str(dead) + " dead, history avg: " + str(sum(HISTORY)/len(HISTORY)))
            
            # اگه ۳ بار پشت سر هم >= threshold
            if len(HISTORY) >= 3 and all(h >= THRESHOLD for h in list(HISTORY)[-3:]):
                if not emergency_active:
                    trigger_emergency(dead)
                    emergency_active = True
            elif dead < 2:
                emergency_active = False
        except Exception as e:
            log("ERR: " + str(e))
        time.sleep(15)

def status():
    dead = count_dead()
    print("Dead: " + str(dead) + "/" + str(len(LAYERS)))
    print("Threshold: " + str(THRESHOLD))
    print("History: " + str(list(HISTORY)))

def test():
    dead = count_dead()
    print("Test OK - " + str(dead) + " dead right now")


def main():
    if len(sys.argv) < 2:
        print("Usage: layer_aegis.py {watch|status|test}")
        return
    cmd = sys.argv[1]
    if cmd == "watch": watch()
    elif cmd == "status": status()
    elif cmd == "test": test()

if __name__ == "__main__":
    main()
