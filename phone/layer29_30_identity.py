#!/usr/bin/env python3
"""L29-L30 — Identity Chain (Credential Stuffing + Login Analyzer)"""
import os, sys, json, time, threading
from datetime import datetime, timedelta
from collections import defaultdict, deque

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
STATE_FILE = os.path.join(BASE, "layer29_30_state.json")

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
    "window_minutes": 5,           # پنجره پایش
    # L29 — Credential Stuffing
    "usernames_per_ip": 5,         # ۵+ یوزرنیم از یک IP → مشکوک
    "usernames_per_ip_block": 10,  # ۱۰+ → بلاک
    # L30 — Login Analyzer
    "ips_per_username": 3,         # ۳+ IP برای یک یوزرنیم → مشکوک
    "ips_per_username_block": 5,   # ۵+ → بلاک
    "failed_per_ip": 10,           # ۱۰+ لاگین ناموفق → بلاک
    "failed_per_username": 20,     # ۲۰+ برای یک یوزرنیم → بلاک
    # Timing
    "fast_login_ms": 500,          # کمتر از ۵۰۰ms بین دو لاگین = bot
    "fast_login_count": 5,         # ۵ بار متوالی = بلاک
}

PRIVATE = ("127.", "10.", "192.168.", "172.")

class IdentityChain:
    def __init__(self):
        # ip → [usernames]
        self.ip_usernames = defaultdict(list)
        # username → [ips]
        self.username_ips = defaultdict(list)
        # ip → [failed_timestamps]
        self.ip_failed = defaultdict(list)
        # username → [failed_timestamps]
        self.username_failed = defaultdict(list)
        # ip → [login_timestamps] for timing
        self.ip_login_times = defaultdict(deque)
        
        self.ab = AutoBlock()
        self.lock = threading.Lock()
        self.stats = {
            "total_logins": 0,
            "failed_logins": 0,
            "credential_stuffing": 0,
            "brute_force": 0,
            "timing_attacks": 0,
            "started": time.time(),
        }
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

    def is_private(self, ip):
        return any(ip.startswith(p) for p in PRIVATE)

    def cleanup(self):
        """پاک کردن رکوردهای قدیمی (بیشتر از ۱ ساعت)"""
        now = time.time()
        cutoff = now - 3600
        for d in [self.ip_usernames, self.username_ips]:
            for k in list(d.keys()):
                d[k] = [x for x in d[k] if x[1] > cutoff] if d[k] and isinstance(d[k][0], tuple) else d[k]
                if not d[k]:
                    del d[k]
        for d in [self.ip_failed, self.username_failed]:
            for k in list(d.keys()):
                d[k] = [t for t in d[k] if t > cutoff]
                if not d[k]:
                    del d[k]

    # ─────────────────────────────────────────
    #   MAIN CHECK — هر لاگین
    # ─────────────────────────────────────────
    def process_login(self, ip, username, success):
        """پردازش یک لاگین"""
        if not ip or not username:
            return {"action": "allow", "reason": "invalid"}
        
        if self.is_private(ip):
            return {"action": "allow", "reason": "private"}

        now = time.time()
        window = CONFIG["window_minutes"] * 60

        with self.lock:
            self.stats["total_logins"] += 1
            if not success:
                self.stats["failed_logins"] += 1

            # ─── L29 Credential Stuffing ───
            # اضافه یوزرنیم به رکورد IP
            self.ip_usernames[ip].append((username, now))
            self.ip_usernames[ip] = [
                (u, t) for u, t in self.ip_usernames[ip] if now - t < window
            ]

            unique_users = set(u for u, t in self.ip_usernames[ip])
            user_count = len(unique_users)

            if user_count >= CONFIG["usernames_per_ip_block"]:
                self.stats["credential_stuffing"] += 1
                self.ab.block(ip, f"cred_stuffing_{user_count}_users", score=85, ip_type="temp")
                self._alert(ip, username, "CREDENTIAL_STUFFING", 
                          f"IP tried {user_count} usernames", "BLOCKED")
                return {"action": "block", "reason": "credential_stuffing", 
                       "users": user_count}
            
            if user_count >= CONFIG["usernames_per_ip"]:
                self._alert(ip, username, "CREDENTIAL_STUFFING",
                          f"IP tried {user_count} usernames", "WARN")

            # ─── L30 Login Analyzer ───
            # اضافه IP به رکورد یوزرنیم
            self.username_ips[username].append((ip, now))
            self.username_ips[username] = [
                (i, t) for i, t in self.username_ips[username] if now - t < window
            ]

            unique_ips = set(i for i, t in self.username_ips[username])
            ip_count = len(unique_ips)

            if ip_count >= CONFIG["ips_per_username_block"]:
                self.stats["brute_force"] += 1
                # همه IPهایی که این یوزرنیم رو امتحان کردن بلاک بشن
                for bad_ip in unique_ips:
                    if not self.is_private(bad_ip):
                        self.ab.block(bad_ip, f"distributed_bruteforce_{ip_count}_ips",
                                     score=80, ip_type="temp")
                self._alert(ip, username, "DISTRIBUTED_BRUTE_FORCE",
                          f"Username attacked from {ip_count} IPs", "BLOCKED")
                return {"action": "block", "reason": "distributed_bruteforce"}

            # ─── Failed logins per IP ───
            if not success:
                self.ip_failed[ip].append(now)
                self.ip_failed[ip] = [
                    t for t in self.ip_failed[ip] if now - t < window
                ]
                if len(self.ip_failed[ip]) >= CONFIG["failed_per_ip"]:
                    self.stats["brute_force"] += 1
                    self.ab.block(ip, f"bruteforce_{len(self.ip_failed[ip])}_fails",
                                 score=80, ip_type="temp")
                    self._alert(ip, username, "BRUTE_FORCE",
                              f"{len(self.ip_failed[ip])} failed logins", "BLOCKED")
                    return {"action": "block", "reason": "bruteforce"}

                # ─── Failed per username ───
                self.username_failed[username].append(now)
                self.username_failed[username] = [
                    t for t in self.username_failed[username] if now - t < window
                ]
                if len(self.username_failed[username]) >= CONFIG["failed_per_username"]:
                    self._alert(ip, username, "TARGETED_USER",
                              f"{len(self.username_failed[username])} fails for this user", "WARN")

            # ─── Timing Analysis ───
            self.ip_login_times[ip].append(now)
            if len(self.ip_login_times[ip]) > 10:
                self.ip_login_times[ip].popleft()

            times = list(self.ip_login_times[ip])
            if len(times) >= CONFIG["fast_login_count"]:
                intervals = [times[i+1] - times[i] for i in range(len(times)-1)]
                avg_ms = (sum(intervals) / len(intervals)) * 1000
                if avg_ms < CONFIG["fast_login_ms"]:
                    self.stats["timing_attacks"] += 1
                    self.ab.block(ip, f"bot_timing_{int(avg_ms)}ms", 
                                 score=75, ip_type="temp")
                    self._alert(ip, username, "BOT_TIMING",
                              f"Avg interval: {int(avg_ms)}ms (too fast)", "BLOCKED")
                    return {"action": "block", "reason": "bot_timing"}

        return {"action": "allow"}

    def _alert(self, ip, username, attack_type, detail, level):
        if not TG: return
        try:
            icon = {"CREDENTIAL_STUFFING": "🎯",
                    "DISTRIBUTED_BRUTE_FORCE": "🌐",
                    "BRUTE_FORCE": "🔨",
                    "TARGETED_USER": "⚠️",
                    "BOT_TIMING": "🤖"}.get(attack_type, "⚠️")
            
            level_icon = "🔴" if level == "BLOCKED" else "🟡"
            
            msg = (
                f"{level_icon} *{level}* — Identity Chain\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"{icon} Attack: `{attack_type}`\n"
                f"🌐 IP: `{ip}`\n"
                f"👤 Username: `{username}`\n"
                f"📊 Detail: {detail}\n"
                f"⏰ {datetime.now().strftime('%H:%M:%S')}"
            )
            requests.post(
                f"https://api.telegram.org/bot{TG}/sendMessage",
                json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
        except: pass

    # ─────────────────────────────────────────
    #   WATCHER — پایش queue
    # ─────────────────────────────────────────
    def watch(self):
        qfile = os.path.join(BASE, "queue.jsonl")
        last_pos = 0

        print("🔐 L29-L30 Identity Chain Watcher")
        print(f"📊 Thresholds:")
        print(f"   Users per IP:      {CONFIG['usernames_per_ip']} warn / {CONFIG['usernames_per_ip_block']} block")
        print(f"   IPs per user:      {CONFIG['ips_per_username']} warn / {CONFIG['ips_per_username_block']} block")
        print(f"   Failed per IP:     {CONFIG['failed_per_ip']} block")
        print(f"   Bot timing:        < {CONFIG['fast_login_ms']}ms avg")
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
                        # فقط event_type لاگین
                        etype = e.get("event_type", "").upper()
                        if "LOGIN" not in etype and "AUTH" not in etype:
                            continue
                        
                        meta = e.get("metadata", {})
                        ip = e.get("source_ip") or meta.get("source_ip") or meta.get("ip")
                        username = meta.get("username") or meta.get("user") or "unknown"
                        success = e.get("result", "").upper() in ("PASS", "ALLOW", "SUCCESS")
                        
                        if ip:
                            result = self.process_login(ip, username, success)
                            if result["action"] == "block":
                                print(f"🚫 {result['reason']}: {ip}")
                    except: pass

                self.cleanup()
                self.save_state()
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"⚠️ {e}")
                time.sleep(5)

    def status(self):
        uptime = int(time.time() - self.stats["started"])
        h, m = divmod(uptime // 60, 60)
        print(f"\n🔐 L29-L30 Identity Chain Status")
        print(f"═══════════════════════════════════")
        print(f"Uptime:              {h}h {m}m")
        print(f"Total logins:        {self.stats['total_logins']}")
        print(f"Failed logins:       {self.stats['failed_logins']}")
        print(f"Credential stuffing: {self.stats['credential_stuffing']}")
        print(f"Brute force:         {self.stats['brute_force']}")
        print(f"Timing attacks:      {self.stats['timing_attacks']}")
        print()
        print(f"📊 Active trackers:")
        print(f"   IPs tracked:     {len(self.ip_usernames)}")
        print(f"   Users tracked:   {len(self.username_ips)}")

    def test(self):
        """تست با سناریوهای حمله"""
        print("🧪 Testing Identity Chain\n")

        # Test 1: Credential Stuffing
        print("📍 Test 1: Credential Stuffing (1 IP, 10 usernames)")
        for i in range(12):
            r = self.process_login("1.2.3.4", f"user{i}", False)
            if r["action"] == "block":
                print(f"   ✅ Blocked at user {i+1}")
                break

        # Test 2: Brute Force (1 user, 10 IPs)
        print("\n📍 Test 2: Distributed Brute Force (10 IPs, 1 username)")
        self.ab.unblock("1.2.3.4")
        for i in range(8):
            ip = f"5.6.7.{i+10}"
            r = self.process_login(ip, "admin", False)
            if r["action"] == "block":
                print(f"   ✅ Blocked at IP {i+1}")
                break

        # Test 3: Timing Attack
        print("\n📍 Test 3: Bot Timing (fast logins)")
        for i in range(10):
            r = self.process_login("9.10.11.12", "someuser", True)
            time.sleep(0.05)  # 50ms
            if r["action"] == "block":
                print(f"   ✅ Blocked at login {i+1}")
                break

        print("\n✅ Tests complete\n")
        self.status()

def main():
    if len(sys.argv) < 2:
        print("Usage: layer29_30_identity.py {watch|status|test}")
        return
    cmd = sys.argv[1]
    ic = IdentityChain()

    if cmd == "watch": ic.watch()
    elif cmd == "status": ic.status()
    elif cmd == "test": ic.test()

if __name__ == "__main__":
    main()
