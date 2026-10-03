#!/usr/bin/env python3
"""L4 — Auto-Block Engine"""
import os, sys, json, time, threading
from datetime import datetime, timedelta
from collections import defaultdict

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
BLOCKLIST = os.path.join(BASE, "blocklist.json")
STATE_FILE = os.path.join(BASE, "layer04_state.json")

sys.path.insert(0, BASE)
from layer02_threat_intel import INTEL

try:
    import requests
    with open(os.path.join(HOME, "vorix/.tg-token")) as f:
        TG = f.read().strip()
except:
    TG = ""
CHAT = "175160049"

CONFIG = {
    "auto_block_score": 70,       # امتیاز ۷۰+ → بلاک خودکار
    "temp_block_hours": 24,        # بلاک موقت ۲۴ ساعت
    "perm_block_score": 90,        # امتیاز ۹۰+ → بلاک دائمی
    "check_interval": 60,
}

PRIVATE = ("127.", "10.", "192.168.", "172.16.", "172.17.", "172.18.",
           "172.19.", "172.20.", "172.21.", "172.22.", "172.23.",
           "172.24.", "172.25.", "172.26.", "172.27.", "172.28.",
           "172.29.", "172.30.", "172.31.", "169.254.")

class AutoBlock:
    def __init__(self):
        self.blocked = self._load(BLOCKLIST)
        self.events = []
        self.lock = threading.Lock()

    def _load(self, path):
        try:
            with open(path) as f:
                return json.load(f)
        except:
            return {}

    def _save(self, path, data):
        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        except: pass

    def is_private(self, ip):
        return any(ip.startswith(p) for p in PRIVATE)

    def is_blocked(self, ip):
        if ip not in self.blocked: return False
        entry = self.blocked[ip]
        # چک انقضا
        if entry.get("type") == "temp":
            try:
                exp = datetime.fromisoformat(entry["expires"])
                if datetime.now() > exp:
                    del self.blocked[ip]
                    self._save(BLOCKLIST, self.blocked)
                    return False
            except: pass
        return True

    def block(self, ip, reason, score=0, ip_type="temp"):
        if self.is_private(ip) or self.is_blocked(ip):
            return False

        entry = {
            "blocked_at": datetime.now().isoformat(),
            "reason": reason,
            "score": score,
            "type": ip_type,
        }
        if ip_type == "temp":
            exp = datetime.now() + timedelta(hours=CONFIG["temp_block_hours"])
            entry["expires"] = exp.isoformat()

        self.blocked[ip] = entry
        self._save(BLOCKLIST, self.blocked)
        self._alert_block(ip, reason, score, ip_type)
        return True

    def unblock(self, ip):
        if ip in self.blocked:
            del self.blocked[ip]
            self._save(BLOCKLIST, self.blocked)
            return True
        return False

    def process_ip(self, ip):
        """پردازش یک IP و تصمیم‌گیری"""
        if not ip or self.is_private(ip):
            return {"action": "allow", "reason": "private"}

        if self.is_blocked(ip):
            return {"action": "block", "reason": "in_blocklist"}

        # Threat Intel check
        r = INTEL.check(ip)
        score = r.get("score", 0)

        if score >= CONFIG["perm_block_score"]:
            self.block(ip, f"threat_score_{score}", score, "perm")
            return {"action": "block", "reason": "perm_threat", "score": score}
        elif score >= CONFIG["auto_block_score"]:
            self.block(ip, f"threat_score_{score}", score, "temp")
            return {"action": "block", "reason": "temp_threat", "score": score}
        elif score >= 40:
            return {"action": "monitor", "reason": "suspicious", "score": score}
        else:
            return {"action": "allow", "score": score}

    def _alert_block(self, ip, reason, score, ip_type):
        if not TG: return
        try:
            icon = "🔴" if ip_type == "perm" else "🚫"
            msg = (
                f"{icon} *Auto-Block*\n\n"
                f"IP: `{ip}`\n"
                f"Type: `{ip_type}`\n"
                f"Score: `{score}`\n"
                f"Reason: `{reason}`\n"
                f"Time: {datetime.now().strftime('%H:%M:%S')}"
            )
            requests.post(
                f"https://api.telegram.org/bot{TG}/sendMessage",
                json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
        except: pass

    def watch_queue(self):
        """پایش queue.jsonl و بلاک خودکار"""
        qfile = os.path.join(BASE, "queue.jsonl")
        last_pos = 0

        print(f"👁️ Auto-Block Watcher active")
        print(f"🎯 Threshold: {CONFIG['auto_block_score']}/100")
        print(f"⏱️  Temp block: {CONFIG['temp_block_hours']}h")
        print(f"🔒 Perm block: {CONFIG['perm_block_score']}/100")
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
                        ip = e.get("source_ip") or e.get("metadata", {}).get("source_ip")
                        if ip:
                            result = self.process_ip(ip)
                            if result["action"] == "block":
                                print(f"🚫 BLOCKED: {ip} ({result['reason']})")
                    except: pass
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"⚠️ {e}")
                time.sleep(5)

    def status(self):
        active = sum(1 for ip in self.blocked if self.is_blocked(ip))
        perm = sum(1 for ip in self.blocked if self.blocked[ip].get("type") == "perm")
        temp = active - perm
        print(f"\n🚫 Auto-Block Status")
        print(f"═══════════════════════════")
        print(f"Total blocked: {active}")
        print(f"   🔴 Permanent: {perm}")
        print(f"   🚫 Temporary: {temp}")
        print(f"\n📋 Recent (last 10):")
        items = sorted(self.blocked.items(), key=lambda x: x[1].get("blocked_at", ""), reverse=True)[:10]
        for ip, info in items:
            icon = "🔴" if info.get("type") == "perm" else "🚫"
            print(f"   {icon} {ip:<18} score={info.get('score', '?')}")

def main():
    if len(sys.argv) < 2:
        print("Usage: layer04_auto_block.py {watch|status|block <ip>|unblock <ip>|list}")
        return
    cmd = sys.argv[1]
    ab = AutoBlock()

    if cmd == "watch": ab.watch_queue()
    elif cmd == "status": ab.status()
    elif cmd == "block" and len(sys.argv) > 2:
        ip = sys.argv[2]
        if ab.block(ip, "manual", 100, "perm"):
            print(f"✅ Blocked: {ip}")
        else:
            print(f"⚠️ Already blocked or private")
    elif cmd == "unblock" and len(sys.argv) > 2:
        ip = sys.argv[2]
        if ab.unblock(ip):
            print(f"✅ Unblocked: {ip}")
        else:
            print(f"⚠️ Not blocked")
    elif cmd == "list":
        ab.status()

if __name__ == "__main__":
    main()
