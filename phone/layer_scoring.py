#!/usr/bin/env python3
"""L-Scoring — Unified Threat Score"""
import os, sys, json, time, threading
from datetime import datetime, timedelta
from collections import defaultdict, deque

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
STATE_FILE = os.path.join(BASE, "layer_scoring_state.json")

try:
    import requests
    with open(os.path.join(HOME, "vorix/.tg-token")) as f:
        TG = f.read().strip()
except:
    TG = ""
CHAT = "175160049"

# وزن هر لایه در امتیاز نهایی
LAYER_WEIGHTS = {
    "threat_intel": 15,
    "geoip": 10,
    "ua_filter": 10,
    "fingerprint": 15,
    "rate_limit": 10,
    "behavioral": 20,
    "ml_anomaly": 15,
    "identity": 20,
    "network": 10,
    "header": 15,
    "cookie": 10,
    "session": 15,
    "playbook": 25,
}

# آستانه‌های تصمیم
THRESHOLDS = {
    "allow": 0,
    "monitor": 30,
    "throttle": 50,
    "block_temp": 70,
    "block_perm": 90,
}


class UnifiedScoring:
    def __init__(self):
        self.scores = defaultdict(lambda: {"score": 0, "last_update": 0, "signals": deque(maxlen=50)})
        self.lock = threading.Lock()
        self.stats = {"scored": 0, "peak": 0, "started": time.time()}
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

    def add_signal(self, ip, layer, signal_score):
        """اضافه سیگنال از یک لایه"""
        with self.lock:
            now = time.time()
            entry = self.scores[ip]
            
            # Decay: هر ثانیه ۱٪ کاهش
            decay = max(0, (now - entry["last_update"]) * 0.01) if entry["last_update"] else 0
            entry["score"] = max(0, entry["score"] - decay)
            
            # وزن‌دار
            weight = LAYER_WEIGHTS.get(layer, 10)
            weighted = signal_score * (weight / 100)
            entry["score"] = min(100, entry["score"] + weighted)
            entry["last_update"] = now
            entry["signals"].append({
                "ts": now,
                "layer": layer,
                "score": signal_score,
                "weighted": weighted,
            })
            
            self.stats["scored"] += 1
            if entry["score"] > self.stats["peak"]:
                self.stats["peak"] = entry["score"]
            
            self.save_state()
            return entry["score"]

    def get_verdict(self, ip):
        """تصمیم بر اساس امتیاز"""
        entry = self.scores.get(ip)
        if not entry:
            return {"verdict": "allow", "score": 0}
        
        now = time.time()
        decay = max(0, (now - entry["last_update"]) * 0.01)
        score = max(0, entry["score"] - decay)
        
        if score >= THRESHOLDS["block_perm"]:
            verdict = "block_perm"
        elif score >= THRESHOLDS["block_temp"]:
            verdict = "block_temp"
        elif score >= THRESHOLDS["throttle"]:
            verdict = "throttle"
        elif score >= THRESHOLDS["monitor"]:
            verdict = "monitor"
        else:
            verdict = "allow"
        
        return {
            "verdict": verdict,
            "score": round(score, 1),
            "signals": len(entry["signals"]),
        }

    def status(self):
        uptime = int(time.time() - self.stats["started"])
        print(f"\n📊 L-Scoring")
        print(f"═══════════════════════════════")
        print(f"Scored:      {self.stats['scored']}")
        print(f"Peak score:  {self.stats['peak']:.1f}")
        print(f"Tracked IPs: {len(self.scores)}")
        print(f"Uptime:      {uptime // 3600}h {(uptime // 60) % 60}m")
        print()
        print(f"📊 Top scored IPs:")
        top = sorted(self.scores.items(), key=lambda x: -x[1]["score"])[:5]
        for ip, e in top:
            v = self.get_verdict(ip)
            print(f"   • {ip:<18} score={v['score']:<5} → {v['verdict']}")

    def test(self):
        print("🧪 Testing Unified Scoring\n")
        
        ip = "9.9.9.9"
        signals = [
            ("threat_intel", 20),
            ("ua_filter", 30),
            ("behavioral", 40),
            ("ml_anomaly", 25),
            ("playbook", 50),
        ]
        
        print(f"📍 Adding signals for {ip}:")
        for layer, score in signals:
            total = self.add_signal(ip, layer, score)
            v = self.get_verdict(ip)
            print(f"   {layer:<15} +{score} → total={v['score']:<5} verdict={v['verdict']}")
        
        print()
        self.status()


def main():
    if len(sys.argv) < 2:
        print("Usage: layer_scoring.py {test|status|get <ip>|add <ip> <layer> <score>}")
        return
    cmd = sys.argv[1]
    us = UnifiedScoring()
    
    if cmd == "test": us.test()
    elif cmd == "status": us.status()
    elif cmd == "get" and len(sys.argv) > 2:
        print(json.dumps(us.get_verdict(sys.argv[2]), indent=2))
    elif cmd == "add" and len(sys.argv) > 4:
        us.add_signal(sys.argv[2], sys.argv[3], int(sys.argv[4]))
        print("✅ Added")

if __name__ == "__main__":
    main()
