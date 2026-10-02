#!/usr/bin/env python3
"""L19 — Password Leak Monitor"""
import os, sys, json, time, hashlib, threading
from datetime import datetime

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
STATE_FILE = os.path.join(BASE, "layer19_state.json")

try:
    import requests
    with open(os.path.join(HOME, "vorix/.tg-token")) as f:
        TG = f.read().strip()
except:
    TG = ""
CHAT = "175160049"

CONFIG = {
    "check_interval": 86400,  # روزانه
    "emails_to_watch": [
        # ایمیل‌های خودت رو اینجا بذار
        # "my@email.com",
    ],
}


class PasswordLeak:
    def __init__(self):
        self.results = {}
        self.stats = {"checks": 0, "breaches_found": 0, "started": time.time()}
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
                json.dump({
                    "stats": self.stats,
                    "results": dict(list(self.results.items())[-50:]),
                }, f, indent=2)
        except: pass

    def check_email(self, email):
        """چک ایمیل با HaveIBeenPwned API"""
        # API رایگان نیاز به کلید داره ولی این ساده‌ست
        try:
            # استفاده از نسخه رایگان limited
            r = requests.get(
                f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
                headers={"User-Agent": "VORIX-Security"},
                timeout=10
            )
            if r.status_code == 200:
                breaches = r.json()
                return breaches
            elif r.status_code == 404:
                return []  # No breaches
            elif r.status_code == 429:
                return None  # Rate limited
        except: pass
        return None

    def check_all(self):
        if not CONFIG["emails_to_watch"]:
            print("⚠️ No emails to watch. Add them to CONFIG.")
            return
        
        for email in CONFIG["emails_to_watch"]:
            print(f"🔍 Checking {email}...")
            result = self.check_email(email)
            self.stats["checks"] += 1
            
            if result is None:
                print(f"   ⚠️ API error")
                continue
            
            if result:
                self.stats["breaches_found"] += len(result)
                self.results[email] = {
                    "breaches": len(result),
                    "list": [b.get("Name", "?") for b in result[:5]],
                    "checked": datetime.now().isoformat(),
                }
                print(f"   🚨 {len(result)} breaches!")
                self._alert(email, result)
            else:
                print(f"   ✅ No breaches")
                self.results[email] = {"breaches": 0, "checked": datetime.now().isoformat()}
        
        self.save_state()

    def _alert(self, email, breaches):
        if not TG: return
        try:
            names = ", ".join(b.get("Name", "?") for b in breaches[:5])
            msg = (
                f"🚨 *Password Leak Alert*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Email: `{email}`\n"
                f"Breaches: `{len(breaches)}`\n"
                f"Sources: {names}\n\n"
                f"⚠️ Change your password immediately!\n"
                f"⏰ {datetime.now().strftime('%H:%M:%S')}"
            )
            requests.post(
                f"https://api.telegram.org/bot{TG}/sendMessage",
                json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
        except: pass

    def watch(self):
        while True:
            try:
                self.check_all()
                time.sleep(CONFIG["check_interval"])
            except KeyboardInterrupt:
                break
            except: time.sleep(3600)

    def status(self):
        uptime = int(time.time() - self.stats["started"])
        print(f"\n🔑 L19 Password Leak Monitor")
        print(f"═══════════════════════════════")
        print(f"Checks:          {self.stats['checks']}")
        print(f"Breaches found:  {self.stats['breaches_found']}")
        print(f"Emails watched:  {len(CONFIG['emails_to_watch'])}")
        print(f"Uptime:          {uptime // 3600}h {(uptime // 60) % 60}m")

    def test(self):
        print("🧪 Testing Password Leak Monitor\n")
        # تست با یک ایمیل تستی که معمولاً لو رفته
        test_emails = ["test@example.com"]
        for email in test_emails:
            result = self.check_email(email)
            if result is None:
                print(f"   ⚠️ API error for {email}")
            elif result:
                print(f"   🚨 {email}: {len(result)} breaches")
            else:
                print(f"   ✅ {email}: No breaches")
        print()
        self.status()


def main():
    if len(sys.argv) < 2:
        print("Usage: layer19_password_leak.py {check|watch|status|test}")
        return
    cmd = sys.argv[1]
    pl = PasswordLeak()
    if cmd == "check": pl.check_all()
    elif cmd == "watch": pl.watch()
    elif cmd == "status": pl.status()
    elif cmd == "test": pl.test()

if __name__ == "__main__":
    main()
