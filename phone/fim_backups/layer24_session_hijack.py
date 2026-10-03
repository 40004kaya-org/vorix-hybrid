#!/usr/bin/env python3
"""L24 — Session Hijack Detection"""
import os, sys, json, time, threading
from datetime import datetime
from collections import defaultdict

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
STATE_FILE = os.path.join(BASE, "layer24_state.json")

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
    "max_ips_per_session": 3,
    "max_uas_per_session": 2,
    "session_window_minutes": 30,
    "impossible_travel_km": 500,  # غیرفعال در نسخه ساده
}


class SessionHijack:
    def __init__(self):
        # session → {ips: set, uas: set, first_seen, last_seen}
        self.sessions = defaultdict(lambda: {
            "ips": set(),
            "uas": set(),
            "first_seen": None,
            "last_seen": None,
            "events": []
        })
        self.ab = AutoBlock()
        self.lock = threading.Lock()
        self.stats = {"checked": 0, "hijacks": 0, "blocked": 0, "started": time.time()}
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

    def check(self, session_id, ip, ua="unknown"):
        """چک session"""
        if not session_id or not ip:
            return None

        with self.lock:
            self.stats["checked"] += 1
            now = time.time()
            s = self.sessions[session_id]

            if s["first_seen"] is None:
                s["first_seen"] = now

            # چک انقضا
            if s["last_seen"] and (now - s["last_seen"]) > CONFIG["session_window_minutes"] * 60:
                # reset
                s["ips"] = set()
                s["uas"] = set()
                s["first_seen"] = now

            s["last_seen"] = now
            s["ips"].add(ip)
            if ua:
                s["uas"].add(ua)

            issue = None

            # چک IP های مختلف
            if len(s["ips"]) > CONFIG["max_ips_per_session"]:
                issue = {
                    "type": "MULTI_IP_SESSION",
                    "session": session_id[:16],
                    "ips_count": len(s["ips"]),
                    "ips": list(s["ips"])[:5],
                    "severity": "SUSPICIOUS"
                }

            # چک UA های مختلف
            if len(s["uas"]) > CONFIG["max_uas_per_session"]:
                issue = {
                    "type": "MULTI_UA_SESSION",
                    "session": session_id[:16],
                    "uas_count": len(s["uas"]),
                    "severity": "SUSPICIOUS"
                }

            if issue:
                self.stats["hijacks"] += 1
                
                # اگه از ۵ IP بیشتر → بلاک
                if len(s["ips"]) > 5:
                    for bad_ip in s["ips"]:
                        self.ab.block(bad_ip, f"session_hijack_{session_id[:8]}",
                                     score=80, ip_type="temp")
                    self.stats["blocked"] += 1
                    issue["severity"] = "CRITICAL"

                self._alert(issue)

            return issue

    def _alert(self, issue):
        if not TG: return
        try:
            icon = "🔴" if issue["severity"] == "CRITICAL" else "🟡"
            ips_str = ", ".join(issue.get("ips", []))[:100] if "ips" in issue else "?"
            msg = (
                f"🔐 *Session Hijack {issue['severity']}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Session: `{issue['session']}`\n"
                f"Type: `{issue['type']}`\n"
                f"IPs Count: `{issue.get('ips_count', '?')}`\n"
                f"IPs: `{ips_str}`\n"
                f"⏰ {datetime.now().strftime('%H:%M:%S')}"
            )
            requests.post(
                f"https://api.telegram.org/bot{TG}/sendMessage",
                json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
        except: pass

    def status(self):
        uptime = int(time.time() - self.stats["started"])
        print(f"\n🔐 L24 Session Hijack")
        print(f"═══════════════════════════════")
        print(f"Checked:     {self.stats['checked']}")
        print(f"Hijacks:     {self.stats['hijacks']}")
        print(f"Blocked:     {self.stats['blocked']}")
        print(f"Sessions:    {len(self.sessions)}")
        print(f"Uptime:      {uptime // 3600}h {(uptime // 60) % 60}m")

    def test(self):
        print("🧪 Testing Session Hijack\n")
        # ۱. session عادی
        print("📍 Normal session (same IP):")
        for _ in range(3):
            r = self.check("session-normal-1", "1.2.3.4", "Mozilla/5.0")
            print(f"   {'🚨' if r else '✅'} → {r['type'] if r else 'OK'}")
        
        # ۲. session hijack
        print("\n📍 Hijack session (5 different IPs):")
        for i in range(6):
            r = self.check("session-hijack-1", f"5.6.7.{i}", "Mozilla/5.0")
            print(f"   {'🚨' if r else '✅'} IP 5.6.7.{i} → {r['type'] if r else 'OK'}")
        
        print()
        self.status()


def main():
    if len(sys.argv) < 2:
        print("Usage: layer24_session_hijack.py {test|status}")
        return
    cmd = sys.argv[1]
    sh = SessionHijack()
    if cmd == "test": sh.test()
    elif cmd == "status": sh.status()


if __name__ == "__main__":
    main()
