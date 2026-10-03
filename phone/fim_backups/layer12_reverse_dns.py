#!/usr/bin/env python3
"""L12 — Reverse DNS Lookup"""
import os, sys, json, time, socket, threading
from datetime import datetime
from collections import defaultdict

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
STATE_FILE = os.path.join(BASE, "layer12_state.json")

try:
    import requests
    with open(os.path.join(HOME, "vorix/.tg-token")) as f:
        TG = f.read().strip()
except:
    TG = ""
CHAT = "175160049"

CONFIG = {
    "cache_hours": 24,
    "notify_suspicious": True,
}

# کلمات کلیدی مشکوک در hostname
SUSPICIOUS_KEYWORDS = [
    "vpn", "proxy", "tor", "scan", "bot", "crawler",
    "spam", "malware", "c2", "attack", "hack",
    "exploit", "shell", "backdoor",
]

PRIVATE = ("127.", "10.", "192.168.", "172.")


class ReverseDNS:
    def __init__(self):
        self.cache = {}
        self.stats = {"lookups": 0, "suspicious": 0, "no_ptr": 0, "started": time.time()}
        self.load_state()

    def load_state(self):
        try:
            with open(STATE_FILE) as f:
                s = json.load(f)
                self.stats = s.get("stats", self.stats)
                self.cache = s.get("cache", {})
        except: pass

    def save_state(self):
        try:
            with open(STATE_FILE, "w") as f:
                json.dump({
                    "stats": self.stats,
                    "cache": dict(list(self.cache.items())[-500:]),
                }, f, indent=2)
        except: pass

    def is_private(self, ip):
        return any(ip.startswith(p) for p in PRIVATE)

    def lookup(self, ip):
        """جستجوی PTR record"""
        if not ip or self.is_private(ip):
            return None

        # Cache
        if ip in self.cache:
            cached = self.cache[ip]
            ts = cached.get("ts", 0)
            if time.time() - ts < CONFIG["cache_hours"] * 3600:
                return cached.get("hostname")

        self.stats["lookups"] += 1

        try:
            hostname = socket.gethostbyaddr(ip)[0]
            self.cache[ip] = {"hostname": hostname, "ts": time.time()}
            self.save_state()
            return hostname
        except socket.herror:
            self.cache[ip] = {"hostname": None, "ts": time.time()}
            self.stats["no_ptr"] += 1
            self.save_state()
            return None
        except:
            return None

    def is_suspicious_hostname(self, hostname):
        """آیا hostname مشکوکه؟"""
        if not hostname:
            return False, []
        
        hostname_lower = hostname.lower()
        found = []
        for kw in SUSPICIOUS_KEYWORDS:
            if kw in hostname_lower:
                found.append(kw)
        return len(found) > 0, found

    def check(self, ip):
        """چک کامل"""
        if self.is_private(ip):
            return {"ip": ip, "hostname": "private", "suspicious": False}

        hostname = self.lookup(ip)
        is_suspicious, keywords = self.is_suspicious_hostname(hostname)

        if is_suspicious:
            self.stats["suspicious"] += 1
            self._alert(ip, hostname, keywords)

        return {
            "ip": ip,
            "hostname": hostname or "no-ptr",
            "suspicious": is_suspicious,
            "keywords": keywords,
        }

    def _alert(self, ip, hostname, keywords):
        if not CONFIG["notify_suspicious"] or not TG:
            return
        try:
            msg = (
                f"🔎 *Reverse DNS — Suspicious*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"IP: `{ip}`\n"
                f"Hostname: `{hostname}`\n"
                f"Keywords: `{', '.join(keywords)}`\n"
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
        print(f"\n🔎 L12 Reverse DNS")
        print(f"═══════════════════════════════")
        print(f"Lookups:      {self.stats['lookups']}")
        print(f"Suspicious:   {self.stats['suspicious']}")
        print(f"No PTR:       {self.stats['no_ptr']}")
        print(f"Cached:       {len(self.cache)}")
        print(f"Uptime:       {uptime // 3600}h {(uptime // 60) % 60}m")

    def test(self):
        print("🧪 Testing Reverse DNS\n")
        test_ips = [
            "8.8.8.8",
            "1.1.1.1",
            "45.33.32.156",
        ]
        for ip in test_ips:
            r = self.check(ip)
            icon = "⚠️" if r["suspicious"] else "✅"
            print(f"   {icon} {ip:<18} → {r['hostname']}")
        print()
        self.status()


def main():
    if len(sys.argv) < 2:
        print("Usage: layer12_reverse_dns.py {check <ip>|status|test}")
        return
    cmd = sys.argv[1]
    rd = ReverseDNS()
    if cmd == "check" and len(sys.argv) > 2:
        print(json.dumps(rd.check(sys.argv[2]), indent=2))
    elif cmd == "status": rd.status()
    elif cmd == "test": rd.test()


if __name__ == "__main__":
    main()
