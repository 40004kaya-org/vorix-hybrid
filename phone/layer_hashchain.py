#!/usr/bin/env python3
"""L-HashChain — Tamper-proof log"""
import os, sys, json, time, hashlib, threading
from datetime import datetime

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
CHAIN_FILE = os.path.join(BASE, "hash_chain.jsonl")
STATE_FILE = os.path.join(BASE, "layer_hashchain_state.json")

try:
    import requests
    with open(os.path.join(HOME, "vorix/.tg-token")) as f:
        TG = f.read().strip()
except:
    TG = ""
CHAT = "175160049"


class HashChain:
    def __init__(self):
        self.last_hash = self._load_last_hash()
        self.stats = {"entries": 0, "verified": 0, "broken": 0, "started": time.time()}
        self.lock = threading.Lock()
        self.load_state()

    def _load_last_hash(self):
        """آخرین hash رو از فایل بارگذاری کن"""
        try:
            if not os.path.exists(CHAIN_FILE):
                return "0" * 64
            with open(CHAIN_FILE) as f:
                lines = f.readlines()
                if lines:
                    last = json.loads(lines[-1])
                    return last.get("hash", "0" * 64)
        except: pass
        return "0" * 64

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

    def add(self, event, source="unknown"):
        """اضافه رویداد به زنجیره"""
        with self.lock:
            entry = {
                "ts": datetime.now().isoformat(),
                "source": source,
                "event": str(event)[:500],
                "prev": self.last_hash,
            }
            # محاسبه hash
            content = json.dumps(entry, sort_keys=True, default=str)
            h = hashlib.sha256(content.encode()).hexdigest()
            entry["hash"] = h
            
            try:
                with open(CHAIN_FILE, "a") as f:
                    f.write(json.dumps(entry, default=str) + "\n")
                self.last_hash = h
                self.stats["entries"] += 1
                self.save_state()
                return h
            except Exception as e:
                print(f"⚠️ Chain write error: {e}")
                return None

    def verify(self):
        """بررسی کل زنجیره"""
        with self.lock:
            if not os.path.exists(CHAIN_FILE):
                return True, 0
            
            try:
                with open(CHAIN_FILE) as f:
                    prev = "0" * 64
                    count = 0
                    for line in f:
                        line = line.strip()
                        if not line: continue
                        entry = json.loads(line)
                        
                        # چک prev
                        if entry.get("prev") != prev:
                            self.stats["broken"] += 1
                            return False, count
                        
                        # محاسبه مجدد hash
                        test = {
                            "ts": entry["ts"],
                            "source": entry["source"],
                            "event": entry["event"],
                            "prev": entry["prev"],
                        }
                        content = json.dumps(test, sort_keys=True, default=str)
                        expected = hashlib.sha256(content.encode()).hexdigest()
                        
                        if expected != entry.get("hash"):
                            self.stats["broken"] += 1
                            return False, count
                        
                        prev = entry["hash"]
                        count += 1
                    
                    self.stats["verified"] += 1
                    return True, count
            except Exception as e:
                print(f"⚠️ Verify error: {e}")
                return False, 0

    def status(self):
        uptime = int(time.time() - self.stats["started"])
        valid, count = self.verify()
        size_kb = os.path.getsize(CHAIN_FILE) / 1024 if os.path.exists(CHAIN_FILE) else 0
        
        print(f"\n⛓️  L-HashChain")
        print(f"═══════════════════════════════")
        print(f"Entries:     {self.stats['entries']}")
        print(f"Chain size:  {count} entries")
        print(f"File:        {size_kb:.1f} KB")
        print(f"Valid:       {'✅ Yes' if valid else '🔴 BROKEN'}")
        print(f"Uptime:      {uptime // 3600}h {(uptime // 60) % 60}m")

    def test(self):
        print("🧪 Testing Hash Chain\n")
        
        # ۱. اضافه چند رویداد
        print("📍 Adding 3 events...")
        for i in range(3):
            h = self.add(f"Test event {i+1}", source="test")
            print(f"   ✅ Hash: {h[:16]}...")
        
        # ۲. بررسی
        print("\n📍 Verifying chain...")
        valid, count = self.verify()
        print(f"   Chain: {'✅ Valid' if valid else '🔴 Broken'}")
        print(f"   Count: {count}")
        
        print()
        self.status()


def main():
    if len(sys.argv) < 2:
        print("Usage: layer_hashchain.py {verify|status|test|add <msg>}")
        return
    cmd = sys.argv[1]
    hc = HashChain()
    if cmd == "verify":
        valid, count = hc.verify()
        print(f"Valid: {valid}, Entries: {count}")
    elif cmd == "status": hc.status()
    elif cmd == "test": hc.test()
    elif cmd == "add" and len(sys.argv) > 2:
        hc.add(" ".join(sys.argv[2:]), source="cli")

if __name__ == "__main__":
    main()
