#!/usr/bin/env python3
"""L2 — Threat Intelligence Engine"""
import os, sys, json, time, socket, requests, threading
from datetime import datetime, timedelta
from collections import defaultdict

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
CACHE_FILE = os.path.join(BASE, "layer02_cache.json")
TOR_FILE = os.path.join(BASE, "tor_exits.json")

# منابع Threat Intel
SOURCES = {
    "tor":     "https://check.torproject.org/torbulkexitlist",
    "abuseipdb_top": "https://raw.githubusercontent.com/stamparm/ipsum/master/levels/3.txt",
}

# IP های محلی
PRIVATE = ("127.", "10.", "192.168.", "172.16.", "172.17.", "172.18.",
           "172.19.", "172.20.", "172.21.", "172.22.", "172.23.",
           "172.24.", "172.25.", "172.26.", "172.27.", "172.28.",
           "172.29.", "172.30.", "172.31.", "169.254.")

# کشورهای پرخطر
HIGH_RISK = ["North Korea", "Syria", "Sudan", "Belarus", "Russia"]

# Whitelist — IPهای معروف امن
KNOWN_GOOD = {
    "8.8.8.8", "8.8.4.4",                       # Google DNS
    "1.1.1.1", "1.0.0.1",                       # Cloudflare DNS
    "9.9.9.9", "149.112.112.112",               # Quad9
    "208.67.222.222", "208.67.220.220",         # OpenDNS
    "140.82.121.3", "140.82.121.4",             # GitHub
    "142.250.185.78",                            # Google
}

# ISP های مشکوک
SUSPICIOUS_ISP = ["vpn", "proxy", "tor", "hosting", "cloud", "datacenter"]

class ThreatIntel:
    def __init__(self):
        self.cache = self._load_json(CACHE_FILE)
        tor_data = self._load_json(TOR_FILE)
        self.tor_list = set(tor_data.get("ips", []))
        self.last_update = tor_data.get("updated", 0)
        self.bad_ips = set()
        self.lock = threading.Lock()
        # فقط اگه ۶ ساعت گذشته باشه
        if time.time() - self.last_update > 21600:
            self._update_feeds()

    def _load_json(self, path):
        try:
            with open(path) as f:
                return json.load(f)
        except:
            return {}

    def _save_json(self, path, data):
        try:
            with open(path, "w") as f:
                json.dump(data, f)
        except: pass

    def _update_feeds(self):
        """به‌روزرسانی لیست‌های تهدید"""
        if time.time() - self.last_update < 21600:  # ۶ ساعت
            return

        # Tor Exit Nodes
        try:
            r = requests.get(SOURCES["tor"], timeout=15)
            if r.status_code == 200:
                ips = set(r.text.strip().split("\n"))
                self.tor_list = ips
                self._save_json(TOR_FILE, {"ips": list(ips), "updated": time.time()})
                print(f"[+] Tor list: {len(ips)} nodes")
        except Exception as e:
            print(f"[!] Tor update failed: {e}")

        # Bad IPs (IPSum Level 3+)
        try:
            r = requests.get(SOURCES["abuseipdb_top"], timeout=15)
            if r.status_code == 200:
                self.bad_ips = set(r.text.strip().split("\n"))
                print(f"[+] Bad IPs: {len(self.bad_ips)}")
        except Exception as e:
            print(f"[!] Bad IPs failed: {e}")

        self.last_update = time.time()

    def is_private(self, ip):
        return any(ip.startswith(p) for p in PRIVATE)

    def check(self, ip):
        """چک کامل یک IP"""
        if not ip or self.is_private(ip):
            return {"score": 0, "flags": ["PRIVATE"], "country": "Local"}

        # Whitelist known good IPs
        if ip in KNOWN_GOOD:
            return {"score": 0, "flags": ["WHITELISTED"], "country": "Known-Good",
                    "city": "-", "isp": "-", "cached_at": datetime.now().isoformat()}

        # Cache (۲۴ ساعت)
        if ip in self.cache:
            cached = self.cache[ip]
            try:
                ts = datetime.fromisoformat(cached.get("cached_at", "2000-01-01"))
                if datetime.now() - ts < timedelta(hours=24):
                    return cached
            except: pass

        result = {
            "ip": ip,
            "score": 0,
            "flags": [],
            "country": "?",
            "city": "?",
            "isp": "?",
            "cached_at": datetime.now().isoformat(),
        }

        # ۱. Tor?
        if ip in self.tor_list:
            result["flags"].append("TOR_EXIT")
            result["score"] += 45

        # ۲. لیست سیاه؟
        if ip in self.bad_ips:
            result["flags"].append("BADLIST")
            result["score"] += 40

        # ۳. GeoIP + Proxy/Hosting
        try:
            r = requests.get(
                f"http://ip-api.com/json/{ip}?fields=status,country,city,isp,proxy,hosting,mobile",
                timeout=4
            ).json()
            if r.get("status") == "success":
                result["country"] = r.get("country", "?")
                result["city"] = r.get("city", "?")
                result["isp"] = r.get("isp", "?")

                if r.get("proxy"):
                    result["flags"].append("PROXY")
                    result["score"] += 30
                if r.get("hosting"):
                    result["flags"].append("HOSTING")
                    result["score"] += 15
        except: pass

        # ۴. کشور پرخطر؟
        if result["country"] in HIGH_RISK:
            result["flags"].append("HIGH_RISK_GEO")
            result["score"] += 20

        # ۵. ISP مشکوک؟
        isp_low = result["isp"].lower()
        if any(s in isp_low for s in SUSPICIOUS_ISP):
            result["flags"].append("SUSPICIOUS_ISP")
            result["score"] += 15

        result["score"] = min(100, result["score"])
        self.cache[ip] = result
        self._save_json(CACHE_FILE, self.cache)
        return result

    def verdict(self, ip):
        """تصمیم نهایی: ALLOW / SUSPICIOUS / BLOCK"""
        r = self.check(ip)
        s = r.get("score", 0)
        if s >= 70: return "BLOCK"
        if s >= 40: return "SUSPICIOUS"
        return "ALLOW"

# Singleton
INTEL = ThreatIntel()

def main():
    if len(sys.argv) < 2:
        print("Usage: layer02_threat_intel.py {check <ip>|update|test}")
        return
    cmd = sys.argv[1]
    if cmd == "check" and len(sys.argv) > 2:
        ip = sys.argv[2]
        r = INTEL.check(ip)
        v = INTEL.verdict(ip)
        print(f"\n🔍 {ip}")
        print(f"   Verdict: {v}")
        print(f"   Score:   {r['score']}/100")
        print(f"   Country: {r['country']}")
        print(f"   ISP:     {r['isp']}")
        print(f"   Flags:   {', '.join(r['flags']) or 'none'}")
    elif cmd == "test":
        for ip in ["8.8.8.8", "1.1.1.1", "45.33.32.156", "185.220.101.45"]:
            r = INTEL.check(ip)
            print(f"{ip:<18} score={r['score']:>3} {r['country']:<20} {','.join(r['flags'])}")
    elif cmd == "update":
        INTEL.last_update = 0
        INTEL._update_feeds()

if __name__ == "__main__":
    main()

