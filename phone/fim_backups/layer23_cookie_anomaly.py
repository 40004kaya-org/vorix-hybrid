#!/usr/bin/env python3
"""L23 — Cookie Anomaly Detection"""
import os, sys, json, time, re, hashlib, threading
from datetime import datetime, timedelta
from collections import defaultdict

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
STATE_FILE = os.path.join(BASE, "layer23_state.json")

sys.path.insert(0, BASE)
from layer04_auto_block import AutoBlock

try:
    import requests
    with open(os.path.join(HOME, "vorix/.tg-token")) as f:
        TG = f.read().strip()
except:
    TG = ""
CHAT = "175160049"

# الگوهای حمله در کوکی
COOKIE_ATTACK_PATTERNS = [
    (r"<script", "XSS"),
    (r"javascript:", "XSS"),
    (r"onerror\s*=", "XSS"),
    (r"union\s+select", "SQLI"),
    (r"'\s*or\s+", "SQLI"),
    (r"\.\./", "PATH_TRAVERSAL"),
    (r"etc/passwd", "LFI"),
    (r";\s*cat\s+", "COMMAND_INJECTION"),
]


class CookieAnomaly:
    def __init__(self):
        self.cookie_history = defaultdict(list)  # ip → [(cookie_hash, ts)]
        self.ab = AutoBlock()
        self.lock = threading.Lock()
        self.stats = {"checked": 0, "anomalies": 0, "blocked": 0, "started": time.time()}
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

    def check_cookie(self, cookie_str, ip):
        """چک یک کوکی"""
        if not cookie_str:
            return []

        with self.lock:
            self.stats["checked"] += 1
            anomalies = []
            cookie_lower = cookie_str.lower()

            # ۱. الگوهای حمله
            for pattern, attack_type in COOKIE_ATTACK_PATTERNS:
                if re.search(pattern, cookie_lower):
                    anomalies.append({
                        "type": attack_type,
                        "detail": f"Pattern: {pattern[:30]}",
                        "severity": "CRITICAL"
                    })
                    break

            # ۲. کوکی با طول غیرعادی
            if len(cookie_str) > 4000:
                anomalies.append({
                    "type": "OVERSIZED_COOKIE",
                    "detail": f"Length: {len(cookie_str)}",
                    "severity": "WARN"
                })

            # ۳. کوکی‌های تکراری
            cookie_hash = hashlib.md5(cookie_str.encode()).hexdigest()[:16]
            now = time.time()
            self.cookie_history[ip].append((cookie_hash, now))
            self.cookie_history[ip] = [
                (h, t) for h, t in self.cookie_history[ip]
                if now - t < 60
            ]

            # اگه یک IP ۱۰ کوکی مختلف در دقیقه فرستاد
            unique_hashes = len(set(h for h, t in self.cookie_history[ip]))
            if unique_hashes > 10:
                anomalies.append({
                    "type": "COOKIE_ROTATION",
                    "detail": f"{unique_hashes} unique cookies in 60s",
                    "severity": "SUSPICIOUS"
                })

            if anomalies:
                self.stats["anomalies"] += 1
                # اگه CRITICAL → بلاک
                for a in anomalies:
                    if a["severity"] == "CRITICAL":
                        self.ab.block(ip, f"cookie_{a['type'].lower()}", score=85, ip_type="temp")
                        self.stats["blocked"] += 1
                        break
                self._alert(ip, anomalies)

            return anomalies

    def _alert(self, ip, anomalies):
        if not TG: return
        try:
            lines = [f"   • {a['type']}: {a['detail']}" for a in anomalies]
            msg = (
                f"🍪 *Cookie Anomaly*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"IP: `{ip}`\n"
                f"Anomalies: `{len(anomalies)}`\n\n" +
                "\n".join(lines) +
                f"\n\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            )
            requests.post(
                f"https://api.telegram.org/bot{TG}/sendMessage",
                json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
        except: pass

    def status(self):
        uptime = int(time.time() - self.stats["started"])
        print(f"\n🍪 L23 Cookie Anomaly")
        print(f"═══════════════════════════════")
        print(f"Checked:     {self.stats['checked']}")
        print(f"Anomalies:   {self.stats['anomalies']}")
        print(f"Blocked:     {self.stats['blocked']}")
        print(f"Uptime:      {uptime // 3600}h {(uptime // 60) % 60}m")

    def test(self):
        print("🧪 Testing Cookie Anomaly\n")
        tests = [
            ("1.2.3.4", "session=abc123"),
            ("1.2.3.5", "session=<script>alert(1)</script>"),
            ("1.2.3.6", "user=' OR 1=1--"),
            ("1.2.3.7", "path=../../../etc/passwd"),
            ("1.2.3.8", "x" * 5000),
        ]
        for ip, cookie in tests:
            a = self.check_cookie(cookie, ip)
            icon = "🚨" if a else "✅"
            print(f"   {icon} {ip} → {len(a)} anomalies")
            for x in a:
                print(f"      • {x['type']}: {x['detail']}")
        print()
        self.status()


def main():
    if len(sys.argv) < 2:
        print("Usage: layer23_cookie_anomaly.py {test|status}")
        return
    cmd = sys.argv[1]
    ca = CookieAnomaly()
    if cmd == "test": ca.test()
    elif cmd == "status": ca.status()


if __name__ == "__main__":
    main()
