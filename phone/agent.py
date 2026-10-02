#!/usr/bin/env python3
"""VORIX Phone Agent — Termux"""
import os, sys, json, time, socket, threading, subprocess, hashlib
from datetime import datetime
from collections import deque
import requests

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
CONFIG_FILE = os.path.join(BASE, "config.json")
QUEUE_FILE = os.path.join(BASE, "queue.jsonl")

CFG = json.load(open(CONFIG_FILE))
CLOUD_URL = CFG["cloud_url"].rstrip("/")
API_KEY = CFG["api_key"]
AGENT_ID = CFG["agent_id"]
AGENT_NAME = CFG["agent_name"]

queue = deque(maxlen=10000)
queue_lock = threading.Lock()
stats = {"sent": 0, "failed": 0, "hits": 0}

def save_queue():
    with queue_lock:
        try:
            with open(QUEUE_FILE, "w") as f:
                for e in queue: f.write(json.dumps(e) + "\n")
        except: pass

def load_queue():
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE) as f:
                for line in f:
                    try: queue.append(json.loads(line))
                    except: pass
        except: pass

_geo = {}
def geoip(ip):
    if ip in _geo: return _geo[ip]
    if not ip or ip.startswith(("127.","10.","192.168.","172.")):
        _geo[ip] = {}
        return {}
    try:
        d = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,city,isp", timeout=3).json()
        if d.get("status") == "success":
            _geo[ip] = d
            return d
    except: pass
    _geo[ip] = {}
    return {}

def push(logs):
    if not logs: return 0
    try:
        r = requests.post(f"{CLOUD_URL}/api/v1/logs/batch", json=logs,
                          headers={"X-API-Key": API_KEY}, timeout=15)
        if r.status_code == 200:
            stats["sent"] += len(logs)
            return len(logs)
    except: pass
    stats["failed"] += 1
    return 0

def heartbeat():
    try:
        requests.post(f"{CLOUD_URL}/api/v1/agent/heartbeat",
                      json={"agent_id": AGENT_ID, "name": AGENT_NAME, "version": "1.0",
                            "metadata": {"hostname": socket.gethostname(), "queue": len(queue)}},
                      headers={"X-API-Key": API_KEY}, timeout=10)
    except: pass

def hp_handle(cs, ip, name, banner):
    try:
        if banner:
            try: cs.send(banner.encode())
            except: pass
        cs.settimeout(5)
        data = b""
        try:
            while len(data) < 4096:
                c = cs.recv(1024)
                if not c: break
                data += c
                if len(data) > 300: break
        except: pass
        d = data.decode("utf-8", errors="replace") if data else "(connection)"
        g = geoip(ip)
        score = 50
        if any(x in d.lower() for x in ["sql","union","or 1=1"]): score += 30
        score = min(100, score)
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "agent_id": AGENT_ID,
            "severity": "CRITICAL" if score >= 70 else "WARN",
            "gate": "GATE01",
            "module": "LOCAL_HONEYPOT",
            "event_type": f"{name}_HIT",
            "source_ip": ip,
            "country": g.get("country", "?"),
            "city": g.get("city", "?"),
            "isp": g.get("isp", "?"),
            "score": score,
            "message": f"Honeypot {name} hit from {ip}",
            "metadata": {"honeypot": name, "data": d[:200]}
        }
        with queue_lock:
            queue.append(event)
        stats["hits"] += 1
        print(f"[🍯] {name} <- {ip} ({g.get('country','?')})")
    except: pass
    finally:
        try: cs.close()
        except: pass

def hp_handler(port, name, banner):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("0.0.0.0", port))
        s.listen(20)
    except OSError as e:
        print(f"[!] {name}:{port} - {e}")
        return
    print(f"[+] {name:<15} :{port}")
    while True:
        try:
            cs, addr = s.accept()
            threading.Thread(target=hp_handle, args=(cs, addr[0], name, banner), daemon=True).start()
        except: break

def start_honeypots():
    traps = [
        (8888, "HTTP-Admin", "HTTP/1.1 200 OK\r\nServer: nginx\r\n\r\n"),
        (2222, "SSH-Fake", "SSH-2.0-OpenSSH_7.4\r\n"),
        (2121, "FTP-Fake", "220 FTP\r\n"),
        (3306, "MySQL-Fake", ""),
        (6379, "Redis-Fake", ""),
    ]
    for port, name, banner in traps:
        threading.Thread(target=hp_handler, args=(port, name, banner), daemon=True).start()

def sync_loop():
    while True:
        try:
            with queue_lock:
                batch = list(queue)[:200]
            if batch:
                sent = push(batch)
                if sent:
                    with queue_lock:
                        for _ in range(sent):
                            if queue: queue.popleft()
                    save_queue()
                    print(f"[+] Sent {sent} | queue: {len(queue)}")
            heartbeat()
            time.sleep(30)
        except: time.sleep(60)

def main():
    print("=" * 55)
    print("   VORIX PHONE AGENT")
    print("=" * 55)
    print(f"  Cloud:  {CLOUD_URL}")
    print(f"  Agent:  {AGENT_NAME} ({AGENT_ID})")
    print()
    load_queue()
    print(f"[*] Queue: {len(queue)} items")
    print()
    start_honeypots()
    time.sleep(1)
    print()
    print("[*] Sync loop started (every 30s)")
    print()
    try:
        sync_loop()
    except KeyboardInterrupt:
        print("\n[!] Stopping...")
        save_queue()

if __name__ == "__main__":
    main()
