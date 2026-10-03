#!/usr/bin/env python3
"""L-Heartbeat — نبض سیستم"""
import os, sys, json, time, hashlib, subprocess, threading
from datetime import datetime

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
LOGS = os.path.join(BASE, "logs")
STATE = os.path.join(BASE, "layer_heartbeat_state.json")
TOKEN = open(os.path.join(HOME, "vorix/.tg-token")).read().strip() if os.path.exists(os.path.join(HOME, "vorix/.tg-token")) else ""
CHAT = "175160049"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(os.path.join(LOGS, "layer_heartbeat.log"), "a") as f:
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


LAYERS = [
    "layer01_selfdefense","layer02_threat_intel","layer03_behavioral",
    "layer04_auto_block","layer05_data_quarantine","layer06_geoip_block",
    "layer08_network_monitor","layer09_rate_limiter","layer10_red_alert",
    "layer17_watchdog","layer19_password_leak","layer21_ml_anomaly",
    "layer25_ssl_monitor","layer29_30_identity","layer_fim","layer_rootkit",
    "layer_multichannel","layer_livefeed","vorix_bot","sync_loop",
]

def check_all():
    alive = []
    dead = []
    for l in LAYERS:
        if pgrep(l): alive.append(l)
        else: dead.append(l)
    return alive, dead

def watch():
    log("💓 Heartbeat started")
    while True:
        try:
            alive, dead = check_all()
            s = load_state()
            s["ts"] = datetime.now().isoformat()
            s["alive"] = len(alive)
            s["dead"] = len(dead)
            s["dead_list"] = dead
            save_state(s)
            
            if len(dead) >= 5:
                alert("💓 Heartbeat: " + str(len(dead)) + " layers dead!\n" + "\n".join(dead[:5]))
                log("⚠ " + str(len(dead)) + " dead layers")
            elif len(dead) > 0:
                log("😐 " + str(len(dead)) + " dead: " + ", ".join(dead[:3]))
            else:
                log("💚 all " + str(len(alive)) + " alive")
        except Exception as e:
            log("ERR: " + str(e))
        time.sleep(20)

def status():
    alive, dead = check_all()
    print("Alive: " + str(len(alive)))
    print("Dead:  " + str(len(dead)))
    if dead: print("Dead list: " + ", ".join(dead))

def test():
    alive, dead = check_all()
    print("OK - " + str(len(alive)) + " alive, " + str(len(dead)) + " dead")


def main():
    if len(sys.argv) < 2:
        print("Usage: layer_heartbeat.py {watch|status|test}")
        return
    cmd = sys.argv[1]
    if cmd == "watch": watch()
    elif cmd == "status": status()
    elif cmd == "test": test()

if __name__ == "__main__":
    main()
