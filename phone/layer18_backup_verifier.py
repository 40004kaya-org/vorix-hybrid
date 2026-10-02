#!/usr/bin/env python3
"""L18 — Backup Verifier"""
import os, sys, json, time, subprocess, hashlib
from datetime import datetime, timedelta

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
STATE_FILE = os.path.join(BASE, "backup_verifier_state.json")

try:
    import requests
    with open(os.path.join(HOME, "vorix/.tg-token")) as f:
        TG = f.read().strip()
except:
    TG = ""
CHAT = "175160049"

CONFIG = {
    "check_interval": 21600,        # هر ۶ ساعت
    "max_age_hours": 48,             # قدیمی‌تر از ۴۸ ساعت → Alert
    "min_size_kb": 1,                # حداقل ۱KB
    "backup_dirs": [
        os.path.join(HOME, "vorix-backups"),
        os.path.join(HOME, "vorix-hybrid-backups"),
        os.path.join(HOME, "killswitch-backups"),
        os.path.join(BASE, "quarantine"),
    ],
}

class BackupVerifier:
    def __init__(self):
        self.results = []
        self.load_state()

    def load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE) as f:
                    self.results = json.load(f).get("results", [])
            except:
                pass

    def save_state(self):
        try:
            with open(STATE_FILE, "w") as f:
                json.dump({
                    "last_check": datetime.now().isoformat(),
                    "results": self.results[-30:],  # ۳۰ نتیجه آخر
                }, f, indent=2)
        except:
            pass

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {msg}")

    def find_backups(self):
        """پیدا کردن همه بک‌آپ‌ها"""
        backups = []
        for d in CONFIG["backup_dirs"]:
            if not os.path.exists(d):
                continue
            try:
                for f in os.listdir(d):
                    if f.endswith((".tar.gz", ".gpg", ".json")):
                        path = os.path.join(d, f)
                        if os.path.isfile(path):
                            backups.append(path)
            except:
                pass
        return backups

    def verify_backup(self, path):
        """چک یک بک‌آپ"""
        result = {
            "path": path,
            "name": os.path.basename(path),
            "status": "unknown",
            "size": 0,
            "age_hours": 0,
            "issues": [],
        }
        try:
            size = os.path.getsize(path)
            result["size"] = size

            if size < CONFIG["min_size_kb"] * 1024:
                result["issues"].append("size_too_small")
                result["status"] = "corrupted"
                return result

            mtime = os.path.getmtime(path)
            age = (time.time() - mtime) / 3600
            result["age_hours"] = int(age)

            if age > CONFIG["max_age_hours"]:
                result["issues"].append("too_old")
                result["status"] = "stale"
                return result

            # تست سالم بودن tar.gz
            if path.endswith(".tar.gz"):
                r = subprocess.run(
                    ["tar", "-tzf", path],
                    capture_output=True, timeout=10
                )
                if r.returncode != 0:
                    result["issues"].append("invalid_tar")
                    result["status"] = "corrupted"
                    return result

            result["status"] = "ok"
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(str(e))
        return result

    def check_all(self):
        self.log("🔍 Checking backups...")
        backups = self.find_backups()

        if not backups:
            self.log("⚠️ No backups found!")
            self._alert("⚠️ *Backup Verifier*\n\nNo backups found!")
            return

        ok = 0
        stale = 0
        corrupted = 0

        for path in backups:
            result = self.verify_backup(path)
            self.results.append(result)
            status = result["status"]
            icon = {"ok": "✅", "stale": "🟡", "corrupted": "🔴", "error": "❌"}.get(status, "❓")
            self.log(f"{icon} {result['name']:<40} ({result['size']//1024}KB, {result['age_hours']}h)")

            if status == "ok": ok += 1
            elif status == "stale": stale += 1
            else: corrupted += 1

        self.save_state()

        print()
        self.log(f"📊 Total: {len(backups)} | ✅ {ok} | 🟡 {stale} | 🔴 {corrupted}")

        # Alert اگه لازمه
        if corrupted > 0:
            self._alert(f"🔴 *Backup Verifier*\n\n{corrupted} بک‌آپ خراب!\n{ok} سالم | {stale} قدیمی")
        elif stale > 0:
            self._alert(f"🟡 *Backup Verifier*\n\n{stale} بک‌آپ قدیمی‌تر از {CONFIG['max_age_hours']}h")

    def _alert(self, msg):
        if not TG:
            return
        try:
            requests.post(
                f"https://api.telegram.org/bot{TG}/sendMessage",
                json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
        except:
            pass

    def run(self):
        print("╔═══════════════════════════════════════════════╗")
        print("║   💾 L18 — BACKUP VERIFIER                    ║")
        print("╚═══════════════════════════════════════════════╝")
        print()
        while True:
            try:
                self.check_all()
                print(f"\n⏳ Next check in {CONFIG['check_interval']//3600}h\n")
                time.sleep(CONFIG["check_interval"])
            except KeyboardInterrupt:
                print("\n⏹ Stopped")
                sys.exit(0)
            except Exception as e:
                self.log(f"⚠️ {e}")
                time.sleep(60)

    def status(self):
        print(f"💾 Backup Verifier Status")
        print(f"Last check: {self.results[-1] if self.results else 'never'}\n")
        backups = self.find_backups()
        print(f"📁 Total backups: {len(backups)}\n")
        for path in backups[:10]:
            r = self.verify_backup(path)
            icon = {"ok": "✅", "stale": "🟡", "corrupted": "🔴", "error": "❌"}.get(r["status"], "❓")
            print(f"   {icon} {r['name']:<40} ({r['size']//1024}KB, {r['age_hours']}h)")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 layer18_backup_verifier.py {check|watch|status}")
        return
    cmd = sys.argv[1]
    bv = BackupVerifier()
    if cmd == "check":
        bv.check_all()
    elif cmd == "watch":
        bv.run()
    elif cmd == "status":
        bv.status()

if __name__ == "__main__":
    main()
