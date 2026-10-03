#!/usr/bin/env python3
"""L9 — Rate Limiter (Anti-Flood)"""
import os, sys, json, time, threading
from datetime import datetime, timedelta
from collections import defaultdict, deque

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
STATE_FILE = os.path.join(BASE, "layer09_state.json")

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
    # Window limits (per IP)
    "per_minute": 60,             # حداکثر ۶۰ درخواست در دقیقه
    "per_hour": 500,              # حداکثر ۵۰۰ در ساعت
    "per_day": 2000,              # حداکثر ۲۰۰۰ در روز
    
    # Burst detection
    "burst_seconds": 5,
    "burst_max": 20,               # حداکثر ۲۰ درخواست در ۵ ثانیه
    
    # Auto-block thresholds
    "violation_threshold": 3,      # ۳ بار تخلف → بلاک
    "violation_window": 300,       # در ۵ دقیقه
    
    # Global
    "global_per_minute": 500,      # کل سیستم
}

PRIVATE = ("127.", "10.", "192.168.", "172.16.", "172.17.", "172.18.",
           "172.19.", "172.20.", "172.21.", "172.22.", "172.23.",
           "172.24.", "172.25.", "172.26.", "172.27.", "172.28.",
           "172.29.", "172.30.", "172.31.", "169.254.")

class RateLimiter:
    def __init__(self):
        # ip → deque of timestamps
        self.requests = defaultdict(deque)
        self.violations = defaultdict(list)  # ip → [timestamps]
        self.global_requests = deque()
        self.ab = AutoBlock()
        self.lock = threading.Lock()
        self.stats = {
            "total": 0,
            "blocked": 0,
            "limited": 0,
            "started": time.time(),
        }
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

    def is_private(self, ip):
        return any(ip.startswith(p) for p in PRIVATE)

    def cleanup(self, ip):
        """پاک کردن رکوردهای قدیمی"""
        now = time.time()
        # روز
        while self.requests[ip] and now - self.requests[ip][0] > 86400:
            self.requests[ip].popleft()

    def check(self, ip):
        """چک rate limit یک IP"""
        if not ip or self.is_private(ip):
            return {"action": "allow", "reason": "private"}

        now = time.time()

        with self.lock:
            self.stats["total"] += 1

            # چک بلاک بودن
            if self.ab.is_blocked(ip):
                self.stats["blocked"] += 1
                return {"action": "block", "reason": "blacklisted"}

            # اضافه درخواست
            self.requests[ip].append(now)
            self.global_requests.append(now)
            self.cleanup(ip)

            # پاک کردن global
            while self.global_requests and now - self.global_requests[0] > 60:
                self.global_requests.popleft()

            # چک‌های Rate Limit
            reqs = self.requests[ip]

            # Burst: ۵ ثانیه
            burst = sum(1 for t in reqs if now - t < CONFIG["burst_seconds"])
            if burst > CONFIG["burst_max"]:
                return self._violate(ip, f"burst_{burst}", "burst")

            # Per minute
            per_min = sum(1 for t in reqs if now - t < 60)
            if per_min > CONFIG["per_minute"]:
                return self._violate(ip, f"per_minute_{per_min}", "minute")

            # Per hour
            per_hour = sum(1 for t in reqs if now - t < 3600)
            if per_hour > CONFIG["per_hour"]:
                return self._violate(ip, f"per_hour_{per_hour}", "hour")

            # Per day
            per_day = len(reqs)
            if per_day > CONFIG["per_day"]:
                return self._violate(ip, f"per_day_{per_day}", "day")

            # Global
            if len(self.global_requests) > CONFIG["global_per_minute"]:
                return {"action": "throttle", "reason": "global_limit"}

        return {"action": "allow"}

    def _violate(self, ip, reason, level):
        """ثبت تخلف"""
        now = time.time()
        self.violations[ip].append(now)

        # پاک کردن قدیمی
        self.violations[ip] = [
            t for t in self.violations[ip]
            if now - t < CONFIG["violation_window"]
        ]

        vcount = len(self.violations[ip])
        self.stats["limited"] += 1

        # اگه به آستانه رسید → بلاک
        if vcount >= CONFIG["violation_threshold"]:
            self.ab.block(ip, f"rate_limit_{reason}", score=75, ip_type="temp")
            self._alert(ip, reason, vcount, "BLOCKED")
            return {"action": "block", "reason": reason, "violations": vcount}

        self._alert(ip, reason, vcount, "WARN")
        return {"action": "throttle", "reason": reason, "violations": vcount}

    def _alert(self, ip, reason, count, action):
        if not TG: return
        try:
            icon = "🚫" if action == "BLOCKED" else "⚠️"
            msg = (
                f"{icon} *Rate Limit {action}*\n\n"
                f"IP: `{ip}`\n"
                f"Reason: `{reason}`\n"
                f"Violations: `{count}`\n"
                f"Time: {datetime.now().strftime('%H:%M:%S')}"
            )
            requests.post(
                f"https://api.telegram.org/bot{TG}/sendMessage",
                json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
        except: pass

    def watch_queue(self):
        """پایش queue.jsonl"""
        qfile = os.path.join(BASE, "queue.jsonl")
        last_pos = 0

        print(f"⏱️  L9 Rate Limiter Watcher")
        print(f"📊 Limits:")
        print(f"   per_minute: {CONFIG['per_minute']}")
        print(f"   per_hour:   {CONFIG['per_hour']}")
        print(f"   per_day:    {CONFIG['per_day']}")
        print(f"   burst_max:  {CONFIG['burst_max']}/{CONFIG['burst_seconds']}s")
        print()

        while True:
            try:
                if not os.path.exists(qfile):
                    time.sleep(2); continue
                size = os.path.getsize(qfile)
                if size < last_pos: last_pos = 0
                if size == last_pos:
                    time.sleep(2); continue

                with open(qfile) as f:
                    f.seek(last_pos)
                    lines = f.readlines()
                    last_pos = f.tell()

                for line in lines:
                    line = line.strip()
                    if not line: continue
                    try:
                        e = json.loads(line)
                        ip = e.get("source_ip") or e.get("metadata", {}).get("source_ip")
                        if ip:
                            r = self.check(ip)
                            if r["action"] in ("block", "throttle"):
                                print(f"⚠️ {r['action']}: {ip} ({r['reason']})")
                    except: pass

                self.save_state()
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"⚠️ {e}")
                time.sleep(5)

    def status(self):
        uptime = int(time.time() - self.stats["started"])
        h, m = divmod(uptime // 60, 60)
        print(f"\n⏱️  Rate Limiter Status")
        print(f"═══════════════════════════")
        print(f"Uptime:    {h}h {m}m")
        print(f"Total:     {self.stats['total']}")
        print(f"Limited:   {self.stats['limited']}")
        print(f"Blocked:   {self.stats['blocked']}")
        print(f"\n📊 Active IPs: {len(self.requests)}")

    def test(self, ip, count=100):
        """تست — شبیه‌سازی count درخواست"""
        print(f"🧪 Testing {ip} with {count} requests...")
        results = {"allow": 0, "throttle": 0, "block": 0}
        for i in range(count):
            r = self.check(ip)
            results[r["action"]] += 1
        print(f"\nResults:")
        for k, v in results.items():
            print(f"   {k}: {v}")
        print(f"\n📊 After test:")
        self.status()

def main():
    if len(sys.argv) < 2:
        print("Usage: layer09_rate_limiter.py {watch|status|test <ip>}")
        return
    cmd = sys.argv[1]
    rl = RateLimiter()

    if cmd == "watch": rl.watch_queue()
    elif cmd == "status": rl.status()
    elif cmd == "test":
        ip = sys.argv[2] if len(sys.argv) > 2 else "1.2.3.4"
        rl.test(ip)

if __name__ == "__main__":
    main()
