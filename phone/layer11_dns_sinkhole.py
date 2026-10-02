#!/usr/bin/env python3
"""L11 — DNS Sinkhole"""
import os, sys, json, time, requests, threading
from datetime import datetime
from collections import defaultdict

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
HOSTS_FILE = "/etc/hosts"
STATE_FILE = os.path.join(BASE, "layer11_state.json")
BLOCKED_FILE = os.path.join(BASE, "layer11_blocked.txt")

try:
    with open(os.path.join(HOME, "vorix/.tg-token")) as f:
        TG = f.read().strip()
except:
    TG = ""
CHAT = "175160049"

# منابع لیست سیاه
SOURCES = {
    "StevenBlack": "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
    "AdAway": "https://adaway.org/hosts.txt",
}

# دامنه‌های داخلی
SAFE_DOMAINS = [
    "localhost", "127.0.0.1",
    "telegram.org", "t.me", "github.com", "githubusercontent.com",
    "google.com", "googleapis.com", "cloudflare.com",
]

class DNSSinkhole:
    def __init__(self):
        self.blocked = self.load_blocked()
        self.stats = {"loaded": 0, "blocked_count": 0, "started": time.time()}
        self.load_state()

    def load_blocked(self):
        try:
            with open(BLOCKED_FILE) as f:
                return set(l.strip() for l in f if l.strip() and not l.startswith("#"))
        except:
            return set()

    def save_blocked(self):
        try:
            with open(BLOCKED_FILE, "w") as f:
                f.write("# VORIX DNS Sinkhole\n")
                f.write(f"# Total: {len(self.blocked)}\n\n")
                for d in sorted(self.blocked):
                    f.write(d + "\n")
        except: pass

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

    def download_blacklists(self):
        """دانلود لیست‌های سیاه"""
        print("📥 Downloading blacklists...")
        total = 0
        for name, url in SOURCES.items():
            try:
                r = requests.get(url, timeout=30)
                if r.status_code != 200: continue
                count = 0
                for line in r.text.split("\n"):
                    line = line.strip()
                    if not line or line.startswith("#"): continue
                    parts = line.split()
                    if len(parts) >= 2:
                        domain = parts[1].lower()
                        if domain and domain not in SAFE_DOMAINS:
                            if domain not in ("localhost", "broadcasthost", "0.0.0.0", "127.0.0.1"):
                                self.blocked.add(domain)
                                count += 1
                print(f"   ✅ {name}: {count} domains")
                total += count
            except Exception as e:
                print(f"   ⚠️ {name}: {e}")
        
        self.stats["loaded"] = total
        self.save_blocked()
        self.save_state()
        print(f"\n📊 Total domains: {len(self.blocked)}")

    def is_blocked(self, domain):
        """چک بلاک بودن دامنه"""
        domain = domain.lower().strip()
        if domain in self.blocked:
            return True
        # چک subdomain
        parts = domain.split(".")
        for i in range(len(parts)):
            sub = ".".join(parts[i:])
            if sub in self.blocked:
                return True
        return False

    def check_query(self, domain, ip=None):
        """چک یک کوئری"""
        if self.is_blocked(domain):
            self.stats["blocked_count"] += 1
            self._alert(domain, ip)
            return True
        return False

    def _alert(self, domain, ip):
        if not TG: return
        try:
            msg = (
                f"🚫 *DNS Sinkhole*\n\n"
                f"Domain: `{domain}`\n"
                f"IP: `{ip or '?'}`\n"
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
        print(f"\n🚫 L11 DNS Sinkhole")
        print(f"═══════════════════════════════")
        print(f"Blocked domains:  {len(self.blocked):,}")
        print(f"Queries blocked:  {self.stats['blocked_count']}")
        print(f"Uptime:           {uptime // 3600}h {(uptime // 60) % 60}m")

    def test(self, domain="malware-c2.example.com"):
        """تست"""
        print(f"🧪 Testing DNS Sinkhole")
        # اضافه یک دامنه تستی
        self.blocked.add("malware-c2.example.com")
        self.blocked.add("ads.doubleclick.net")
        
        tests = [
            ("google.com", False),
            ("malware-c2.example.com", True),
            ("ads.doubleclick.net", True),
            ("sub.ads.doubleclick.net", True),
            ("github.com", False),
        ]
        
        for d, expected in tests:
            result = self.is_blocked(d)
            icon = "🚫" if result else "✅"
            status = "OK" if result == expected else "WRONG"
            print(f"   {icon} {d:<35} → {status}")
        
        self.status()


def main():
    if len(sys.argv) < 2:
        print("Usage: layer11_dns_sinkhole.py {load|status|test|check <domain>}")
        return
    cmd = sys.argv[1]
    ds = DNSSinkhole()

    if cmd == "load": ds.download_blacklists()
    elif cmd == "status": ds.status()
    elif cmd == "test": ds.test()
    elif cmd == "check" and len(sys.argv) > 2:
        print(ds.is_blocked(sys.argv[2]))


if __name__ == "__main__":
    main()
