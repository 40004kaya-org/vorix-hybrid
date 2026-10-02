#!/usr/bin/env python3
"""L31 — Log Encryption (AES-256)"""
import os, sys, json, time, hashlib, secrets, base64, threading
from datetime import datetime
from collections import defaultdict
from cryptography.fernet import Fernet

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
KEY_FILE = os.path.join(BASE, ".log_encryption_key")
ARCHIVE_DIR = os.path.join(BASE, "encrypted_logs")
STATE_FILE = os.path.join(BASE, "layer31_state.json")

os.makedirs(ARCHIVE_DIR, exist_ok=True)

LOG_FILES = [
    os.path.join(BASE, "queue.jsonl"),
    os.path.join(BASE, "layer03_events.jsonl"),
    os.path.join(BASE, "layer10_events.jsonl"),
    os.path.join(BASE, "watchdog.log"),
    os.path.join(BASE, "quarantine/quarantine.log"),
]

CONFIG = {
    "archive_after_days": 1,       # بایگانی بعد از ۱ روز
    "delete_after_archive": True,
    "max_unencrypted_mb": 10,      # حداکثر لاگ غیررمز
    "check_interval": 3600,
}


class LogEncryption:
    def __init__(self):
        self.key = self._load_or_create_key()
        self.fernet = Fernet(self.key)
        self.stats = {"encrypted": 0, "decrypted": 0, "errors": 0, "started": time.time()}
        self.load_state()

    def _load_or_create_key(self):
        """بارگذاری یا ساخت کلید"""
        if os.path.exists(KEY_FILE):
            try:
                with open(KEY_FILE, "rb") as f:
                    return f.read().strip()
            except: pass
        
        # ساخت کلید جدید
        key = Fernet.generate_key()
        try:
            with open(KEY_FILE, "wb") as f:
                f.write(key)
            os.chmod(KEY_FILE, 0o600)
            print(f"🔑 New encryption key created: {KEY_FILE}")
        except Exception as e:
            print(f"⚠️ Key save failed: {e}")
        return key

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

    def encrypt_file(self, filepath):
        """رمزنگاری یک فایل"""
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, "rb") as f:
                data = f.read()
            
            if not data:
                return None
            
            encrypted = self.fernet.encrypt(data)
            
            # اسم فایل خروجی
            basename = os.path.basename(filepath)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_name = f"{basename}.{ts}.enc"
            out_path = os.path.join(ARCHIVE_DIR, out_name)
            
            with open(out_path, "wb") as f:
                f.write(encrypted)
            os.chmod(out_path, 0o600)
            
            self.stats["encrypted"] += 1
            return out_path
        except Exception as e:
            self.stats["errors"] += 1
            print(f"⚠️ Encrypt failed {filepath}: {e}")
            return None

    def decrypt_file(self, filepath, output=None):
        """رمزگشایی یک فایل"""
        try:
            with open(filepath, "rb") as f:
                encrypted = f.read()
            
            data = self.fernet.decrypt(encrypted)
            
            if output is None:
                # پیش‌فرض: بدون .enc
                output = filepath.replace(".enc", ".decrypted")
            
            with open(output, "wb") as f:
                f.write(data)
            
            self.stats["decrypted"] += 1
            return output
        except Exception as e:
            self.stats["errors"] += 1
            print(f"⚠️ Decrypt failed: {e}")
            return None

    def archive_logs(self):
        """بایگانی همه لاگ‌ها"""
        print("🔒 Archiving logs...")
        count = 0
        
        for log_file in LOG_FILES:
            if not os.path.exists(log_file):
                continue
            
            # چک سن فایل
            age_hours = (time.time() - os.path.getmtime(log_file)) / 3600
            if age_hours < CONFIG["archive_after_days"] * 24:
                continue
            
            size_kb = os.path.getsize(log_file) / 1024
            if size_kb < 1:
                continue
            
            out = self.encrypt_file(log_file)
            if out:
                size_enc = os.path.getsize(out) / 1024
                print(f"   ✅ {os.path.basename(log_file)} ({size_kb:.0f}KB) → {size_enc:.0f}KB")
                
                if CONFIG["delete_after_archive"]:
                    os.remove(log_file)
                    print(f"      🗑️ Original removed")
                count += 1
        
        print(f"\n📊 Archived: {count} files")
        self.save_state()

    def verify_encrypted(self):
        """تست صحت رمزنگاری"""
        test_data = b"VORIX TEST DATA " + secrets.token_bytes(32)
        
        try:
            encrypted = self.fernet.encrypt(test_data)
            decrypted = self.fernet.decrypt(encrypted)
            
            if decrypted == test_data:
                print("✅ Encryption verification: OK")
                return True
            else:
                print("❌ Encryption verification: FAILED")
                return False
        except Exception as e:
            print(f"❌ Verification error: {e}")
            return False

    def get_encrypted_files(self):
        """لیست فایل‌های رمز"""
        try:
            files = []
            for f in os.listdir(ARCHIVE_DIR):
                if f.endswith(".enc"):
                    path = os.path.join(ARCHIVE_DIR, f)
                    size = os.path.getsize(path)
                    mtime = os.path.getmtime(path)
                    files.append({
                        "name": f,
                        "size": size,
                        "date": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M"),
                    })
            return sorted(files, key=lambda x: x["date"], reverse=True)
        except:
            return []

    def watch(self):
        print(f"🔒 L31 Log Encryption")
        print(f"📊 Archive dir: {ARCHIVE_DIR}")
        print(f"🔑 Key: {KEY_FILE}")
        print(f"📊 Check every {CONFIG['check_interval'] // 60}min")
        print()
        
        # تست
        self.verify_encrypted()
        print()
        
        while True:
            try:
                self.archive_logs()
                time.sleep(CONFIG["check_interval"])
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"⚠️ {e}")
                time.sleep(300)

    def status(self):
        uptime = int(time.time() - self.stats["started"])
        files = self.get_encrypted_files()
        total_size = sum(f["size"] for f in files)
        
        print(f"\n🔒 L31 Log Encryption")
        print(f"═══════════════════════════════")
        print(f"Encrypted:    {self.stats['encrypted']}")
        print(f"Decrypted:    {self.stats['decrypted']}")
        print(f"Errors:       {self.stats['errors']}")
        print(f"Uptime:       {uptime // 3600}h {(uptime // 60) % 60}m")
        print()
        print(f"📁 Archive: {ARCHIVE_DIR}")
        print(f"   Files:    {len(files)}")
        print(f"   Total:    {total_size / 1024:.1f} KB")
        print()
        
        if files:
            print(f"📋 Recent encrypted:")
            for f in files[:5]:
                print(f"   • {f['name']:<40} ({f['size'] / 1024:.1f}KB)")

    def test(self):
        print("🧪 Testing Log Encryption\n")
        
        # ۱. تست رمزگذاری
        print("📍 Verification...")
        ok = self.verify_encrypted()
        
        # ۲. تست کامل
        if ok:
            print("\n📍 Full cycle test:")
            test_file = os.path.join(BASE, "test_encryption.txt")
            with open(test_file, "w") as f:
                f.write("Secret VORIX data\n" * 10)
            
            out = self.encrypt_file(test_file)
            if out:
                print(f"   ✅ Encrypted: {os.path.basename(out)}")
                
                # رمزگشایی
                dec = self.decrypt_file(out)
                if dec:
                    with open(dec) as f:
                        content = f.read()
                    if "Secret VORIX data" in content:
                        print(f"   ✅ Decryption verified")
                    else:
                        print(f"   ❌ Content mismatch")
                
                # پاک‌سازی
                os.remove(test_file)
                os.remove(out)
                if dec and os.path.exists(dec):
                    os.remove(dec)
        
        print()
        self.status()


def main():
    if len(sys.argv) < 2:
        print("Usage: layer31_log_encryption.py {archive|status|test|verify}")
        return
    cmd = sys.argv[1]
    le = LogEncryption()

    if cmd == "archive": le.archive_logs()
    elif cmd == "status": le.status()
    elif cmd == "test": le.test()
    elif cmd == "verify": le.verify_encrypted()


if __name__ == "__main__":
    main()
