#!/usr/bin/env python3
"""L17 — Self-Healing Watchdog"""
import os, sys, json, time, subprocess, threading
from datetime import datetime
from collections import defaultdict

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
STATE_FILE = os.path.join(BASE, "watchdog_state.json")
LOG_FILE = os.path.join(BASE, "watchdog.log")

try:
    import requests
    with open(os.path.join(HOME, "vorix/.tg-token")) as f:
        TG = f.read().strip()
except:
    TG = ""
CHAT = "175160049"

CONFIG = {
    "check_interval": 30,
    "restart_threshold": 3,
    "killswitch_threshold": 5,
    "max_restarts_per_hour": 20,
}

SERVICES = {
    "phone-agent": {
        "pattern": "agent.py",
        "command": "cd ~/vorix-hybrid/phone && nohup python3 agent.py > /dev/null 2>&1 &",
    },
    "dashboard": {
        "pattern": "server.py",
        "command": "cd ~/vorix/dashboard && nohup python3 server.py > /dev/null 2>&1 &",
    },
    "sentinel": {
        "pattern": "sentinel.py",
        "command": "cd ~/vorix && nohup python3 sentinel.py > /dev/null 2>&1 &",
    },
}

class Watchdog:
    def __init__(self):
        self.restart_counts = defaultdict(list)
        self.crash_counts = defaultdict(int)
        self.start_time = time.time()
        self.total_restarts = 0
        self.load_state()

    def load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE) as f:
                    s = json.load(f)
                    self.total_restarts = s.get("total_restarts", 0)
            except:
                pass

    def save_state(self):
        try:
            with open(STATE_FILE, "w") as f:
                json.dump({
                    "total_restarts": self.total_restarts,
                    "saved_at": datetime.now().isoformat(),
                }, f, indent=2)
        except:
            pass

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line)
        try:
            with open(LOG_FILE, "a") as f:
                f.write(line + "\n")
        except:
            pass

    def is_running(self, pattern):
        try:
            r = subprocess.run(["pgrep", "-f", pattern],
                             capture_output=True, timeout=5)
            return r.returncode == 0
        except:
            return False

    def start_service(self, name, svc):
        try:
            self.log(f"🚀 Restarting: {name}")
            os.system(svc["command"])
            time.sleep(3)
            if self.is_running(svc["pattern"]):
                self.log(f"✅ {name} started")
                return True
            self.log(f"❌ {name} failed")
            return False
        except Exception as e:
            self.log(f"⚠️ {name} error: {e}")
            return False

    def can_restart(self, name):
        now = time.time()
        self.restart_counts[name] = [
            t for t in self.restart_counts[name] if now - t < 3600
        ]
        return len(self.restart_counts[name]) < CONFIG["max_restarts_per_hour"]

    def record_restart(self, name):
        self.restart_counts[name].append(time.time())
        self.crash_counts[name] += 1
        self.total_restarts += 1
        self.save_state()

    def check_all(self):
        for name, svc in SERVICES.items():
            if self.is_running(svc["pattern"]):
                if name in self.crash_counts:
                    self.crash_counts[name] = 0
                continue

            self.log(f"⚠️ {name} is DOWN")

            if not self.can_restart(name):
                self._alert_limit(name)
                continue

            if self.start_service(name, svc):
                self.record_restart(name)
                crashes = self.crash_counts[name]
                if crashes >= CONFIG["killswitch_threshold"]:
                    self.log(f"🔴 Kill Switch trigger: {name}")
                    self._trigger_killswitch(name, crashes)
                elif crashes >= CONFIG["restart_threshold"]:
                    self._alert_crashes(name, crashes)

    def _alert_crashes(self, name, count):
        if not TG: return
        try:
            msg = f"⚠️ *Watchdog*\n\nService: `{name}`\nCrashes: `{count}`\nAuto-restarted"
            requests.post(f"https://api.telegram.org/bot{TG}/sendMessage",
                json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"},
                timeout=10)
        except: pass

    def _alert_limit(self, name):
        if not TG: return
        try:
            msg = f"🔴 *Watchdog Limit*\n\nService: `{name}`\nToo many restarts"
            requests.post(f"https://api.telegram.org/bot{TG}/sendMessage",
                json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"},
                timeout=10)
        except: pass

    def _trigger_killswitch(self, name, crashes):
        try:
            from layer16_killswitch import KillSwitch
            ks = KillSwitch()
            ks.manual_trigger(f"Watchdog: {name} crashed {crashes} times")
        except Exception as e:
            self.log(f"⚠️ KS call failed: {e}")

    def run(self):
        print("🐕 L17 — Self-Healing Watchdog")
        print(f"📊 Monitoring {len(SERVICES)} services")
        for name, svc in SERVICES.items():
            status = "✅" if self.is_running(svc["pattern"]) else "❌"
            print(f"   {status} {name}")
        print()
        while True:
            try:
                self.check_all()
                time.sleep(CONFIG["check_interval"])
            except KeyboardInterrupt:
                print("\n⏹ Stopped")
                sys.exit(0)
            except Exception as e:
                self.log(f"⚠️ {e}")
                time.sleep(10)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 layer17_watchdog.py {watch|status|once}")
        return
    cmd = sys.argv[1]
    wd = Watchdog()
    if cmd == "watch":
        wd.run()
    elif cmd == "status":
        print(f"🐕 Watchdog Status")
        print(f"Total restarts: {wd.total_restarts}\n")
        for name, svc in SERVICES.items():
            status = "✅ RUN" if wd.is_running(svc["pattern"]) else "❌ DOWN"
            crashes = wd.crash_counts.get(name, 0)
            print(f"   {status}  {name:<15} crashes: {crashes}")
    elif cmd == "once":
        wd.check_all()

if __name__ == "__main__":
    main()
