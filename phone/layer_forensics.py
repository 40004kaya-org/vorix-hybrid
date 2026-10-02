#!/usr/bin/env python3
"""L-Forensics — Attack Evidence Storage"""
import os, sys, json, time, hashlib, shutil, subprocess, threading
from datetime import datetime

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
FORENSICS_DIR = os.path.join(BASE, "forensics")
STATE_FILE = os.path.join(BASE, "layer_forensics_state.json")

os.makedirs(FORENSICS_DIR, exist_ok=True)

try:
    import requests
    with open(os.path.join(HOME, "vorix/.tg-token")) as f:
        TG = f.read().strip()
except:
    TG = ""
CHAT = "175160049"


class Forensics:
    def __init__(self):
        self.stats = {"collected": 0, "size_kb": 0, "started": time.time()}
        self.lock = threading.Lock()
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

    def collect_evidence(self, attack_type, ip, extra_data=None):
        """جمع‌آوری شواهد"""
        with self.lock:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            case_dir = os.path.join(FORENSICS_DIR, f"case_{ts}_{attack_type}")
            
            try:
                os.makedirs(case_dir, exist_ok=True)
                
                # ۱. اطلاعات پایه
                info = {
                    "timestamp": datetime.now().isoformat(),
                    "attack_type": attack_type,
                    "source_ip": ip,
                    "extra": extra_data or {},
                }
                with open(os.path.join(case_dir, "info.json"), "w") as f:
                    json.dump(info, f, indent=2)
                
                # ۲. شبکه
                try:
                    r = subprocess.run(["netstat", "-tun"], capture_output=True, text=True, timeout=5)
                    with open(os.path.join(case_dir, "netstat.txt"), "w") as f:
                        f.write(r.stdout)
                except: pass
                
                # ۳. پروسه‌ها
                try:
                    r = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=5)
                    with open(os.path.join(case_dir, "processes.txt"), "w") as f:
                        f.write(r.stdout)
                except: pass
                
                # ۴. لاگ‌ها
                try:
                    for log in ["queue.jsonl", "layer03_events.jsonl", "watchdog.log"]:
                        log_path = os.path.join(BASE, log)
                        if os.path.exists(log_path):
                            shutil.copy2(log_path, case_dir)
                except: pass
                
                # ۵. hash
                case_hash = self._hash_case(case_dir)
                with open(os.path.join(case_dir, "case.hash"), "w") as f:
                    f.write(case_hash)
                
                self.stats["collected"] += 1
                self.save_state()
                
                self._alert(case_dir, attack_type, ip, case_hash)
                return case_dir
                
            except Exception as e:
                print(f"⚠️ Forensics error: {e}")
                return None

    def _hash_case(self, case_dir):
        """hash کل case"""
        h = hashlib.sha256()
        for root, _, files in os.walk(case_dir):
            for fname in sorted(files):
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "rb") as fp:
                        h.update(fp.read())
                except: pass
        return h.hexdigest()

    def _alert(self, case_dir, attack_type, ip, case_hash):
        if not TG: return
        try:
            size = sum(os.path.getsize(os.path.join(dp, f))
                      for dp, _, fs in os.walk(case_dir) for f in fs) / 1024
            msg = (
                f"🔬 *Forensics Collected*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Attack: `{attack_type}`\n"
                f"IP: `{ip}`\n"
                f"Size: `{size:.1f} KB`\n"
                f"Hash: `{case_hash[:16]}...`\n\n"
                f"📁 `{os.path.basename(case_dir)}`\n"
                f"⏰ {datetime.now().strftime('%H:%M:%S')}"
            )
            requests.post(
                f"https://api.telegram.org/bot{TG}/sendMessage",
                json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
        except: pass

    def list_cases(self):
        """لیست cases"""
        try:
            cases = []
            for d in os.listdir(FORENSICS_DIR):
                path = os.path.join(FORENSICS_DIR, d)
                if os.path.isdir(path):
                    size = sum(os.path.getsize(os.path.join(dp, f))
                              for dp, _, fs in os.walk(path) for f in fs)
                    cases.append({
                        "name": d,
                        "size": size,
                        "mtime": os.path.getmtime(path),
                    })
            return sorted(cases, key=lambda x: x["mtime"], reverse=True)
        except:
            return []

    def status(self):
        uptime = int(time.time() - self.stats["started"])
        cases = self.list_cases()
        total_size = sum(c["size"] for c in cases) / 1024
        
        print(f"\n🔬 L-Forensics")
        print(f"═══════════════════════════════")
        print(f"Cases:       {len(cases)}")
        print(f"Total size:  {total_size:.1f} KB")
        print(f"Uptime:      {uptime // 3600}h {(uptime // 60) % 60}m")
        print()
        if cases:
            print(f"📋 Recent cases:")
            for c in cases[:5]:
                print(f"   • {c['name']} ({c['size']/1024:.1f}KB)")

    def test(self):
        print("🧪 Testing Forensics\n")
        
        print("📍 Collecting evidence...")
        case = self.collect_evidence(
            "TEST_ATTACK",
            "1.2.3.4",
            {"test": True, "reason": "unit test"}
        )
        
        if case:
            print(f"   ✅ Case: {os.path.basename(case)}")
            files = os.listdir(case)
            print(f"   📁 {len(files)} files collected")
            for f in files[:5]:
                print(f"      • {f}")
        
        print()
        self.status()


def main():
    if len(sys.argv) < 2:
        print("Usage: layer_forensics.py {list|status|test|collect <type> <ip>}")
        return
    cmd = sys.argv[1]
    fo = Forensics()
    if cmd == "list":
        for c in fo.list_cases():
            print(f"{c['name']} — {c['size']/1024:.1f}KB")
    elif cmd == "status": fo.status()
    elif cmd == "test": fo.test()
    elif cmd == "collect" and len(sys.argv) > 3:
        fo.collect_evidence(sys.argv[2], sys.argv[3])

if __name__ == "__main__":
    main()
