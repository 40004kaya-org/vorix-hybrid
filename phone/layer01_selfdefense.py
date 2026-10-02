#!/usr/bin/env python3
"""L01 — Self-Defense (Anti-Kill Protection)"""
import os, sys, json, time, subprocess, threading, signal
from datetime import datetime

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
STATE_FILE = os.path.join(BASE, "layer01_state.json")

try:
    import requests
    with open(os.path.join(HOME, "vorix/.tg-token")) as f:
        TG = f.read().strip()
except:
    TG = ""
CHAT = "175160049"

# فایل‌هایی که باید همیشه زنده باشن
PROTECTED = [
    "layer01_selfdefense",
    "layer02_threat_intel",
    "layer03_behavioral",
    "layer04_auto_block",
    "layer17_watchdog",
    "agent.py",
    "server.py",
]

CONFIG = {
    "check_interval": 20,
    "max_restarts_per_hour": 30,
}

class SelfDefense:
    def __init__(self):
        self.restart_log = {}
        self.stats = {"checks": 0, "restarts": 0, "kill_attempts": 0, "started": time.time()}
        self.load_state()
        # Signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def load_state(self):
        try:
            with open(STATE_FILE) as f:
                s = json.load(f)
                self.stats = s.get("stats", self.stats)
        except: pass

    def save_state(self):
        try:
            with open(STATE_FILE, "w") as f:
                json.dump({"stats": self.stats}, f, indent=2)
        except: pass

    def _signal_handler(self, signum, frame):
        """اگر کسی سعی کرد ما رو بکشه"""
        self.stats["kill_attempts"] += 1
        self.save_state()
        self._alert(f"Kill attempt blocked! Signal: {signum}")
        # نادیده بگیر
        print(f"🛡️  Kill attempt blocked: signal {signum}")

    def is_running(self, name):
        try:
            r = subprocess.run(["pgrep", "-f", name], capture_output=True, timeout=3)
            return r.returncode == 0
        except:
            return False

    def restart_service(self, name):
        now = time.time()
        # چک rate limit
        if name not in self.restart_log:
            self.restart_log[name] = []
        self.restart_log[name] = [t for t in self.restart_log[name] if now - t < 3600]
        
        if len(self.restart_log[name]) >= CONFIG["max_restarts_per_hour"]:
            self._alert(f"⚠️ Too many restarts: {name}")
            return False
        
        self.restart_log[name].append(now)
        
        # راه‌اندازی
        script = f"{BASE}/{name}.py" if not name.endswith(".py") else f"{BASE}/{name}"
        if not os.path.exists(script):
            return False
        
        os.system(f"cd {BASE} && nohup python3 {name}.py > /dev/null 2>&1 &")
        self.stats["restarts"] += 1
        return True

    def _alert(self, msg):
        if not TG: return
        try:
            requests.post(
                f"https://api.telegram.org/bot{TG}/sendMessage",
                json={"chat_id": CHAT, "text": f"🛡️ *Self-Defense*\n\n{msg}",
                      "parse_mode": "Markdown"},
                timeout=10
            )
        except: pass

    def watch(self):
        print("🛡️  L01 Self-Defense active")
        print(f"📊 Protected: {len(PROTECTED)} services")
        print(f"⏱️  Check every {CONFIG['check_interval']}s\n")

        while True:
            try:
                self.stats["checks"] += 1
                for svc in PROTECTED:
                    if not self.is_running(svc):
                        print(f"⚠️ {svc} is dead — restarting")
                        if self.restart_service(svc):
                            print(f"   ✅ {svc} restarted")
                            self._alert(f"Restarted: {svc}")
                
                self.save_state()
                time.sleep(CONFIG["check_interval"])
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"⚠️ {e}")
                time.sleep(10)

    def status(self):
        uptime = int(time.time() - self.stats["started"])
        print(f"\n🛡️  L01 Self-Defense")
        print(f"═══════════════════════════════")
        print(f"Checks:         {self.stats['checks']}")
        print(f"Restarts:       {self.stats['restarts']}")
        print(f"Kill attempts:  {self.stats['kill_attempts']}")
        print(f"Uptime:         {uptime // 3600}h {(uptime // 60) % 60}m")
        print()
        print(f"📊 Protected:")
        for svc in PROTECTED:
            icon = "✅" if self.is_running(svc) else "❌"
            print(f"   {icon} {svc}")


def main():
    if len(sys.argv) < 2:
        print("Usage: layer01_selfdefense.py {watch|status}")
        return
    cmd = sys.argv[1]
    sd = SelfDefense()
    if cmd == "watch": sd.watch()
    elif cmd == "status": sd.status()

if __name__ == "__main__":
    main()
