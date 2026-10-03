#!/usr/bin/env python3
"""L10 — Red Alert Mode"""
import os, sys, json, time, threading, subprocess
from datetime import datetime, timedelta
from collections import defaultdict, deque

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
STATE_FILE = os.path.join(BASE, "layer10_state.json")
EVENTS_FILE = os.path.join(BASE, "layer10_events.jsonl")

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
    # تریگرها
    "critical_in_5min": 5,         # ۵ حمله CRITICAL در ۵ دقیقه
    "attacks_in_5min": 20,          # ۲۰ حمله (هر نوع) در ۵ دقیقه
    "attack_types_diversity": 3,    # ۳ نوع حمله مختلف
    
    # حالت Red Alert
    "duration_minutes": 30,          # ۳۰ دقیقه فعال باشه
    "sensitivity_multiplier": 2,    # ۲x حساس‌تر
    
    # اکشن‌ها
    "notify_telegram": True,
    "notify_voice": True,
    "notify_vibrate": True,
    "enhanced_logging": True,
}

class RedAlert:
    def __init__(self):
        self.active = False
        self.activated_at = None
        self.expires_at = None
        self.events = deque(maxlen=1000)  # ۱۰۰۰ رویداد آخر
        self.alert_count = 0
        self.lock = threading.Lock()
        self.load_state()

    def load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE) as f:
                    s = json.load(f)
                    self.active = s.get("active", False)
                    self.activated_at = s.get("activated_at")
                    self.expires_at = s.get("expires_at")
                    self.alert_count = s.get("alert_count", 0)
                    # چک expiration
                    if self.active and self.expires_at:
                        exp = datetime.fromisoformat(self.expires_at)
                        if datetime.now() > exp:
                            self._deactivate("expired")
            except: pass

    def save_state(self):
        try:
            with open(STATE_FILE, "w") as f:
                json.dump({
                    "active": self.active,
                    "activated_at": self.activated_at,
                    "expires_at": self.expires_at,
                    "alert_count": self.alert_count,
                    "saved_at": datetime.now().isoformat(),
                }, f, indent=2)
        except: pass

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {msg}")
        try:
            with open(EVENTS_FILE, "a") as f:
                f.write(f"[{ts}] {msg}\n")
        except: pass

    # ─────────────────────────────────────────
    #   ACTIVATION
    # ─────────────────────────────────────────
    def activate(self, reason):
        """فعال‌سازی Red Alert"""
        if self.active:
            # تمدید
            self.expires_at = (datetime.now() + 
                              timedelta(minutes=CONFIG["duration_minutes"])).isoformat()
            self.save_state()
            return

        self.active = True
        self.activated_at = datetime.now().isoformat()
        self.expires_at = (datetime.now() + 
                          timedelta(minutes=CONFIG["duration_minutes"])).isoformat()
        self.alert_count += 1

        self.log("🚨 RED ALERT ACTIVATED")
        self.log(f"   Reason: {reason}")
        self.log(f"   Duration: {CONFIG['duration_minutes']}min")

        self._notify(reason)
        self.save_state()

    def _deactivate(self, reason):
        """غیرفعال‌سازی"""
        if not self.active:
            return
        self.active = False
        self.log(f"🟢 Red Alert deactivated: {reason}")
        self._notify_deactivate(reason)
        self.save_state()

    def deactivate_manual(self):
        self._deactivate("manual")

    # ─────────────────────────────────────────
    #   EVENT TRACKING
    # ─────────────────────────────────────────
    def record_event(self, severity, event_type, ip=None):
        """ثبت یک رویداد"""
        with self.lock:
            event = {
                "ts": time.time(),
                "severity": severity,
                "type": event_type,
                "ip": ip,
            }
            self.events.append(event)

            # چک تریگرها
            self._check_triggers()

    def _check_triggers(self):
        """چک کِی فعال بشه"""
        if self.active:
            return

        now = time.time()
        last_5min = [e for e in self.events if now - e["ts"] < 300]

        # ۱. CRITICAL زیاد؟
        critical_count = sum(1 for e in last_5min if e["severity"] == "CRITICAL")
        if critical_count >= CONFIG["critical_in_5min"]:
            self.activate(f"{critical_count} CRITICAL in 5min")
            return

        # ۲. کل حملات؟
        if len(last_5min) >= CONFIG["attacks_in_5min"]:
            self.activate(f"{len(last_5min)} attacks in 5min")
            return

        # ۳. تنوع حمله؟
        types = set(e["type"] for e in last_5min)
        if len(types) >= CONFIG["attack_types_diversity"]:
            self.activate(f"{len(types)} attack types in 5min")
            return

    # ─────────────────────────────────────────
    #   NOTIFICATIONS
    # ─────────────────────────────────────────
    def _notify(self, reason):
        # Telegram
        if CONFIG["notify_telegram"] and TG:
            try:
                msg = (
                    "🚨🚨🚨 *RED ALERT MODE* 🚨🚨🚨\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"⚠️ *Reason:* {reason}\n"
                    f"⏰ *Duration:* {CONFIG['duration_minutes']} minutes\n"
                    f"📊 *Sensitivity:* {CONFIG['sensitivity_multiplier']}x\n\n"
                    "🛡️ *Actions:*\n"
                    "• Enhanced logging ON\n"
                    "• All alerts prioritized\n"
                    "• Voice alerts ON\n"
                    "• Aggressive blocking\n\n"
                    "🔄 *Recovery:*\n"
                    "`python3 layer10_red_alert.py deactivate`\n\n"
                    "⚠️ _System in high-alert mode_"
                )
                requests.post(
                    f"https://api.telegram.org/bot{TG}/sendMessage",
                    json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"},
                    timeout=10
                )
            except: pass

        # Voice
        if CONFIG["notify_voice"]:
            try:
                os.system('termux-tts-speak "Red alert activated. System in high alert mode" 2>/dev/null')
            except: pass

        # Vibrate
        if CONFIG["notify_vibrate"]:
            try:
                for _ in range(5):
                    os.system('termux-vibrate -d 500 2>/dev/null')
                    time.sleep(0.2)
            except: pass

    def _notify_deactivate(self, reason):
        if TG:
            try:
                msg = (
                    "🟢 *Red Alert Deactivated*\n\n"
                    f"Reason: {reason}\n"
                    f"Time: {datetime.now().strftime('%H:%M:%S')}"
                )
                requests.post(
                    f"https://api.telegram.org/bot{TG}/sendMessage",
                    json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"},
                    timeout=10
                )
            except: pass

    # ─────────────────────────────────────────
    #   WATCHER
    # ─────────────────────────────────────────
    def watch(self):
        qfile = os.path.join(BASE, "queue.jsonl")
        last_pos = 0

        print("🚨 L10 Red Alert Mode active")
        print(f"📊 Triggers:")
        print(f"   {CONFIG['critical_in_5min']}+ CRITICAL in 5min")
        print(f"   {CONFIG['attacks_in_5min']}+ attacks in 5min")
        print(f"   {CONFIG['attack_types_diversity']}+ attack types")
        print(f"⏱️  Duration: {CONFIG['duration_minutes']}min")
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
                        sev = e.get("severity", "INFO")
                        etype = e.get("event_type", "UNKNOWN")
                        ip = e.get("source_ip") or e.get("metadata", {}).get("source_ip")
                        
                        self.record_event(sev, etype, ip)
                    except: pass

                # چک انقضا
                if self.active and self.expires_at:
                    exp = datetime.fromisoformat(self.expires_at)
                    if datetime.now() > exp:
                        self._deactivate("expired")
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"⚠️ {e}")
                time.sleep(5)

    def status(self):
        icon = "🔴" if self.active else "🟢"
        print(f"\n🚨 L10 Red Alert Status")
        print(f"═══════════════════════════════")
        print(f"Status:      {icon} {'ACTIVE' if self.active else 'INACTIVE'}")
        print(f"Activated:   {self.activated_at or '-'}")
        print(f"Expires:     {self.expires_at or '-'}")
        print(f"Alert count: {self.alert_count}")
        print(f"Events:      {len(self.events)}")
        print()
        print(f"📊 Triggers:")
        print(f"   {CONFIG['critical_in_5min']}+ CRITICAL in 5min")
        print(f"   {CONFIG['attacks_in_5min']}+ attacks in 5min")
        print(f"   {CONFIG['attack_types_diversity']}+ types")

    def test(self):
        """تست"""
        print("🧪 Testing Red Alert\n")

        print("📍 Sending 5 CRITICAL events...")
        for i in range(5):
            self.record_event("CRITICAL", "TEST_ATTACK", f"1.2.3.{i}")
            time.sleep(0.1)

        print()
        self.status()

def main():
    if len(sys.argv) < 2:
        print("Usage: layer10_red_alert.py {watch|status|test|activate|deactivate}")
        return
    cmd = sys.argv[1]
    ra = RedAlert()

    if cmd == "watch": ra.watch()
    elif cmd == "status": ra.status()
    elif cmd == "test": ra.test()
    elif cmd == "activate": ra.activate("manual")
    elif cmd == "deactivate": ra.deactivate_manual()

if __name__ == "__main__":
    main()
