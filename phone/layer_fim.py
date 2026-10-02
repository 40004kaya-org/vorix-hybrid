#!/usr/bin/env python3
"""L-FIM — File Integrity Monitor"""
import os, sys, json, time, hashlib, threading, shutil
from datetime import datetime
from collections import defaultdict

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
BASELINE_FILE = os.path.join(BASE, "fim_baseline.json")
STATE_FILE = os.path.join(BASE, "fim_state.json")
BACKUP_DIR = os.path.join(BASE, "fim_backups")

os.makedirs(BACKUP_DIR, exist_ok=True)

try:
    import requests
    with open(os.path.join(HOME, "vorix/.tg-token")) as f:
        TG = f.read().strip()
except:
    TG = ""
CHAT = "175160049"

CONFIG = {
    "check_interval": 300,
    "watch_files": [
        # خود VORIX
        "layer01_selfdefense.py",
        "layer02_threat_intel.py",
        "layer03_behavioral.py",
        "layer04_auto_block.py",
        "layer05_data_quarantine.py",
        "layer06_geoip_block.py",
        "layer08_network_monitor.py",
        "layer09_rate_limiter.py",
        "layer10_red_alert.py",
        "layer11_dns_sinkhole.py",
        "layer12_reverse_dns.py",
        "layer15_fingerprint.py",
        "layer16_killswitch.py",
        "layer17_watchdog.py",
        "layer18_backup_verifier.py",
        "layer21_ml_anomaly.py",
        "layer22_header_analysis.py",
        "layer23_cookie_anomaly.py",
        "layer24_session_hijack.py",
        "layer25_ssl_monitor.py",
        "layer26_hsts.py",
        "layer29_30_identity.py",
        "layer31_log_encryption.py",
        "layer_rootkit.py",
        "vorix-all",
    ],
}

class FIM:
    def __init__(self):
        self.baseline = self.load_baseline()
        self.stats = {"checks": 0, "modified": 0, "restored": 0, "started": time.time()}
        self.lock = threading.Lock()
        self.load_state()

    def load_baseline(self):
        try:
            with open(BASELINE_FILE) as f:
                return json.load(f)
        except:
            return {}

    def save_baseline(self):
        try:
            with open(BASELINE_FILE, "w") as f:
                json.dump(self.baseline, f, indent=2)
        except: pass

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

    def hash_file(self, path):
        """SHA-256 فایل"""
        try:
            with open(path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except:
            return None

    def create_baseline(self):
        """ساخت baseline اولیه"""
        print("📸 Creating FIM baseline...")
        self.baseline = {}
        count = 0
        
        for fname in CONFIG["watch_files"]:
            path = os.path.join(BASE, fname)
            if not os.path.exists(path):
                continue
            h = self.hash_file(path)
            if h:
                self.baseline[fname] = {
                    "hash": h,
                    "size": os.path.getsize(path),
                    "ts": time.time(),
                }
                # بک‌آپ
                backup = os.path.join(BACKUP_DIR, fname)
                try:
                    shutil.copy2(path, backup)
                except: pass
                count += 1
        
        self.save_baseline()
        print(f"✅ Baseline created: {count} files")

    def check_integrity(self):
        """چک integrity"""
        with self.lock:
            self.stats["checks"] += 1
            modified = []

            for fname, info in self.baseline.items():
                path = os.path.join(BASE, fname)
                if not os.path.exists(path):
                    modified.append((fname, "DELETED"))
                    continue
                
                h = self.hash_file(path)
                if h and h != info["hash"]:
                    modified.append((fname, "MODIFIED"))

            if modified:
                self.stats["modified"] += len(modified)
                for fname, status in modified:
                    self._restore_file(fname, status)
                    self._alert(fname, status)

            return modified

    def _restore_file(self, fname, status):
        """بازگردانی از بک‌آپ"""
        backup = os.path.join(BACKUP_DIR, fname)
        target = os.path.join(BASE, fname)
        
        if os.path.exists(backup):
            try:
                shutil.copy2(backup, target)
                self.stats["restored"] += 1
                print(f"   ✅ Restored: {fname}")
            except Exception as e:
                print(f"   ⚠️ Restore failed {fname}: {e}")

    def _alert(self, fname, status):
        if not TG: return
        try:
            icon = "🔴" if status == "DELETED" else "🟡"
            msg = (
                f"{icon} *File Integrity Alert*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"File: `{fname}`\n"
                f"Status: `{status}`\n"
                f"Action: Auto-restored\n"
                f"⏰ {datetime.now().strftime('%H:%M:%S')}"
            )
            requests.post(
                f"https://api.telegram.org/bot{TG}/sendMessage",
                json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
        except: pass

    def watch(self):
        print("🔒 L-FIM — File Integrity Monitor")
        print(f"📊 Watching: {len(self.baseline)} files")
        print(f"⏱️  Check every {CONFIG['check_interval']}s")
        print()
        
        if not self.baseline:
            print("⚠️ No baseline! Creating...")
            self.create_baseline()
        
        while True:
            try:
                modified = self.check_integrity()
                if modified:
                    print(f"🚨 {len(modified)} files modified:")
                    for f, s in modified:
                        print(f"   • {f}: {s}")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ All OK")
                
                self.save_state()
                time.sleep(CONFIG["check_interval"])
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"⚠️ {e}")
                time.sleep(60)

    def status(self):
        uptime = int(time.time() - self.stats["started"])
        print(f"\n🔒 L-FIM Status")
        print(f"═══════════════════════════════")
        print(f"Baseline:    {len(self.baseline)} files")
        print(f"Checks:      {self.stats['checks']}")
        print(f"Modified:    {self.stats['modified']}")
        print(f"Restored:    {self.stats['restored']}")
        print(f"Uptime:      {uptime // 3600}h {(uptime // 60) % 60}m")
        print()
        print(f"📁 Backups: {BACKUP_DIR}")

    def test(self):
        print("🧪 Testing FIM\n")
        
        # ساخت baseline اگر نبود
        if not self.baseline:
            self.create_baseline()
        
        # تست: تغییر یک فایل
        print("\n📍 Testing modification detection...")
        test_file = os.path.join(BASE, "layer16_killswitch.py")
        if os.path.exists(test_file):
            # ذخیره نسخه اصلی
            with open(test_file, "rb") as f:
                original = f.read()
            
            # اضافه یک خط
            with open(test_file, "a") as f:
                f.write("\n# TEST MODIFICATION\n")
            
            # چک
            modified = self.check_integrity()
            print(f"   Detected: {len(modified)} modifications")
            for f, s in modified:
                print(f"      • {f}: {s}")
            
            # بازگردانی
            print(f"   ✅ Auto-restored from baseline")
        
        print()
        self.status()


def main():
    if len(sys.argv) < 2:
        print("Usage: layer_fim.py {baseline|watch|status|test}")
        return
    cmd = sys.argv[1]
    fim = FIM()
    
    if cmd == "baseline": fim.create_baseline()
    elif cmd == "watch": fim.watch()
    elif cmd == "status": fim.status()
    elif cmd == "test": fim.test()

if __name__ == "__main__":
    main()
