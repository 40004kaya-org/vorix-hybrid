#!/usr/bin/env python3
"""L15 — Client Fingerprinting (Advanced)"""
import os, sys, json, time, re, threading
from datetime import datetime
from collections import defaultdict, Counter

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
STATE_FILE = os.path.join(BASE, "layer15_state.json")

sys.path.insert(0, BASE)
from layer04_auto_block import AutoBlock

try:
    import requests
    with open(os.path.join(HOME, "vorix/.tg-token")) as f:
        TG = f.read().strip()
except:
    TG = ""
CHAT = "175160049"

# ═══════════════════════════════════════════════
#   FINGERPRINT SIGNATURES
# ═══════════════════════════════════════════════
TOOL_SIGNATURES = {
    # Security scanners
    "nmap": ["nmap", "nmap scripting engine", "nse"],
    "masscan": ["masscan"],
    "sqlmap": ["sqlmap"],
    "nikto": ["nikto"],
    "nuclei": ["nuclei"],
    "acunetix": ["acunetix"],
    "nessus": ["nessus", "tenable"],
    "openvas": ["openvas"],
    "burp": ["burp", "portswigger"],
    "zap": ["zaproxy", "owasp zap"],
    "wpscan": ["wpscan"],
    "dirb": ["dirb"],
    "gobuster": ["gobuster"],
    "ffuf": ["ffuf"],
    "hydra": ["hydra"],
    "metasploit": ["metasploit"],
    
    # Programming clients
    "python-requests": ["python-requests", "python/", "pyrequests"],
    "python-urllib": ["python-urllib"],
    "curl": ["curl/", "libcurl"],
    "wget": ["wget/", "gnu wget"],
    "go-http": ["go-http-client", "golang"],
    "rust-reqwest": ["reqwest"],
    "node-fetch": ["node-fetch", "axios"],
    "java": ["java/", "okhttp", "apache-httpclient"],
    
    # Cloud scanners
    "shodan": ["shodan"],
    "censys": ["censys"],
    "palo-alto": ["palo alto"],
    
    # Bots
    "googlebot": ["googlebot"],
    "bingbot": ["bingbot"],
    "semrush": ["semrush"],
    "ahrefs": ["ahrefs"],
    "yandex": ["yandex"],
    
    # Suspicious
    "gobuster": ["gobuster"],
    "custom-scanner": ["scanner", "scan/", "exploit", "attack"],
}

SUSPICIOUS_TOOLS = ["nmap", "masscan", "sqlmap", "nikto", "nuclei",
                    "acunetix", "nessus", "openvas", "hydra",
                    "metasploit", "custom-scanner", "dirb",
                    "gobuster", "ffuf", "wpscan"]

GOOD_BOTS = ["googlebot", "bingbot", "yandex", "semrush", "ahrefs"]


class Fingerprint:
    def __init__(self):
        self.tool_hits = defaultdict(Counter)  # ip → Counter of tools
        self.stats = {"total": 0, "detected": 0, "blocked": 0, "started": time.time()}
        self.lock = threading.Lock()
        self.ab = AutoBlock()
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

    def detect_tool(self, ua, headers=None):
        """تشخیص ابزار از User-Agent"""
        if not ua:
            return None
        ua_lower = ua.lower()

        for tool, sigs in TOOL_SIGNATURES.items():
            for sig in sigs:
                if sig in ua_lower:
                    return tool
        return None

    def process(self, ip, ua, headers=None):
        """پردازش یک درخواست"""
        if not ip or not ua:
            return

        with self.lock:
            self.stats["total"] += 1
            tool = self.detect_tool(ua)
            
            if not tool:
                return

            self.tool_hits[ip][tool] += 1
            self.stats["detected"] += 1

            # اگه ابزار مشکوک بود
            if tool in SUSPICIOUS_TOOLS:
                count = self.tool_hits[ip][tool]
                self._alert(ip, tool, ua, count, "SUSPICIOUS")
                
                # بلاک بعد از ۳ بار
                if count >= 3:
                    self.ab.block(ip, f"tool_{tool}_{count}", score=85, ip_type="temp")
                    self.stats["blocked"] += 1
            
            elif tool in GOOD_BOTS:
                # ربات‌های معتبر — فقط لاگ
                pass

    def _alert(self, ip, tool, ua, count, level):
        if not TG: return
        try:
            icon = "🤖" if level == "SUSPICIOUS" else "ℹ️"
            msg = (
                f"{icon} *Tool Detected*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Tool: `{tool}`\n"
                f"IP: `{ip}`\n"
                f"Count: `{count}`\n"
                f"UA: `{ua[:60]}`\n"
                f"Time: {datetime.now().strftime('%H:%M:%S')}"
            )
            requests.post(
                f"https://api.telegram.org/bot{TG}/sendMessage",
                json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
        except: pass

    def status(self):
        uptime = int(time.time() - self.stats["started"])
        print(f"\n🖐️  L15 Fingerprint")
        print(f"═══════════════════════════════")
        print(f"Total:       {self.stats['total']}")
        print(f"Detected:    {self.stats['detected']}")
        print(f"Blocked:     {self.stats['blocked']}")
        print(f"Uptime:      {uptime // 3600}h {(uptime // 60) % 60}m")
        print()
        
        if self.tool_hits:
            print(f"📊 Detected Tools:")
            tool_counter = Counter()
            for ip, tools in self.tool_hits.items():
                for t, c in tools.items():
                    tool_counter[t] += c
            for t, c in tool_counter.most_common(10):
                icon = "⚠️" if t in SUSPICIOUS_TOOLS else "✅"
                print(f"   {icon} {t:<20} {c}")

    def test(self):
        print("🧪 Testing Fingerprint\n")
        
        test_cases = [
            ("1.2.3.4", "Mozilla/5.0 (compatible; Nmap Scripting Engine)", "nmap"),
            ("1.2.3.5", "sqlmap/1.7#stable (http://sqlmap.org)", "sqlmap"),
            ("1.2.3.6", "python-requests/2.31.0", "python-requests"),
            ("1.2.3.7", "Mozilla/5.0 (compatible; Googlebot/2.1)", "googlebot"),
            ("1.2.3.8", "curl/8.0.1", "curl"),
            ("1.2.3.9", "Nikto/2.5.0", "nikto"),
        ]
        
        for ip, ua, expected in test_cases:
            tool = self.detect_tool(ua)
            icon = "⚠️" if tool in SUSPICIOUS_TOOLS else "✅"
            status = "OK" if tool == expected else f"GOT {tool}"
            print(f"   {icon} {expected:<20} → {status}")
        
        print()
        self.status()


def main():
    if len(sys.argv) < 2:
        print("Usage: layer15_fingerprint.py {test|status}")
        return
    cmd = sys.argv[1]
    fp = Fingerprint()

    if cmd == "test": fp.test()
    elif cmd == "status": fp.status()


if __name__ == "__main__":
    main()
