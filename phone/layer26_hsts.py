#!/usr/bin/env python3
"""L26 — HSTS Enforcement"""
import os, sys, json, time, ssl, socket, threading
from datetime import datetime
from collections import defaultdict

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
STATE_FILE = os.path.join(BASE, "layer26_state.json")

try:
    import requests
    with open(os.path.join(HOME, "vorix/.tg-token")) as f:
        TG = f.read().strip()
except:
    TG = ""
CHAT = "175160049"

# دامنه‌هایی که HSTS باید داشته باشن
DOMAINS_TO_CHECK = [
    "github.com",
    "google.com",
    "cloudflare.com",
    "telegram.org",
]


class HSTSEnforce:
    def __init__(self):
        self.results = {}
        self.stats = {"checked": 0, "missing_hsts": 0, "weak_hsts": 0, "started": time.time()}
        self.load_state()

    def load_state(self):
        try:
            with open(STATE_FILE) as f:
                s = json.load(f)
                self.stats = s.get("stats", self.stats)
                self.results = s.get("results", {})
        except: pass

    def save_state(self):
        try:
            with open(STATE_FILE, "w") as f:
                json.dump({"stats": self.stats, "results": self.results}, f, indent=2)
        except: pass

    def check_hsts(self, domain):
        """چک HSTS header"""
        try:
            r = requests.head(f"https://{domain}", timeout=10, allow_redirects=True)
            hsts = r.headers.get("Strict-Transport-Security", "")
            return {
                "domain": domain,
                "hsts": hsts,
                "has_hsts": bool(hsts),
                "max_age": self._extract_max_age(hsts),
                "include_subdomains": "includesubdomains" in hsts.lower(),
                "preload": "preload" in hsts.lower(),
            }
        except Exception as e:
            return {"domain": domain, "error": str(e)}

    def _extract_max_age(self, hsts):
        if not hsts:
            return 0
        for part in hsts.split(";"):
            part = part.strip()
            if part.startswith("max-age="):
                try:
                    return int(part.split("=")[1])
                except:
                    return 0
        return 0

    def check_all(self):
        print("🔒 HSTS Enforcement")
        print(f"📊 Domains: {len(DOMAINS_TO_CHECK)}\n")

        for domain in DOMAINS_TO_CHECK:
            print(f"🔍 {domain}...")
            result = self.check_hsts(domain)
            self.results[domain] = result
            self.stats["checked"] += 1

            if "error" in result:
                print(f"   ❌ Error: {result['error'][:50]}")
                continue

            if not result["has_hsts"]:
                self.stats["missing_hsts"] += 1
                print(f"   🟡 No HSTS header")
                self._alert(domain, "MISSING")
            elif result["max_age"] < 31536000:  # less than 1 year
                self.stats["weak_hsts"] += 1
                print(f"   🟡 Weak HSTS: max-age={result['max_age']}")
                self._alert(domain, "WEAK", result["max_age"])
            else:
                extras = []
                if result["include_subdomains"]: extras.append("subdomains")
                if result["preload"]: extras.append("preload")
                print(f"   ✅ Strong HSTS: max-age={result['max_age']} ({', '.join(extras) or 'basic'})")

        self.save_state()

    def _alert(self, domain, level, max_age=0):
        if not TG: return
        try:
            icon = "🟡"
            msg = (
                f"{icon} *HSTS Alert*\n\n"
                f"Domain: `{domain}`\n"
                f"Issue: {level} (max-age: {max_age})\n"
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
        print(f"\n🔒 L26 HSTS Enforcement")
        print(f"═══════════════════════════════")
        print(f"Checked:        {self.stats['checked']}")
        print(f"Missing HSTS:   {self.stats['missing_hsts']}")
        print(f"Weak HSTS:      {self.stats['weak_hsts']}")
        print(f"Uptime:         {uptime // 3600}h {(uptime // 60) % 60}m")
        print()
        if self.results:
            print(f"📊 Domains:")
            for d, r in self.results.items():
                if "error" in r:
                    print(f"   ❌ {d}: error")
                elif r["has_hsts"]:
                    print(f"   ✅ {d}: max-age={r['max_age']}")
                else:
                    print(f"   🟡 {d}: no HSTS")

    def test(self):
        print("🧪 Testing HSTS Enforce\n")
        self.check_all()
        print()
        self.status()


def main():
    if len(sys.argv) < 2:
        print("Usage: layer26_hsts.py {check|status|test}")
        return
    cmd = sys.argv[1]
    he = HSTSEnforce()
    if cmd == "check": he.check_all()
    elif cmd == "status": he.status()
    elif cmd == "test": he.test()


if __name__ == "__main__":
    main()
