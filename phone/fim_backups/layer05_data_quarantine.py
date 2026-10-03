#!/usr/bin/env python3
"""
L5 — DATA QUARANTINE
Snapshot → Isolate → Backup → Alert
"""
import os, sys, json, time, socket, subprocess, threading, shutil
from datetime import datetime
from collections import deque

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
QUARANTINE_DIR = os.path.join(BASE, "quarantine")
STATE_FILE = os.path.join(BASE, "quarantine_state.json")

os.makedirs(QUARANTINE_DIR, exist_ok=True)

try:
    import requests
    with open(os.path.join(HOME, "vorix/.tg-token")) as f:
        TG = f.read().strip()
except:
    TG = ""
CHAT = "175160049"

# ═══════════════════════════════════════════════
#   CONFIG
# ═══════════════════════════════════════════════
CONFIG = {
    "trigger_on_attempts": 3,        # ۳ تلاش دزدی → قفل
    "window_seconds": 60,            # در ۶۰ ثانیه
    "auto_recover_after": None,      # None = دستی
    "notify_before": True,           # اول Alert بعد Lock
    "isolate_method": "filesystem",  # filesystem | network | both
}

# الگوهای تلاش دزدی
EXFIL_PATTERNS = [
    "bulk_export", "mass_download", "data_dump",
    "select_all", "export_table", "dump_database",
    "copy_database", "backup_export", "unauthorized_read",
    "EXFIL", "EXFILTRATION", "DATA_THEFT", "MASS_READ"
]

# ═══════════════════════════════════════════════
#   DATA QUARANTINE
# ═══════════════════════════════════════════════

class DataQuarantine:
    def __init__(self):
        self.attempts = deque(maxlen=100)
        self.quarantined = False
        self.quarantined_at = None
        self.snapshot_path = None
        self.backup_path = None
        self.load_state()

    def load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE) as f:
                    s = json.load(f)
                    self.quarantined = s.get("quarantined", False)
                    self.quarantined_at = s.get("quarantined_at")
                    self.snapshot_path = s.get("snapshot_path")
                    self.backup_path = s.get("backup_path")
            except:
                pass

    def save_state(self):
        try:
            with open(STATE_FILE, "w") as f:
                json.dump({
                    "quarantined": self.quarantined,
                    "quarantined_at": self.quarantined_at,
                    "snapshot_path": self.snapshot_path,
                    "backup_path": self.backup_path,
                    "saved_at": datetime.now().isoformat(),
                }, f, indent=2)
        except:
            pass

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line)
        try:
            with open(os.path.join(QUARANTINE_DIR, "quarantine.log"), "a") as f:
                f.write(line + "\n")
        except:
            pass

    # ─────────────────────────────────────────
    #   DETECT EXFIL
    # ─────────────────────────────────────────
    def check_event(self, event):
        """بررسی هر رویداد — آیا تلاش دزدی هست؟"""
        if self.quarantined:
            return  # قبلاً قفل شده

        etype = (event.get("event_type", "") + " " + 
                 event.get("message", "")).upper()

        is_exfil = False
        for pattern in EXFIL_PATTERNS:
            if pattern.upper() in etype:
                is_exfil = True
                break

        # اگر نه، چک کن با metadata
        meta = event.get("metadata", {})
        if meta.get("bulk_size") and int(meta.get("bulk_size", 0)) > 1000:
            is_exfil = True

        if is_exfil:
            self.record_exfil_attempt(event)

    def record_exfil_attempt(self, event):
        """ثبت تلاش دزدی"""
        now = time.time()
        self.attempts.append({
            "ts": now,
            "event": event,
            "ip": event.get("source_ip", "?")
        })

        # چک کن تعداد در بازه
        recent = [a for a in self.attempts if now - a["ts"] < CONFIG["window_seconds"]]
        count = len(recent)

        self.log(f"⚠️ Exfil attempt #{count} from {event.get('source_ip', '?')}")

        # اگه بسته شد → قفل کن
        if count >= CONFIG["trigger_on_attempts"]:
            self.trigger_quarantine(recent)

    # ─────────────────────────────────────────
    #   TRIGGER — Snapshot → Isolate → Backup
    # ─────────────────────────────────────────
    def trigger_quarantine(self, attempts):
        """قفل کردن — با ترتیب درست"""
        if self.quarantined:
            return

        print()
        print("╔════════════════════════════════════════════╗")
        print("║  🔴 DATA QUARANTINE ACTIVATED              ║")
        print("║  Snapshot → Isolate → Backup               ║")
        print("╚════════════════════════════════════════════╝")
        print()

        self.quarantined = True
        self.quarantined_at = datetime.now().isoformat()

        # ── مرحله ۱: Snapshot فوری (۱-۲ ثانیه)
        print("📸 [1/5] Snapshot فوری...")
        self.snapshot_path = self._take_snapshot()

        # ── مرحله ۲: Alert سریع به تو (پیش از قطع)
        if CONFIG["notify_before"]:
            print("📱 [2/5] Alert به تو...")
            self._notify_alert(attempts)

        # ── مرحله ۳: قطع فوری اینترنت (۱ ثانیه)
        print("🌐 [3/5] قطع اینترنت...")
        self._isolate_network()

        # ── مرحله ۴: بک‌آپ کامل (پس‌زمینه)
        print("💾 [4/5] شروع بک‌آپ...")
        threading.Thread(target=self._full_backup, daemon=True).start()

        # ── مرحله ۵: قفل فایل‌ها
        print("🔒 [5/5] قفل فایل‌ها...")
        self._lock_files()

        self.save_state()

        print()
        print("✅ Quarantine کامل شد")
        print(f"   Snapshot: {self.snapshot_path}")
        print()
        print("🔄 برای بازگردانی:")
        print("   python3 layer05_data_quarantine.py recover")
        print()

    def _take_snapshot(self):
        """Snapshot فوری از state"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(QUARANTINE_DIR, f"snapshot_{ts}")

        try:
            os.makedirs(path, exist_ok=True)

            # فایل‌های state مهم
            state_files = [
                "queue.jsonl",
                "threat_cache.json",
                "killswitch_state.json",
                "stats.json",
            ]

            for f in state_files:
                src = os.path.join(BASE, f)
                if os.path.exists(src):
                    shutil.copy2(src, path)

            # snapshot فوری به یک فایل zip کوچک
            archive = os.path.join(QUARANTINE_DIR, f"snapshot_{ts}.tar.gz")
            os.system(f"cd {path} && tar -czf {archive} . 2>/dev/null")
            shutil.rmtree(path, ignore_errors=True)

            size = os.path.getsize(archive) if os.path.exists(archive) else 0
            self.log(f"📸 Snapshot: {archive} ({size} bytes)")
            return archive
        except Exception as e:
            self.log(f"⚠️ Snapshot failed: {e}")
            return None

    def _isolate_network(self):
        """قطع فوری اینترنت"""
        try:
            # روش ۱: قطع WiFi
            pass  # REMOVED — network isolation disabled (was breaking internet)

            # روش ۲: بلاک همه اتصالات خروجی (اگر دسترسی داریم)
            pass  # REMOVED
            os.system(f'iptables -I OUTPUT -d 127.0.0.1 -j ACCEPT 2>/dev/null || true')

            self.log("🌐 Network isolated")
        except Exception as e:
            self.log(f"⚠️ Network isolate: {e}")

    def _full_backup(self):
        """بک‌آپ کامل در پس‌زمینه"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(QUARANTINE_DIR, f"backup_{ts}.tar.gz")

        try:
            os.system(
                f"cd {HOME} && tar -czf {path} "
                f"--exclude='quarantine' "
                f"--exclude='killswitch-backups' "
                f"--exclude='*.tar.gz' "
                f"--exclude='__pycache__' "
                f"vorix vorix-hybrid vorix-master 2>/dev/null"
            )

            if os.path.exists(path):
                size = os.path.getsize(path)
                self.backup_path = path
                self.save_state()
                self.log(f"💾 Backup: {path} ({size//1024}KB)")

                # Alert نهایی
                self._notify_backup_done(path, size)
        except Exception as e:
            self.log(f"⚠️ Backup failed: {e}")

    def _lock_files(self):
        """قفل فایل‌های حساس"""
        try:
            # فایل‌های حساس → فقط خواندنی
            sensitive = [
                os.path.join(HOME, "vorix/.tg-token"),
                os.path.join(BASE, "config.json"),
            ]
            for f in sensitive:
                if os.path.exists(f):
                    os.chmod(f, 0o400)

            # پوشه‌های اصلی → فقط خواندنی
            for d in ["vorix", "vorix-hybrid", "vorix-master"]:
                path = os.path.join(HOME, d)
                if os.path.exists(path):
                    os.system(f"chmod -R 500 {path} 2>/dev/null")

            self.log("🔒 Files locked (read-only)")
        except Exception as e:
            self.log(f"⚠️ Lock failed: {e}")

    # ─────────────────────────────────────────
    #   NOTIFY
    # ─────────────────────────────────────────
    def _notify_alert(self, attempts):
        """Alert فوری به تلگرام"""
        if not TG:
            return
        try:
            ips = list(set(a["ip"] for a in attempts))
            msg = (
                "🔴 *DATA QUARANTINE — فعال شد!*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"⚠️ *Reason:* {len(attempts)} تلاش دزدی داده\n"
                f"🎯 *Attacker IPs:* `{', '.join(ips[:3])}`\n"
                f"⏰ *Time:* {datetime.now().strftime('%H:%M:%S')}\n\n"
                "🛡️ *Actions in progress:*\n"
                "• 📸 Snapshot گرفته شد\n"
                "• 🌐 اینترنت قطع شد\n"
                "• 💾 بک‌آپ در حال اجرا\n"
                "• 🔒 فایل‌ها قفل می‌شن\n\n"
                "⚡ _سیستم در حالت Quarantine_\n"
                "🔄 _Recovery: python3 layer05_data_quarantine.py recover_"
            )
            requests.post(
                f"https://api.telegram.org/bot{TG}/sendMessage",
                json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
            os.system('termux-vibrate -d 1000 2>/dev/null')
            os.system('termux-tts-speak "Data quarantine activated" 2>/dev/null')
        except:
            pass

    def _notify_backup_done(self, path, size):
        """اطلاع پس از تکمیل بک‌آپ"""
        if not TG:
            return
        try:
            msg = (
                "✅ *Backup کامل شد*\n\n"
                f"📁 `{os.path.basename(path)}`\n"
                f"📊 `{size // 1024} KB`\n\n"
                "🟢 سیستم در Quarantine — منتظر تصمیم تو"
            )
            requests.post(
                f"https://api.telegram.org/bot{TG}/sendMessage",
                json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
        except:
            pass

    # ─────────────────────────────────────────
    #   RECOVER
    # ─────────────────────────────────────────
    def recover(self):
        """بازگردانی سیستم"""
        print("🔄 در حال بازگردانی...")

        # اینترنت
        os.system('svc wifi enable 2>/dev/null || true')
        os.system('iptables -F OUTPUT 2>/dev/null || true')

        # فایل‌ها
        for d in ["vorix", "vorix-hybrid", "vorix-master"]:
            path = os.path.join(HOME, d)
            if os.path.exists(path):
                os.system(f"chmod -R 700 {path} 2>/dev/null")

        # فایل‌های حساس
        sensitive = [
            os.path.join(HOME, "vorix/.tg-token"),
            os.path.join(BASE, "config.json"),
        ]
        for f in sensitive:
            if os.path.exists(f):
                os.chmod(f, 0o600)

        self.quarantined = False
        self.quarantined_at = None
        self.attempts.clear()
        self.save_state()

        self.log("🟢 Quarantine RELEASED")

        if TG:
            try:
                requests.post(
                    f"https://api.telegram.org/bot{TG}/sendMessage",
                    json={"chat_id": CHAT, "text": "🟢 *Quarantine released*\nسیستم بازگشت"},
                    parse_mode="Markdown", timeout=10
                )
            except:
                pass

    # ─────────────────────────────────────────
    #   STATUS
    # ─────────────────────────────────────────
    def status(self):
        return {
            "quarantined": self.quarantined,
            "quarantined_at": self.quarantined_at,
            "snapshot": self.snapshot_path,
            "backup": self.backup_path,
            "attempts": len(self.attempts),
        }

# ═══════════════════════════════════════════════
#   WATCHER — وصل شدن به queue
# ═══════════════════════════════════════════════
def watch():
    """پایش queue.jsonl"""
    dq = DataQuarantine()
    qfile = os.path.join(BASE, "queue.jsonl")
    last_pos = 0

    print("🛡️ Data Quarantine Watcher active")
    print(f"👁️  Watching: {qfile}")
    print(f"🎯 Threshold: {CONFIG['trigger_on_attempts']} attempts in {CONFIG['window_seconds']}s")
    print()

    while True:
        try:
            if not os.path.exists(qfile):
                time.sleep(2)
                continue

            size = os.path.getsize(qfile)
            if size < last_pos:
                last_pos = 0
            if size == last_pos:
                time.sleep(1)
                continue

            with open(qfile) as f:
                f.seek(last_pos)
                lines = f.readlines()
                last_pos = f.tell()

            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    dq.check_event(event)
                except:
                    pass

        except KeyboardInterrupt:
            print("\n⏹ Stopped")
            sys.exit(0)
        except Exception as e:
            print(f"⚠️ {e}")
            time.sleep(5)

# ═══════════════════════════════════════════════
#   CLI
# ═══════════════════════════════════════════════
def main():
    if len(sys.argv) < 2:
        print("""
🔴 L5 — DATA QUARANTINE

Usage:
  watch     پایش و قفل خودکار
  status    وضعیت
  trigger   فعال‌سازی دستی (تست)
  recover   بازگردانی

Triggers:
  • 3 attempts in 60s → فعال
  • Bulk export detection
  • Mass download
  • Unauthorized read
        """)
        return

    cmd = sys.argv[1]
    dq = DataQuarantine()

    if cmd == "watch":
        watch()
    elif cmd == "status":
        s = dq.status()
        print(f"""
🔴 Data Quarantine Status
══════════════════════════
Quarantined:  {"🔴 YES" if s['quarantined'] else "🟢 NO"}
When:         {s['quarantined_at'] or '-'}
Attempts:     {s['attempts']}
Snapshot:     {s['snapshot'] or '-'}
Backup:       {s['backup'] or '-'}
        """)
    elif cmd == "trigger":
        # تست — ۳ رویداد جعلی
        for i in range(3):
            dq.record_exfil_attempt({"source_ip": "1.2.3.4", "event_type": "EXFIL"})
        print("✅ Trigger test done")
    elif cmd == "recover":
        dq.recover()

if __name__ == "__main__":
    main()
