#!/usr/bin/env python3
"""L6 — GeoIP Blocking"""
import os, sys, json, time, threading
from datetime import datetime, timedelta
from collections import defaultdict

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
CONFIG_FILE = os.path.join(BASE, "geoip_config.json")
STATE_FILE = os.path.join(BASE, "layer06_state.json")

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
#   GEOIP CONFIG
# ═══════════════════════════════════════════════
DEFAULT_CONFIG = {
    "mode": "blocklist",   # "blocklist" | "allowlist" | "score"
    
    # حالت blocklist
    "blocked_countries": [
        "North Korea",
        "Syria", 
        "Sudan",
        "Belarus",
    ],
    
    # حالت allowlist (اگه mode=allowlist)
    "allowed_countries": [
        "Iran",
        "United States",
        "Germany",
        "Netherlands",
    ],
    
    # امتیازها (حالت score)
    "high_risk_score": 25,      # کشور پرخطر
    "medium_risk_score": 10,    # کشور متوسط
    "low_risk_score": 0,         # کشور امن
    
    # رفتار
    "auto_block": True,          # خودکار بلاک کن
    "notify": True,             # به تلگرام اطلاع بده
}

HIGH_RISK = ["North Korea", "Syria", "Sudan", "Belarus", "Russia", "Afghanistan"]
MEDIUM_RISK = ["China", "Vietnam", "Indonesia", "Brazil", "Pakistan"]
LOW_RISK = ["Iran", "Germany", "France", "United Kingdom", "Netherlands",
            "United States", "Canada", "Japan", "Australia", "Sweden"]

PRIVATE = ("127.", "10.", "192.168.", "172.")

class GeoIPBlock:
    def __init__(self):
        self.cfg = self.load_config()
        self.cache = {}  # ip → country
        self.ab = AutoBlock()
        self.lock = threading.Lock()
        self.stats = {
            "total": 0,
            "blocked_country": 0,
            "allowed_country": 0,
            "started": time.time(),
        }
        self.load_state()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE) as f:
                    cfg = json.load(f)
                    # merge با default
                    merged = dict(DEFAULT_CONFIG)
                    merged.update(cfg)
                    return merged
            except: pass
        # ساخت فایل
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)
        except: pass
        return dict(DEFAULT_CONFIG)

    def load_state(self):
        if os.path.exists(STATE_FILE):
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
                    "cache": dict(list(self.cache.items())[-1000:]),  # فقط ۱۰۰۰ آخر
                }, f, indent=2)
        except: pass

    def is_private(self, ip):
        return any(ip.startswith(p) for p in PRIVATE)

    def get_country(self, ip):
        """گرفتن کشور با cache"""
        if ip in self.cache:
            return self.cache[ip]
        
        try:
            r = requests.get(
                f"http://ip-api.com/json/{ip}?fields=status,country,countryCode",
                timeout=4
            ).json()
            if r.get("status") == "success":
                country = r.get("country", "?")
                self.cache[ip] = country
                return country
        except: pass
        return "?"

    def check(self, ip):
        """چک GeoIP"""
        if not ip or self.is_private(ip):
            return {"action": "allow", "reason": "private"}

        if self.ab.is_blocked(ip):
            return {"action": "block", "reason": "blacklisted"}

        with self.lock:
            self.stats["total"] += 1
            country = self.get_country(ip)

            # اعمال policy بر اساس mode
            mode = self.cfg.get("mode", "blocklist")

            if mode == "blocklist":
                if country in self.cfg.get("blocked_countries", []):
                    return self._block(ip, country, "blocklist")
                return {"action": "allow", "country": country}

            elif mode == "allowlist":
                if country not in self.cfg.get("allowed_countries", []):
                    return self._block(ip, country, "not_in_allowlist")
                return {"action": "allow", "country": country}

            elif mode == "score":
                score = 0
                if country in HIGH_RISK: score = self.cfg["high_risk_score"]
                elif country in MEDIUM_RISK: score = self.cfg["medium_risk_score"]
                else: score = self.cfg["low_risk_score"]

                if score >= 20:
                    return self._block(ip, country, f"geo_score_{score}")
                return {"action": "allow", "country": country, "score": score}

        return {"action": "allow", "country": country}

    def _block(self, ip, country, reason):
        """بلاک بر اساس کشور"""
        self.stats["blocked_country"] += 1
        
        if self.cfg.get("auto_block", True):
            self.ab.block(ip, f"geoip_{country}", score=60, ip_type="temp")

        if self.cfg.get("notify", True):
            self._alert(ip, country, reason)

        return {"action": "block", "country": country, "reason": reason}

    def _alert(self, ip, country, reason):
        if not TG: return
        try:
            msg = (
                f"🌍 *GeoIP Block*\n\n"
                f"IP: `{ip}`\n"
                f"Country: `{country}`\n"
                f"Reason: `{reason}`\n"
                f"Time: {datetime.now().strftime('%H:%M:%S')}"
            )
            requests.post(
                f"https://api.telegram.org/bot{TG}/sendMessage",
                json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
        except: pass

    def watch(self):
        qfile = os.path.join(BASE, "queue.jsonl")
        last_pos = 0

        print("🌍 L6 GeoIP Block Watcher")
        print(f"📊 Mode: {self.cfg.get('mode')}")
        print(f"🚫 Blocked countries: {', '.join(self.cfg.get('blocked_countries', []))}")
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
                            if r["action"] == "block":
                                print(f"🚫 {r['country']}: {ip}")
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
        print(f"\n🌍 L6 GeoIP Block Status")
        print(f"═══════════════════════════════")
        print(f"Mode:              {self.cfg.get('mode')}")
        print(f"Uptime:            {h}h {m}m")
        print(f"Total checked:     {self.stats['total']}")
        print(f"Blocked country:   {self.stats['blocked_country']}")
        print(f"Cached:            {len(self.cache)} IPs")
        print()
        print(f"🚫 Blocked Countries:")
        for c in self.cfg.get("blocked_countries", []):
            print(f"   • {c}")

    def test(self):
        """تست"""
        print("🧪 Testing GeoIP Block\n")

        test_ips = [
            ("8.8.8.8", "United States"),
            ("1.1.1.1", "Australia"),
            ("185.220.101.45", "Germany"),  # TOR
            ("5.9.0.1", "Germany"),
        ]

        for ip, expected in test_ips:
            r = self.check(ip)
            icon = "🚫" if r["action"] == "block" else "✅"
            print(f"{icon} {ip:<18} → {r.get('country', '?'):<20} {r['action']}")

        print()
        self.status()

def main():
    if len(sys.argv) < 2:
        print("Usage: layer06_geoip_block.py {watch|status|test}")
        return
    cmd = sys.argv[1]
    gb = GeoIPBlock()

    if cmd == "watch": gb.watch()
    elif cmd == "status": gb.status()
    elif cmd == "test": gb.test()

if __name__ == "__main__":
    main()
