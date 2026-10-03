#!/usr/bin/env python3
"""
L16 — DEAD MAN'S SWITCH
کلید نهایی — وقتی هکر جدی شد، همه چیز خاموش می‌شه
"""
import os
import sys
import json
import time
import signal
import threading
import subprocess
import requests
from datetime import datetime, timedelta
from collections import deque, defaultdict

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
LOGS = os.path.join(BASE, "logs")
os.makedirs(LOGS, exist_ok=True)

STATE_FILE = os.path.join(BASE, "killswitch_state.json")
EVENTS_FILE = os.path.join(BASE, "killswitch_events.jsonl")

try:
    with open(os.path.join(HOME, "vorix/.tg-token")) as f:
        TG_TOKEN = f.read().strip()
except:
    TG_TOKEN = ""
CHAT_ID = "175160049"

# ═══════════════════════════════════════════════
#   CONFIG — کِی فعال بشه
# ═══════════════════════════════════════════════

TRIGGERS = {
    "critical_in_60s":     3,      # ۳ حمله CRITICAL در ۶۰ ثانیه
    "total_attacks_60s":   10,     # ۱۰ حمله (هر نوع) در ۶۰ ثانیه
    "data_exfil":          True,   # تلاش برای خروج داده
    "admin_denied":        True,   # تلاش برای دسترسی ادمین
    "kernel_anomaly":      True,   # رفتار مشکوک kernel
    "manual":              True,   # کاربر دستی زد
}

# ═══════════════════════════════════════════════
#   ACTIONS — چیکار کنه وقتی فعال شد
# ═══════════════════════════════════════════════

ACTIONS = {
    "notify_telegram":     True,   # خبر به تلگرام
    "notify_voice":        True,   # هشدار صوتی
    "notify_vibrate":      True,   # ویبره
    "backup_data":         True,   # بک‌آپ فوری
    "kill_services":       True,   # کشتن سرویس‌ها
    "disable_network":     True,   # قطع شبکه (اگه ممکن)
    "lock_files":          True,   # قفل فایل‌ها
    "wipe_sensitive":      False,  # پاک‌سازی حساس (خطرناک!)
    "reboot_device":       False,  # ری‌استارت (خطرناک!)
}

# ═══════════════════════════════════════════════
#   KILL SWITCH
# ═══════════════════════════════════════════════

class KillSwitch:
    def __init__(self):
        self.armed = True               # فعال هست
        self.triggered = False          # زده شده؟
        self.triggered_at = None
        self.trigger_reason = None
        self.events = deque(maxlen=500) # ۵۰۰ رویداد اخیر
        self.lock = threading.Lock()
        self.load_state()

    def load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE) as f:
                    s = json.load(f)
                    self.armed = s.get("armed", True)
                    self.triggered = s.get("triggered", False)
                    self.trigger_reason = s.get("reason")
            except:
                pass

    def save_state(self):
        try:
            with open(STATE_FILE, "w") as f:
                json.dump({
                    "armed": self.armed,
                    "triggered": self.triggered,
                    "reason": self.trigger_reason,
                    "triggered_at": self.triggered_at,
                    "saved_at": datetime.now().isoformat(),
                }, f, indent=2)
        except:
            pass

    def log(self, msg):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line)
        try:
            with open(os.path.join(LOGS, "killswitch.log"), "a") as f:
                f.write(line + "\n")
        except:
            pass

    # ─────────── Event Recording ───────────
    def record_event(self, severity, event_type, extra=None):
        """هر حمله رو ثبت کن"""
        if not self.armed or self.triggered:
            return

        with self.lock:
            event = {
                "ts": time.time(),
                "severity": severity,
                "type": event_type,
                "extra": extra or {},
            }
            self.events.append(event)
            self._check_triggers()

    def _check_triggers(self):
        """چک کن کِی باید فعال بشه"""
        now = time.time()
        last_60s = [e for e in self.events if now - e["ts"] < 60]

        # ۱. Critical in 60s
        crit_count = sum(1 for e in last_60s if e["severity"] == "CRITICAL")
        if crit_count >= TRIGGERS["critical_in_60s"]:
            self.trigger(f"{crit_count} CRITICAL attacks in 60s")
            return

        # ۲. Total attacks in 60s
        if len(last_60s) >= TRIGGERS["total_attacks_60s"]:
            self.trigger(f"{len(last_60s)} attacks in 60s")
            return

        # ۳. Data Exfiltration
        for e in last_60s:
            if e["type"] == "DATA_EXFIL":
                self.trigger("Data exfiltration detected")
                return

        # ۴. Admin Access Denied
        for e in last_60s:
            if e["type"] == "ADMIN_ACCESS_DENIED":
                self.trigger("Admin access denied")
                return

        # ۵. Kernel Anomaly
        for e in last_60s:
            if e["type"] == "KERNEL_ANOMALY":
                self.trigger("Kernel anomaly detected")
                return

    # ─────────── Manual Trigger ───────────
    def manual_trigger(self, reason="User pressed PANIC"):
        """کاربر دستی زد"""
        self.trigger(reason)

    # ─────────── Actual Trigger ───────────
    def trigger(self, reason):
        """فعال‌سازی Kill Switch"""
        if self.triggered:
            return

        self.triggered = True
        self.triggered_at = datetime.now().isoformat()
        self.trigger_reason = reason

        print()
        print("╔═══════════════════════════════════════════════╗")
        print("║                                               ║")
        print("║      🔴 DEAD MAN'S SWITCH ACTIVATED 🔴        ║")
        print("║                                               ║")
        print("║      Reason: " + reason[:35].ljust(35) + "║")
        print("║      Time:   " + datetime.now().strftime("%H:%M:%S").ljust(35) + "║")
        print("║                                               ║")
        print("╚═══════════════════════════════════════════════╝")
        print()

        self.log(f"🔴 KILL SWITCH TRIGGERED: {reason}")
        self.save_state()
        self._log_trigger_event(reason)
        self._execute_actions()

    def _log_trigger_event(self, reason):
        try:
            with open(EVENTS_FILE, "a") as f:
                f.write(json.dumps({
                    "timestamp": datetime.now().isoformat(),
                    "action": "KILL_SWITCH",
                    "reason": reason,
                    "events_count": len(self.events),
                }) + "\n")
        except:
            pass

    # ─────────── Actions ───────────
    def _execute_actions(self):
        """اجرای همه اکشن‌ها"""
        print("🔴 Executing protective actions...\n")

        if ACTIONS["notify_telegram"]:
            self._action_telegram()

        if ACTIONS["notify_voice"]:
            self._action_voice()

        if ACTIONS["notify_vibrate"]:
            self._action_vibrate()

        if ACTIONS["backup_data"]:
            self._action_backup()

        if ACTIONS["kill_services"]:
            self._action_kill_services()

        if ACTIONS["disable_network"]:
            self._action_disable_network()

        if ACTIONS["lock_files"]:
            self._action_lock_files()

        if ACTIONS["wipe_sensitive"]:
            self._action_wipe()

        if ACTIONS["reboot_device"]:
            self._action_reboot()

        print("\n✅ همه اکشن‌ها اجرا شد")
        self.log("✅ All protective actions executed")

    def _action_telegram(self):
        try:
            msg = (
                "🔴 *DEAD MAN'S SWITCH*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"⚠️ *Reason:* {self.trigger_reason}\n"
                f"⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"📊 *Events:* {len(self.events)}\n\n"
                "🛡️ *Actions taken:*\n"
                "• 🔒 Services killed\n"
                "• 💾 Backup executed\n"
                "• 🌐 Network disabled\n"
                "• 📁 Files locked\n\n"
                "🔄 *To recover:*\n"
                "`bash ~/vorix-master/scripts/vorix-recover.sh`\n\n"
                "⚠️ _System is now OFFLINE._"
            )
            requests.post(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
            print("  ✅ Telegram sent")
        except Exception as e:
            print(f"  ⚠️ Telegram failed: {e}")

    def _action_voice(self):
        try:
            os.system('termux-tts-speak "Dead man switch activated. System offline." 2>/dev/null')
            print("  ✅ Voice alert")
        except:
            pass

    def _action_vibrate(self):
        try:
            for _ in range(3):
                os.system('termux-vibrate -d 800 2>/dev/null')
                time.sleep(0.3)
            print("  ✅ Vibration")
        except:
            pass

    def _action_backup(self):
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(HOME, "killswitch-backups")
            os.makedirs(backup_dir, exist_ok=True)
            path = os.path.join(backup_dir, f"emergency_{ts}.tar.gz")

            os.system(
                f"cd {HOME} && tar -czf {path} "
                f"--exclude='killswitch-backups' "
                f"--exclude='*.tar.gz' "
                f"vorix vorix-hybrid vorix-master 2>/dev/null"
            )
            print(f"  ✅ Backup: {path}")
            self.log(f"💾 Backup saved: {path}")
        except Exception as e:
            print(f"  ⚠️ Backup failed: {e}")

    def _action_kill_services(self):
        try:
            services = [
                "agent.py", "sentinel.py", "server.py",
                "alertd.py", "shield.py", "fortress.py",
                "mocker.py", "layer16_killswitch.py",
            ]
            for svc in services:
                os.system(f"pkill -f {svc} 2>/dev/null")

            # خودمون رو هم می‌کشیم (بعد از همه اکشن‌ها)
            print("  ✅ Services killed")

            # اسکریپت خودکشی (بعد از ۳ ثانیه)
            threading.Timer(3.0, lambda: os.kill(os.getpid(), signal.SIGTERM)).start()
        except Exception as e:
            print(f"  ⚠️ Kill failed: {e}")

    def _action_disable_network(self):
        """قطع WiFi (اگر ممکن)"""
        try:
            # تلاش برای قطع WiFi
            os.system('svc wifi disable 2>/dev/null || true')
            # یا قطع اینترنت در Termux
            os.system('termux-wifi-connectioninfo 2>/dev/null > /dev/null || true')
            print("  ✅ Network disabled (best effort)")
        except:
            pass

    def _action_lock_files(self):
        """قفل کردن فایل‌های حساس"""
        try:
            sensitive_dirs = [
                os.path.join(HOME, "vorix-hybrid"),
                os.path.join(HOME, "vorix"),
                os.path.join(HOME, "vorix-master"),
            ]
            for d in sensitive_dirs:
                if os.path.exists(d):
                    os.system(f"chmod -R 000 {d} 2>/dev/null")
            print("  ✅ Files locked")
        except:
            pass

    def _action_wipe(self):
        """پاک‌سازی فایل‌های فوق حساس (فقط اگه فعال باشه)"""
        try:
            wipe_files = [
                os.path.join(HOME, "vorix/.tg-token"),
                os.path.join(HOME, "vorix-hybrid/phone/config.json"),
            ]
            for f in wipe_files:
                if os.path.exists(f):
                    os.system(f"shred -u {f} 2>/dev/null || rm -f {f}")
            print("  ✅ Sensitive data wiped")
        except:
            pass

    def _action_reboot(self):
        """ری‌استارت گوشی (خطرناک)"""
        try:
            os.system('reboot 2>/dev/null || svc power reboot 2>/dev/null || true')
        except:
            pass

    # ─────────── Recovery ───────────
    def recover(self):
        """بازگرداندن سیستم از حالت قفل"""
        self.triggered = False
        self.triggered_at = None
        self.trigger_reason = None
        self.events.clear()
        self.save_state()

        # باز کردن فایل‌ها
        try:
            for d in ["vorix", "vorix-hybrid", "vorix-master"]:
                path = os.path.join(HOME, d)
                if os.path.exists(path):
                    os.system(f"chmod -R 700 {path} 2>/dev/null")
        except:
            pass

        # روشن کردن WiFi
        try:
            os.system('svc wifi enable 2>/dev/null || true')
        except:
            pass

        self.log("🟢 KILL SWITCH RECOVERED")

# ═══════════════════════════════════════════════
#   INTEGRATION — چطور به سیستم وصل بشه
# ═══════════════════════════════════════════════

# استفاده در sentinel.py یا agent.py:
#
# from layer16_killswitch import KillSwitch
# ks = KillSwitch()
#
# # هر رویداد که اومد:
# ks.record_event("CRITICAL", "SQLI_DETECTED", {"ip": "1.2.3.4"})
#
# # اگه کاربر خواست دستی بزنه:
# ks.manual_trigger("User panic")

# ═══════════════════════════════════════════════
#   WATCHER — پایش فایل لاگ
# ═══════════════════════════════════════════════

def watch_and_trigger():
    """پایش لحظه‌ای — اگه حمله شدید شد، فعال کن"""
    ks = KillSwitch()

    log_file = os.path.join(HOME, "vorix-hybrid/phone/queue.jsonl")
    last_pos = 0

    print("🛡️ Kill Switch Watcher active")
    print(f"📁 Watching: {log_file}")
    print()

    while True:
        try:
            if not os.path.exists(log_file):
                time.sleep(2)
                continue

            size = os.path.getsize(log_file)
            if size < last_pos:
                last_pos = 0
            if size == last_pos:
                time.sleep(1)
                continue

            with open(log_file) as f:
                f.seek(last_pos)
                lines = f.readlines()
                last_pos = f.tell()

            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    sev = e.get("severity", "INFO")
                    etype = e.get("event_type", "UNKNOWN")
                    ks.record_event(sev, etype, e.get("metadata", {}))
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
🔴 L16 — DEAD MAN'S SWITCH

Usage:
  python3 layer16_killswitch.py watch       → پایش و تشخیص
  python3 layer16_killswitch.py trigger     → فعال‌سازی دستی (PANIC)
  python3 layer16_killswitch.py recover     → بازگردانی
  python3 layer16_killswitch.py status      → وضعیت
  python3 layer16_killswitch.py arm         → فعال کردن
  python3 layer16_killswitch.py disarm      → غیرفعال کردن

Triggers:
  • 3 CRITICAL in 60s
  • 10 total attacks in 60s
  • Data exfiltration
  • Admin access denied
  • Kernel anomaly
  • Manual panic
        """)
        return

    cmd = sys.argv[1]
    ks = KillSwitch()

    if cmd == "watch":
        watch_and_trigger()
    elif cmd == "trigger":
        ks.manual_trigger("User pressed PANIC")
    elif cmd == "recover":
        ks.recover()
        print("🟢 System recovered")
    elif cmd == "status":
        print(f"""
🔴 Kill Switch Status
═══════════════════════
Armed:       {"✅" if ks.armed else "❌"}
Triggered:   {"🔴 YES" if ks.triggered else "🟢 NO"}
Reason:      {ks.trigger_reason or "-"}
When:        {ks.triggered_at or "-"}
Events:      {len(ks.events)}
        """)
    elif cmd == "arm":
        ks.armed = True
        ks.save_state()
        print("✅ Kill Switch armed")
    elif cmd == "disarm":
        ks.armed = False
        ks.save_state()
        print("⚠️ Kill Switch disarmed")

if __name__ == "__main__":
    main()
