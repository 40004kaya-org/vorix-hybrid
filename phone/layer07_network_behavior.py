#!/usr/bin/env python3
"""L7 — Network Behavior Analysis"""
import os, sys, json, time, threading
from datetime import datetime
from collections import defaultdict, deque

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
STATE_FILE = os.path.join(BASE, "layer07_state.json")

sys.path.insert(0, BASE)
from layer04_auto_block import AutoBlock

try:
    import requests
    with open(os.path.join(HOME, "vorix/.tg-token")) as f:
        TG = f.read().strip()
except:
    TG = ""
CHAT = "175160049"

CONFIG = {
    "window_seconds": 60,
    "high_volume_threshold": 50,     # ۵۰ اتصال در دقیقه
    "night_activity_hours": (0, 6),  # ۱۲ شب تا ۶ صبح
    "off_hours_multiplier": 2,        # حساسیت ۲x شب‌ها
}


class NetworkBehavior:
    def __init__(self):
        self.traffic = defaultdict(lambda: deque(maxlen=200))
        self.ab = AutoBlock()
        self.lock = threading.Lock()
        self.stats = {"analyzed": 0, "anomalies": 0, "started": time.time()}
        self.load_state()

    def load_state(self):
        try:
            with open(STATE_FILE) as f:
                s = json.load(f)
                self.stats = s.get("stats", self.stats)
        except: pass

    def save_state(self):
        try:
            with open(STATE_FILE, "w") as f:
                json.dump({"stats": self.stats}, f, indent=2)
        except: pass

    def is_night(self):
        h = datetime.now().hour
        start, end = CONFIG["night_activity_hours"]
        return start <= h < end

    def record(self, ip):
        """ثبت یک اتصال"""
        with self.lock:
            self.stats["analyzed"] += 1
            now = time.time()
            self.traffic[ip].append(now)
            
            # پاک کردن قدیمی
            while self.traffic[ip] and now - self.traffic[ip][0] > CONFIG["window_seconds"]:
                self.traffic[ip].popleft()
            
            # چک
            count = len(self.traffic[ip])
            threshold = CONFIG["high_volume_threshold"]
            if self.is_night():
                threshold = threshold // CONFIG["off_hours_multiplier"]
            
            if count >= threshold:
                self.stats["anomalies"] += 1
                self.ab.block(ip, f"network_volume_{count}", score=75, ip_type="temp")
                self._alert(ip, count)
                return True
        return False

    def _alert(self, ip, count):
        if not TG: return
        try:
            night = "🌙 night" if self.is_night() else "☀️ day"
            msg = (
                f"🌐 *Network Behavior Anomaly*\n\n"
                f"IP: `{ip}`\n"
                f"Volume: `{count}/{CONFIG['window_seconds']}s`\n"
                f"Time: `{night}`\n"
                f"⏰ {datetime.now().strftime('%H:%M:%S')}"
            )
            requests.post(
                f"https://api.telegram.org/bot{TG}/sendMessage",
                json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
        except: pass

    def status(self):
        uptime = int(time.time() - self.stats["started"])
        print(f"\n🌐 L7 Network Behavior")
        print(f"═══════════════════════════════")
        print(f"Analyzed:    {self.stats['analyzed']}")
        print(f"Anomalies:   {self.stats['anomalies']}")
        print(f"Tracking:    {len(self.traffic)} IPs")
        print(f"Uptime:      {uptime // 3600}h {(uptime // 60) % 60}m")

    def test(self):
        print("🧪 Testing Network Behavior\n")
        print("📍 Simulating 60 connections from 1.2.3.4...")
        for i in range(60):
            self.record("1.2.3.4")
        print()
        self.status()


def main():
    if len(sys.argv) < 2:
        print("Usage: layer07_network_behavior.py {test|status}")
        return
    cmd = sys.argv[1]
    nb = NetworkBehavior()
    if cmd == "test": nb.test()
    elif cmd == "status": nb.status()

if __name__ == "__main__":
    main()
