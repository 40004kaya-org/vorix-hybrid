#!/usr/bin/env python3
"""L3 — Behavioral Analytics (Correlation Engine)"""
import os, sys, json, time, threading
from datetime import datetime, timedelta
from collections import defaultdict, deque

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
STATE_FILE = os.path.join(BASE, "layer03_state.json")
EVENTS_FILE = os.path.join(BASE, "layer03_events.jsonl")

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
    "window_minutes": 15,           # پنجره correlation
    "attack_chain_threshold": 3,    # ۳ نوع حمله مختلف از یک IP → زنجیره
    "repeat_offender_threshold": 5, # ۵ حمله از یک IP → بلاک
    "persistent_attacker_hours": 24, # ۲۴ ساعت پایش
    "correlate_users": True,
}

PRIVATE = ("127.", "10.", "192.168.", "172.")

# انواع حمله
ATTACK_TYPES = {
    "PORT_SCAN": {"weight": 1, "category": "recon"},
    "SQLI": {"weight": 3, "category": "exploit"},
    "SQL_INJECTION": {"weight": 3, "category": "exploit"},
    "BRUTE_FORCE": {"weight": 4, "category": "auth"},
    "CRED_STUFFING": {"weight": 4, "category": "auth"},
    "CREDENTIAL_STUFFING": {"weight": 4, "category": "auth"},
    "XSS": {"weight": 2, "category": "exploit"},
    "DDoS": {"weight": 5, "category": "dos"},
    "DOS": {"weight": 5, "category": "dos"},
    "MALWARE": {"weight": 5, "category": "malware"},
    "BACKDOOR": {"weight": 5, "category": "malware"},
    "DATA_EXFIL": {"weight": 5, "category": "exfil"},
    "EXFIL": {"weight": 5, "category": "exfil"},
    "PRIV_ESC": {"weight": 4, "category": "exploit"},
    "BOT_TIMING": {"weight": 3, "category": "automation"},
    "SUSPICIOUS_PROCESS": {"weight": 2, "category": "host"},
    "FILE_MODIFIED": {"weight": 2, "category": "host"},
}

class BehavioralAnalytics:
    def __init__(self):
        # ip → list of events
        self.ip_events = defaultdict(list)
        # username → list of events
        self.user_events = defaultdict(list)
        # زمان‌ها
        self.start_time = time.time()
        self.ab = AutoBlock()
        self.lock = threading.Lock()
        self.stats = {
            "total": 0,
            "chains_detected": 0,
            "repeat_offenders": 0,
            "cross_layer": 0,
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

    def classify_attack(self, event):
        """تشخیص نوع حمله"""
        etype = event.get("event_type", "").upper().replace(" ", "_")
        msg = event.get("message", "").upper()

        # مستقیم چک کن
        if etype in ATTACK_TYPES:
            return etype, ATTACK_TYPES[etype]

        # جستجو در متن
        for atype, info in ATTACK_TYPES.items():
            if atype in etype or atype in msg:
                return atype, info

        # کلمات کلیدی
        text = etype + " " + msg
        if "SQL" in text or "OR 1=1" in text:
            return "SQLI", ATTACK_TYPES["SQLI"]
        if "BRUTE" in text or "FAILED LOGIN" in text:
            return "BRUTE_FORCE", ATTACK_TYPES["BRUTE_FORCE"]
        if "SCAN" in text:
            return "PORT_SCAN", ATTACK_TYPES["PORT_SCAN"]
        if "DDOS" in text or "FLOOD" in text:
            return "DDoS", ATTACK_TYPES["DDoS"]

        return None, {"weight": 0, "category": "unknown"}

    def process_event(self, event):
        """پردازش یک رویداد"""
        with self.lock:
            self.stats["total"] += 1
            now = time.time()

            ip = event.get("source_ip") or event.get("metadata", {}).get("source_ip")
            username = event.get("metadata", {}).get("username") or event.get("metadata", {}).get("user")
            attack_type, info = self.classify_attack(event)

            if not attack_type or info["weight"] == 0:
                return

            if ip and not self.is_private(ip):
                # اضافه به تاریخچه IP
                self.ip_events[ip].append({
                    "ts": now,
                    "type": attack_type,
                    "category": info["category"],
                    "weight": info["weight"],
                    "severity": event.get("severity", "INFO"),
                })

                # پاک کردن قدیمی‌ها
                cutoff = now - (CONFIG["persistent_attacker_hours"] * 3600)
                self.ip_events[ip] = [
                    e for e in self.ip_events[ip] if e["ts"] > cutoff
                ]

                self._analyze_ip(ip, event)

            if username and CONFIG["correlate_users"]:
                self.user_events[username].append({
                    "ts": now,
                    "type": attack_type,
                    "ip": ip,
                })
                cutoff = now - (CONFIG["persistent_attacker_hours"] * 3600)
                self.user_events[username] = [
                    e for e in self.user_events[username] if e["ts"] > cutoff
                ]

    def _analyze_ip(self, ip, current_event):
        """تحلیل رفتار IP"""
        now = time.time()
        window = CONFIG["window_minutes"] * 60
        recent = [e for e in self.ip_events[ip] if now - e["ts"] < window]

        # ۱. Attack Chain — چند نوع حمله مختلف؟
        attack_types = set(e["type"] for e in recent)
        if len(attack_types) >= CONFIG["attack_chain_threshold"]:
            self.stats["chains_detected"] += 1
            self._alert_chain(ip, attack_types, recent, current_event)
            self.ab.block(ip, f"attack_chain_{len(attack_types)}_types",
                         score=90, ip_type="perm")

        # ۲. Repeat Offender — چند حمله از این IP؟
        total_attacks = len(recent)
        if total_attacks >= CONFIG["repeat_offender_threshold"]:
            self.stats["repeat_offenders"] += 1
            self.ab.block(ip, f"repeat_offender_{total_attacks}",
                         score=85, ip_type="temp")

        # ۳. Cross-Layer Detection — رویداد از لایه‌های مختلف؟
        # اینجا ما فقط شدت و تنوع رو چک می‌کنیم
        severities = set(e["severity"] for e in recent)
        if "CRITICAL" in severities and len(attack_types) >= 2:
            self.stats["cross_layer"] += 1

    def _alert_chain(self, ip, attack_types, recent, event):
        """Alert برای زنجیره حمله"""
        if not TG: return
        try:
            # دسته‌بندی
            categories = set(e["category"] for e in recent)
            total_weight = sum(e["weight"] for e in recent)
            
            # مرتب‌سازی توسط زمان
            sorted_events = sorted(recent, key=lambda x: x["ts"])
            timeline = "\n".join([
                f"  {i+1}. {e['type']} @ {datetime.fromtimestamp(e['ts']).strftime('%H:%M')}"
                for i, e in enumerate(sorted_events[-5:])
            ])

            msg = (
                f"🧠 *ATTACK CHAIN DETECTED*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🌐 IP: `{ip}`\n"
                f"🎯 Attack Types: `{len(attack_types)}`\n"
                f"⚡ Total Weight: `{total_weight}`\n"
                f"📁 Categories: `{', '.join(categories)}`\n\n"
                f"📜 *Timeline:*\n{timeline}\n\n"
                f"🚫 *Action:* Permanently blocked\n"
                f"⏰ {datetime.now().strftime('%H:%M:%S')}"
            )
            requests.post(
                f"https://api.telegram.org/bot{TG}/sendMessage",
                json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
            # Voice alert
            os.system('termux-tts-speak "Attack chain detected" 2>/dev/null')
            os.system('termux-vibrate -d 500 2>/dev/null')
        except: pass

    def watch(self):
        qfile = os.path.join(BASE, "queue.jsonl")
        last_pos = 0

        print("🧠 L3 Behavioral Analytics — Correlation Engine")
        print(f"📊 Config:")
        print(f"   Window: {CONFIG['window_minutes']}min")
        print(f"   Chain threshold: {CONFIG['attack_chain_threshold']} types")
        print(f"   Repeat threshold: {CONFIG['repeat_offender_threshold']}")
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
                        self.process_event(e)
                    except: pass

                self.save_state()
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"⚠️ {e}")
                time.sleep(5)

    def status(self):
        uptime = int(time.time() - self.stats["started"])
        h, m = divmod(uptime // 60, 60)
        print(f"\n🧠 L3 Behavioral Analytics Status")
        print(f"═══════════════════════════════════")
        print(f"Uptime:              {h}h {m}m")
        print(f"Total events:        {self.stats['total']}")
        print(f"Chains detected:     {self.stats['chains_detected']}")
        print(f"Repeat offenders:    {self.stats['repeat_offenders']}")
        print(f"Cross-layer:         {self.stats['cross_layer']}")
        print()
        print(f"📊 Tracked:")
        print(f"   IPs:     {len(self.ip_events)}")
        print(f"   Users:   {len(self.user_events)}")

    def test(self):
        """تست زنجیره حمله"""
        print("🧪 Testing Behavioral Analytics\n")

        ip = "9.9.9.9"

        print(f"📍 Attack chain from {ip}:")
        
        # مرحله ۱: Port Scan
        print("   1. Port Scan...")
        self.process_event({
            "event_type": "PORT_SCAN",
            "severity": "WARN",
            "source_ip": ip,
            "message": "Port scan detected",
        })
        time.sleep(0.1)

        # مرحله ۲: SQLi
        print("   2. SQL Injection...")
        self.process_event({
            "event_type": "SQLI",
            "severity": "CRITICAL",
            "source_ip": ip,
            "message": "SQL Injection: OR 1=1",
        })
        time.sleep(0.1)

        # مرحله ۳: Brute Force
        print("   3. Brute Force...")
        self.process_event({
            "event_type": "BRUTE_FORCE",
            "severity": "CRITICAL",
            "source_ip": ip,
            "message": "Brute force: 100 attempts",
        })

        print("\n✅ Chain should be detected!")
        print()
        self.status()

def main():
    if len(sys.argv) < 2:
        print("Usage: layer03_behavioral.py {watch|status|test}")
        return
    cmd = sys.argv[1]
    ba = BehavioralAnalytics()

    if cmd == "watch": ba.watch()
    elif cmd == "status": ba.status()
    elif cmd == "test": ba.test()

if __name__ == "__main__":
    main()
