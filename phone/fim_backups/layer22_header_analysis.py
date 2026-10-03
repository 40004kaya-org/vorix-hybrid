#!/usr/bin/env python3
"""L22 — HTTP Header Analysis"""
import os, sys, json, time, re, threading
from datetime import datetime
from collections import defaultdict

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
STATE_FILE = os.path.join(BASE, "layer22_state.json")

sys.path.insert(0, BASE)
from layer04_auto_block import AutoBlock

try:
    import requests
    with open(os.path.join(HOME, "vorix/.tg-token")) as f:
        TG = f.read().strip()
except:
    TG = ""
CHAT = "175160049"

# الگوهای حمله در هدرها
ATTACK_PATTERNS = {
    "SQL_INJECTION": [
        r"'\s*or\s+'?\d+'?\s*=\s*'?\d+",
        r"union\s+select",
        r"'\s*;\s*drop\s+table",
        r"--\s*$",
        r"/\*.*\*/",
    ],
    "XSS": [
        r"<script[^>]*>",
        r"javascript:",
        r"onerror\s*=",
        r"onload\s*=",
        r"<iframe[^>]*>",
        r"<img[^>]*src\s*=",
        r"eval\s*\(",
    ],
    "PATH_TRAVERSAL": [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"/etc/passwd",
        r"c:\\windows",
    ],
    "COMMAND_INJECTION": [
        r";\s*cat\s+",
        r"\|\s*ls\s+",
        r"&&\s*whoami",
        r"`[^`]+`",
        r"\$\([^)]+\)",
    ],
    "LFI_RFI": [
        r"php://",
        r"file://",
        r"data://",
        r"expect://",
        r"http://.*\.php",
    ],
    "SSRF": [
        r"localhost",
        r"127\.0\.0\.1",
        r"169\.254\.169\.254",
        r"metadata\.",
    ],
}

# هدرهای مشکوک
SUSPICIOUS_HEADERS = [
    "x-forwarded-for",
    "x-originating-ip",
    "x-remote-ip",
    "x-remote-addr",
    "x-client-ip",
    "x-real-ip",
    "x-forwarded-host",
    "x-rewrite-url",
]

USER_AGENT_PATTERNS = [
    (r"sqlmap", "SQLMAP"),
    (r"nmap", "NMAP"),
    (r"nikto", "NIKTO"),
    (r"masscan", "MASSCAN"),
    (r"nuclei", "NUCLEI"),
    (r"dirb", "DIRB"),
    (r"gobuster", "GOBUSTER"),
    (r"ffuf", "FFUF"),
]


class HeaderAnalysis:
    def __init__(self):
        self.detections = defaultdict(int)
        self.ab = AutoBlock()
        self.lock = threading.Lock()
        self.stats = {"analyzed": 0, "attacks": 0, "blocked": 0, "started": time.time()}
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

    def analyze_headers(self, headers, ip):
        """تحلیل هدرها"""
        with self.lock:
            self.stats["analyzed"] += 1
            attacks_found = []

            # تبدیل به رشته
            combined = json.dumps(headers).lower()
            ua = str(headers.get("User-Agent", headers.get("user-agent", "")))

            # چک UA
            for pattern, tool in USER_AGENT_PATTERNS:
                if re.search(pattern, ua, re.IGNORECASE):
                    attacks_found.append(("TOOL_DETECTED", tool))
                    self.detections[f"tool_{tool}"] += 1

            # چک الگوهای حمله
            for attack_type, patterns in ATTACK_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, combined, re.IGNORECASE):
                        attacks_found.append((attack_type, pattern[:30]))
                        self.detections[attack_type] += 1
                        break

            # چک هدرهای مشکوک
            for h in SUSPICIOUS_HEADERS:
                if h in combined:
                    attacks_found.append(("SUSPICIOUS_HEADER", h))
                    self.detections[f"header_{h}"] += 1

            if attacks_found:
                self.stats["attacks"] += len(attacks_found)
                # بلاک اگه حمله جدی بود
                for atype, detail in attacks_found:
                    if atype in ("SQL_INJECTION", "COMMAND_INJECTION", "LFI_RFI", "SSRF"):
                        self.ab.block(ip, f"header_{atype.lower()}", score=90, ip_type="perm")
                        self.stats["blocked"] += 1
                        break
                
                self._alert(ip, attacks_found)

            return attacks_found

    def _alert(self, ip, attacks):
        if not TG: return
        try:
            lines = [f"   • `{a[0]}`: {a[1]}" for a in attacks[:5]]
            msg = (
                f"📋 *Header Attack Detected*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"IP: `{ip}`\n"
                f"Attacks: `{len(attacks)}`\n\n"
                f"📊 Details:\n" + "\n".join(lines) +
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
        print(f"\n📋 L22 HTTP Header Analysis")
        print(f"═══════════════════════════════")
        print(f"Analyzed:     {self.stats['analyzed']}")
        print(f"Attacks:      {self.stats['attacks']}")
        print(f"Blocked:      {self.stats['blocked']}")
        print(f"Uptime:       {uptime // 3600}h {(uptime // 60) % 60}m")
        print()
        if self.detections:
            print(f"📊 Top Detections:")
            for k, v in sorted(self.detections.items(), key=lambda x: -x[1])[:10]:
                print(f"   • {k}: {v}")

    def test(self):
        print("🧪 Testing Header Analysis\n")
        tests = [
            ("1.2.3.4", {"User-Agent": "sqlmap/1.7", "X-Forwarded-For": "1.2.3.4"}),
            ("1.2.3.5", {"User-Agent": "Mozilla/5.0", "Referer": "http://x.com/?id=' OR 1=1--"}),
            ("1.2.3.6", {"User-Agent": "Mozilla/5.0", "X-Custom": "<script>alert(1)</script>"}),
            ("1.2.3.7", {"User-Agent": "curl/8.0", "Path": "../../etc/passwd"}),
            ("1.2.3.8", {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1)"}),
        ]
        for ip, h in tests:
            attacks = self.analyze_headers(h, ip)
            icon = "🚨" if attacks else "✅"
            print(f"   {icon} {ip} → {len(attacks)} attacks")
            for a in attacks:
                print(f"      • {a[0]}: {a[1]}")
        print()
        self.status()


def main():
    if len(sys.argv) < 2:
        print("Usage: layer22_header_analysis.py {test|status}")
        return
    cmd = sys.argv[1]
    ha = HeaderAnalysis()
    if cmd == "test": ha.test()
    elif cmd == "status": ha.status()


if __name__ == "__main__":
    main()
