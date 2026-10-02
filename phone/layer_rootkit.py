#!/usr/bin/env python3
"""L-Rootkit — Rootkit Detection"""
import os, sys, json, time, subprocess, threading
from datetime import datetime
from collections import defaultdict

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
STATE_FILE = os.path.join(BASE, "layer_rootkit_state.json")

sys.path.insert(0, BASE)
from layer04_auto_block import AutoBlock

try:
    import requests
    with open(os.path.join(HOME, "vorix/.tg-token")) as f:
        TG = f.read().strip()
except:
    TG = ""
CHAT = "175160049"

CONFIG = {
    "check_interval": 300,
    "suspicious_names": ["kworker", "kthread", "sys_", "kern_"],
}

class RootkitDetect:
    def __init__(self):
        self.known_pids = set()
        self.ab = AutoBlock()
        self.stats = {"checks": 0, "anomalies": 0, "started": time.time()}
        self.load_state()

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

    def get_processes(self):
        """لیست پروسه‌ها"""
        procs = {}
        try:
            for pid_dir in os.listdir("/proc"):
                if not pid_dir.isdigit():
                    continue
                pid = int(pid_dir)
                try:
                    with open(f"/proc/{pid}/cmdline") as f:
                        cmdline = f.read().replace("\x00", " ").strip()
                    with open(f"/proc/{pid}/comm") as f:
                        comm = f.read().strip()
                    procs[pid] = {"cmdline": cmdline, "comm": comm}
                except:
                    pass
        except: pass
        return procs

    def check_hidden_processes(self):
        """پروسه‌های مخفی"""
        anomalies = []
        proc_pids = set(self.get_processes().keys())
        
        # لیست PID ها از ps
        try:
            r = subprocess.run(["ps", "-eo", "pid"], capture_output=True, text=True, timeout=5)
            ps_pids = set()
            for line in r.stdout.split("\n")[1:]:
                try:
                    ps_pids.add(int(line.strip()))
                except: pass
            
            # PID هایی که در ps نیستن ولی در /proc هستن → مخفی
            hidden = proc_pids - ps_pids
            hidden = {p for p in hidden if p > 2}  # صرف‌نظر از kernel
            
            if hidden:
                anomalies.append(f"Hidden processes: {len(hidden)}")
        except: pass
        
        return anomalies

    def check_suspicious_processes(self):
        """پروسه‌های مشکوک"""
        anomalies = []
        procs = self.get_processes()
        
        for pid, info in procs.items():
            name = info["comm"].lower()
            cmdline = info["cmdline"].lower()
            
            # بررسی نام‌های مشکوک
            for sus in CONFIG["suspicious_names"]:
                if sus in name and pid > 100:
                    anomalies.append(f"Suspicious: PID {pid} ({name})")
                    break
            
            # مسیر مخفی (/) یا (tmp)
            if any(p in cmdline for p in ["/tmp/", "/dev/shm/", "/.hidden"]):
                anomalies.append(f"Hidden path: PID {pid} ({cmdline[:40]})")
        
        return anomalies

    def check_ld_preload(self):
        """LD_PRELOAD rootkit"""
        anomalies = []
        try:
            with open("/etc/ld.so.preload") as f:
                content = f.read().strip()
                if content:
                    anomalies.append(f"LD_PRELOAD set: {content[:50]}")
        except FileNotFoundError:
            pass
        except: pass
        return anomalies

    def check_kernel_modules(self):
        """ماژول‌های kernel"""
        anomalies = []
        try:
            r = subprocess.run(["lsmod"], capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                modules = r.stdout.split("\n")[1:]
                # چک ماژول‌های مشکوک
                for m in modules:
                    name = m.split()[0].lower() if m else ""
                    if any(s in name for s in ["hide", "root", "magic", "hook"]):
                        anomalies.append(f"Suspicious module: {name}")
        except: pass
        return anomalies

    def scan(self):
        """اسکن کامل"""
        self.stats["checks"] += 1
        anomalies = []
        
        anomalies.extend(self.check_hidden_processes())
        anomalies.extend(self.check_suspicious_processes())
        anomalies.extend(self.check_ld_preload())
        anomalies.extend(self.check_kernel_modules())
        
        if anomalies:
            self.stats["anomalies"] += len(anomalies)
            self._alert(anomalies)
        
        return anomalies

    def _alert(self, anomalies):
        if not TG: return
        try:
            lines = [f"   • {a}" for a in anomalies[:5]]
            msg = (
                f"🚨 *Rootkit Detected*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Anomalies: `{len(anomalies)}`\n\n" +
                "\n".join(lines) +
                f"\n\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            )
            requests.post(
                f"https://api.telegram.org/bot{TG}/sendMessage",
                json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
        except: pass

    def watch(self):
        print("🔍 L-Rootkit — Rootkit Detection")
        print(f"⏱️  Check every {CONFIG['check_interval']}s\n")
        
        while True:
            try:
                anomalies = self.scan()
                if anomalies:
                    print(f"🚨 {len(anomalies)} anomalies detected:")
                    for a in anomalies[:3]:
                        print(f"   • {a}")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Clean")
                
                self.save_state()
                time.sleep(CONFIG["check_interval"])
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"⚠️ {e}")
                time.sleep(60)

    def status(self):
        uptime = int(time.time() - self.stats["started"])
        print(f"\n🔍 L-Rootkit Detection")
        print(f"═══════════════════════════════")
        print(f"Checks:      {self.stats['checks']}")
        print(f"Anomalies:   {self.stats['anomalies']}")
        print(f"Uptime:      {uptime // 3600}h {(uptime // 60) % 60}m")
        print()
        print(f"📊 Current scan:")
        anomalies = self.scan()
        if anomalies:
            for a in anomalies:
                print(f"   🚨 {a}")
        else:
            print(f"   ✅ No anomalies")

    def test(self):
        print("🧪 Testing Rootkit Detection\n")
        print("📍 Hidden processes check...")
        hidden = self.check_hidden_processes()
        print(f"   Found: {len(hidden)}")
        
        print("\n📍 LD_PRELOAD check...")
        ld = self.check_ld_preload()
        print(f"   Found: {len(ld)}")
        
        print("\n📍 Suspicious names check...")
        sus = self.check_suspicious_processes()
        print(f"   Found: {len(sus)}")
        
        print()
        self.status()


def main():
    if len(sys.argv) < 2:
        print("Usage: layer_rootkit.py {watch|status|test|scan}")
        return
    cmd = sys.argv[1]
    rd = RootkitDetect()
    if cmd == "watch": rd.watch()
    elif cmd == "status": rd.status()
    elif cmd == "test": rd.test()
    elif cmd == "scan":
        anomalies = rd.scan()
        print(json.dumps(anomalies, indent=2))

if __name__ == "__main__":
    main()
