#!/usr/bin/env python3
"""L25 — SSL/TLS Monitor"""
import os, sys, json, time, socket, ssl, threading
from datetime import datetime, timedelta
from collections import defaultdict

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
STATE_FILE = os.path.join(BASE, "layer25_state.json")

try:
    import requests
    with open(os.path.join(HOME, "vorix/.tg-token")) as f:
        TG = f.read().strip()
except:
    TG = ""
CHAT = "175160049"

# دامنه‌هایی که مانیتور می‌شن
DOMAINS = [
    "github.com",
    "google.com",
    "cloudflare.com",
    "telegram.org",
]

CONFIG = {
    "check_interval": 86400,        # هر ۲۴ ساعت
    "warn_days": 30,                # ۳۰ روز مونده → warn
    "critical_days": 7,             # ۷ روز مونده → critical
    "min_tls": "TLSv1.2",           # حداقل نسخه
}

WEAK_CIPHERS = ["RC4", "DES", "3DES", "MD5", "NULL", "EXPORT"]


class SSLMonitor:
    def __init__(self):
        self.results = {}
        self.stats = {"checks": 0, "warnings": 0, "critical": 0, "started": time.time()}
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

    def check_cert(self, host, port=443):
        """چک گواهی"""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((host, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
                    tls_version = ssock.version()
                    cipher = ssock.cipher()
                    
                    # تاریخ انقضا
                    not_after = cert.get("notAfter", "")
                    try:
                        expires = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                    except:
                        expires = None
                    
                    days_left = (expires - datetime.now()).days if expires else 0
                    
                    return {
                        "host": host,
                        "expires": expires.isoformat() if expires else None,
                        "days_left": days_left,
                        "tls": tls_version,
                        "cipher": cipher[0] if cipher else "?",
                        "issuer": dict(x[0] for x in cert.get("issuer", [])),
                        "subject": dict(x[0] for x in cert.get("subject", [])),
                    }
        except Exception as e:
            return {"host": host, "error": str(e)}

    def analyze(self, result):
        """تحلیل نتیجه"""
        issues = []
        host = result.get("host", "?")
        
        if "error" in result:
            issues.append(("ERROR", f"Connection failed: {result['error']}"))
            self.stats["critical"] += 1
            return issues
        
        days = result.get("days_left", 999)
        tls = result.get("tls", "?")
        cipher = result.get("cipher", "?")
        
        # چک انقضا
        if days <= CONFIG["critical_days"]:
            issues.append(("CRITICAL", f"Certificate expires in {days} days"))
            self.stats["critical"] += 1
        elif days <= CONFIG["warn_days"]:
            issues.append(("WARN", f"Certificate expires in {days} days"))
            self.stats["warnings"] += 1
        
        # چک TLS
        if tls in ("TLSv1", "TLSv1.1", "SSLv3", "SSLv2"):
            issues.append(("CRITICAL", f"Weak TLS: {tls}"))
            self.stats["critical"] += 1
        
        # چک cipher
        for weak in WEAK_CIPHERS:
            if weak in cipher:
                issues.append(("WARN", f"Weak cipher: {cipher}"))
                self.stats["warnings"] += 1
                break
        
        return issues

    def check_all(self):
        """چک همه دامنه‌ها"""
        print("🔒 SSL/TLS Monitor")
        print(f"📊 Domains: {len(DOMAINS)}")
        print()
        
        for host in DOMAINS:
            print(f"🔍 {host}...")
            result = self.check_cert(host)
            self.results[host] = result
            self.stats["checks"] += 1
            
            issues = self.analyze(result)
            
            if issues:
                for level, msg in issues:
                    icon = "🔴" if level == "CRITICAL" else "🟡"
                    print(f"   {icon} {msg}")
                self._alert(host, issues)
            else:
                days = result.get("days_left", "?")
                tls = result.get("tls", "?")
                print(f"   ✅ OK ({days}d, {tls})")
        
        self.save_state()

    def _alert(self, host, issues):
        if not TG: return
        try:
            lines = []
            for level, msg in issues:
                icon = "🔴" if level == "CRITICAL" else "🟡"
                lines.append(f"{icon} {msg}")
            
            msg = (
                f"🔒 *SSL Monitor Alert*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Host: `{host}`\n\n" + "\n".join(lines) +
                f"\n\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            )
            requests.post(
                f"https://api.telegram.org/bot{TG}/sendMessage",
                json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
        except: pass

    def watch(self):
        print(f"🔒 SSL Monitor — every {CONFIG['check_interval']}s")
        while True:
            try:
                self.check_all()
                print(f"\n⏳ Next check in {CONFIG['check_interval'] // 3600}h\n")
                time.sleep(CONFIG["check_interval"])
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"⚠️ {e}")
                time.sleep(3600)

    def status(self):
        uptime = int(time.time() - self.stats["started"])
        print(f"\n🔒 L25 SSL/TLS Monitor")
        print(f"═══════════════════════════════")
        print(f"Checks:     {self.stats['checks']}")
        print(f"Warnings:   {self.stats['warnings']}")
        print(f"Critical:   {self.stats['critical']}")
        print(f"Uptime:     {uptime // 3600}h {(uptime // 60) % 60}m")
        print()
        print(f"📊 Monitored:")
        for host, r in self.results.items():
            if "error" in r:
                print(f"   ❌ {host}: {r['error'][:40]}")
            else:
                days = r.get("days_left", "?")
                tls = r.get("tls", "?")
                icon = "🔴" if isinstance(days, int) and days <= 7 else "🟢"
                print(f"   {icon} {host:<20} {days}d, {tls}")

    def test(self):
        print("🧪 Testing SSL Monitor\n")
        self.check_all()
        print()
        self.status()


def main():
    if len(sys.argv) < 2:
        print("Usage: layer25_ssl_monitor.py {watch|status|check|test}")
        return
    cmd = sys.argv[1]
    sm = SSLMonitor()

    if cmd == "watch": sm.watch()
    elif cmd == "status": sm.status()
    elif cmd == "check": sm.check_all()
    elif cmd == "test": sm.test()


if __name__ == "__main__":
    main()
