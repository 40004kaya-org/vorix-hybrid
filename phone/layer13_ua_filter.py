#!/usr/bin/env python3
"""L13 — User-Agent Filter"""
import os, sys, json, time, re, threading
from datetime import datetime
from collections import defaultdict

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
STATE_FILE = os.path.join(BASE, "layer13_state.json")

sys.path.insert(0, BASE)
from layer04_auto_block import AutoBlock

try:
    import requests
    with open(os.path.join(HOME, "vorix/.tg-token")) as f:
        TG = f.read().strip()
except:
    TG = ""
CHAT = "175160049"

# Bad UA patterns
BAD_UA_PATTERNS = {
    "nmap": r"nmap",
    "sqlmap": r"sqlmap",
    "nikto": r"nikto",
    "masscan": r"masscan",
    "nuclei": r"nuclei",
    "acunetix": r"acunetix",
    "nessus": r"nessus",
    "openvas": r"openvas",
    "dirbuster": r"dirbuster",
    "gobuster": r"gobuster",
    "dirb": r"dirb",
    "wpscan": r"wpscan",
    "hydra": r"hydra",
    "metasploit": r"metasploit",
    "zap": r"zaproxy|owasp.zap",
    "burp": r"burp",
    "python-requests": r"python-requests",
    "python-urllib": r"python-urllib",
    "curl": r"curl",
    "wget": r"wget",
    "go-http": r"go-http-client",
    "java": r"java/|okhttp|apache-httpclient",
    "ruby": r"ruby",
    "perl": r"libwww-perl",
    "php": r"php/",
    "empty": r"^$",
    "short": r"^.{1,5}$",
}

WHITELIST_UA = [
    "googlebot", "bingbot", "yandex", "duckduckbot",
    "facebookexternalhit", "twitterbot", "linkedinbot",
    "applebot", "semrushbot", "ahrefsbot",
]


class UAFilter:
    def __init__(self):
        self.detections = defaultdict(int)
        self.ab = AutoBlock()
        self.lock = threading.Lock()
        self.stats = {"checked": 0, "bad": 0, "blocked": 0, "started": time.time()}
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

    def check(self, ua, ip=None):
        """چک یک UA"""
        if not ua:
            return None

        with self.lock:
            self.stats["checked"] += 1
            ua_lower = ua.lower()

            # Whitelist
            for good in WHITELIST_UA:
                if good in ua_lower:
                    return None

            # چک الگوهای بد
            for tool, pattern in BAD_UA_PATTERNS.items():
                if re.search(pattern, ua_lower, re.IGNORECASE):
                    self.stats["bad"] += 1
                    self.detections[tool] += 1
                    self.save_state()

                    if ip:
                        self.ab.block(ip, f"ua_{tool}", score=70, ip_type="temp")
                        self.stats["blocked"] += 1
                        self._alert(ip, tool, ua)

                    return tool
        return None

    def _alert(self, ip, tool, ua):
        if not TG: return
        try:
            msg = (
                f"🖐️ *UA Filter*\n\n"
                f"Tool: `{tool}`\n"
                f"IP: `{ip}`\n"
                f"UA: `{ua[:60]}`\n"
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
        print(f"\n🖐️  L13 User-Agent Filter")
        print(f"═══════════════════════════════")
        print(f"Checked:     {self.stats['checked']}")
        print(f"Bad UA:      {self.stats['bad']}")
        print(f"Blocked:     {self.stats['blocked']}")
        print(f"Uptime:      {uptime // 3600}h {(uptime // 60) % 60}m")
        if self.detections:
            print(f"\n🎯 Detected:")
            for t, c in sorted(self.detections.items(), key=lambda x: -x[1])[:10]:
                print(f"   • {t}: {c}")

    def test(self):
        print("🧪 Testing UA Filter\n")
        tests = [
            "Mozilla/5.0 (Windows NT 10.0)",
            "sqlmap/1.7",
            "nmap scripting engine",
            "curl/8.0",
            "Googlebot/2.1",
            "python-requests/2.31",
            "",
        ]
        for ua in tests:
            result = self.check(ua, "1.2.3.4")
            icon = "🚫" if result else "✅"
            print(f"   {icon} '{ua[:40]}' → {result or 'allowed'}")
        print()
        self.status()


def main():
    if len(sys.argv) < 2:
        print("Usage: layer13_ua_filter.py {test|status}")
        return
    cmd = sys.argv[1]
    uf = UAFilter()
    if cmd == "test": uf.test()
    elif cmd == "status": uf.status()

if __name__ == "__main__":
    main()
