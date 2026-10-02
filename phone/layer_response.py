#!/usr/bin/env python3
"""L-Response — Auto Response Playbook (SOAR-like)"""
import os, sys, json, time, subprocess, threading
from datetime import datetime
from collections import defaultdict

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
STATE_FILE = os.path.join(BASE, "layer_response_state.json")

sys.path.insert(0, BASE)
from layer04_auto_block import AutoBlock

try:
    import requests
    with open(os.path.join(HOME, "vorix/.tg-token")) as f:
        TG = f.read().strip()
except:
    TG = ""
CHAT = "175160049"

# ═══════════════════════════════════════════════
#   PLAYBOOKS — سناریوهای پاسخ خودکار
# ═══════════════════════════════════════════════
PLAYBOOKS = {
    "SQL_INJECTION": {
        "actions": ["block_ip", "alert_critical", "log_forensics"],
        "score_boost": 20,
        "escalate": True,
    },
    "BRUTE_FORCE": {
        "actions": ["block_ip", "alert_high", "rate_limit_account"],
        "score_boost": 15,
        "escalate": False,
    },
    "PORT_SCAN": {
        "actions": ["block_ip", "alert_medium", "fingerprint"],
        "score_boost": 5,
        "escalate": False,
    },
    "BEACONING": {
        "actions": ["block_ip", "alert_critical", "kill_switch_ready", "forensics"],
        "score_boost": 30,
        "escalate": True,
    },
    "DATA_EXFIL": {
        "actions": ["block_ip", "alert_critical", "data_quarantine", "kill_switch_ready"],
        "score_boost": 40,
        "escalate": True,
    },
    "CREDENTIAL_STUFFING": {
        "actions": ["block_ip", "alert_high", "force_mfa"],
        "score_boost": 20,
        "escalate": True,
    },
    "TOOL_DETECTED": {
        "actions": ["block_ip", "alert_medium", "mocker_taunt"],
        "score_boost": 10,
        "escalate": False,
    },
    "ROOTKIT": {
        "actions": ["alert_critical", "kill_switch_ready", "forensics", "isolate"],
        "score_boost": 50,
        "escalate": True,
    },
}


class ResponsePlaybook:
    def __init__(self):
        self.ab = AutoBlock()
        self.recent_actions = defaultdict(list)
        self.lock = threading.Lock()
        self.stats = {"triggered": 0, "actions": 0, "started": time.time()}
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

    def execute(self, attack_type, ip, context=None):
        """اجرای playbook"""
        with self.lock:
            attack_key = attack_type.upper().replace(" ", "_")
            playbook = PLAYBOOKS.get(attack_key)
            
            if not playbook:
                return None
            
            self.stats["triggered"] += 1
            results = []
            
            for action in playbook["actions"]:
                try:
                    r = self._do_action(action, ip, attack_key, context or {})
                    results.append({"action": action, "result": r})
                    self.stats["actions"] += 1
                except Exception as e:
                    results.append({"action": action, "error": str(e)})
            
            self.save_state()
            
            # لاگ
            self._log_playbook(attack_key, ip, results)
            
            return {
                "attack": attack_key,
                "ip": ip,
                "actions_executed": len(results),
                "results": results,
                "score_boost": playbook["score_boost"],
                "escalate": playbook["escalate"],
            }

    def _do_action(self, action, ip, attack, ctx):
        """اجرای یک اکشن"""
        if action == "block_ip":
            return self.ab.block(ip, f"playbook_{attack.lower()}", score=80, ip_type="temp")
        
        elif action == "block_perm":
            return self.ab.block(ip, f"playbook_perm_{attack.lower()}", score=95, ip_type="perm")
        
        elif action == "alert_critical":
            self._send_alert("🔴 CRITICAL", attack, ip, ctx)
            os.system('termux-vibrate -d 500 2>/dev/null')
            os.system('termux-tts-speak "Critical attack detected" 2>/dev/null')
            return True
        
        elif action == "alert_high":
            self._send_alert("🟠 HIGH", attack, ip, ctx)
            os.system('termux-vibrate -d 300 2>/dev/null')
            return True
        
        elif action == "alert_medium":
            self._send_alert("🟡 MEDIUM", attack, ip, ctx)
            return True
        
        elif action == "log_forensics":
            try:
                sys.path.insert(0, BASE)
                from layer_forensics import Forensics
                fo = Forensics()
                fo.collect_evidence(attack, ip, ctx)
                return True
            except: return False
        
        elif action == "forensics":
            try:
                from layer_forensics import Forensics
                fo = Forensics()
                fo.collect_evidence(attack, ip, ctx)
                return True
            except: return False
        
        elif action == "kill_switch_ready":
            # فقط آماده‌سازی، نه فعال‌سازی کامل
            try:
                with open(os.path.join(BASE, "killswitch_ready.flag"), "w") as f:
                    f.write(f"{datetime.now().isoformat()} — {attack} from {ip}\n")
                return True
            except: return False
        
        elif action == "data_quarantine":
            try:
                from layer05_data_quarantine import DataQuarantine
                dq = DataQuarantine()
                dq.record_exfil_attempt({"source_ip": ip, "event_type": attack})
                return True
            except: return False
        
        elif action == "mocker_taunt":
            try:
                from layer_mocker import Mocker
                mk = Mocker()
                msg = mk.taunt(ip, attack)
                return msg[:50] if msg else True
            except: return False
        
        elif action == "fingerprint":
            # ثبت برای fingerprint
            return True
        
        elif action == "rate_limit_account":
            return True
        
        elif action == "force_mfa":
            return True
        
        elif action == "isolate":
            try:
                # قطع شبکه موقت
                return True
            except: return False
        
        return None

    def _send_alert(self, level, attack, ip, ctx):
        if not TG: return
        try:
            msg = (
                f"⚡ *Response Playbook*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Level: {level}\n"
                f"Attack: `{attack}`\n"
                f"IP: `{ip}`\n"
                f"Actions: `{len(PLAYBOOKS.get(attack, {}).get('actions', []))}`\n"
                f"⏰ {datetime.now().strftime('%H:%M:%S')}"
            )
            requests.post(
                f"https://api.telegram.org/bot{TG}/sendMessage",
                json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
        except: pass

    def _log_playbook(self, attack, ip, results):
        try:
            log_file = os.path.join(BASE, "playbooks.jsonl")
            with open(log_file, "a") as f:
                f.write(json.dumps({
                    "ts": datetime.now().isoformat(),
                    "attack": attack,
                    "ip": ip,
                    "results": results,
                }, default=str) + "\n")
        except: pass

    def status(self):
        uptime = int(time.time() - self.stats["started"])
        print(f"\n⚡ L-Response Playbook")
        print(f"═══════════════════════════════")
        print(f"Triggers:    {self.stats['triggered']}")
        print(f"Actions:     {self.stats['actions']}")
        print(f"Uptime:      {uptime // 3600}h {(uptime // 60) % 60}m")
        print(f"\n📚 Playbooks: {len(PLAYBOOKS)}")
        for name in list(PLAYBOOKS.keys())[:5]:
            print(f"   • {name}")

    def test(self):
        print("🧪 Testing Response Playbook\n")
        
        print("📍 SQL Injection playbook...")
        r = self.execute("SQL_INJECTION", "1.2.3.4", {"payload": "' OR 1=1--"})
        if r:
            print(f"   ✅ Executed {r['actions_executed']} actions")
            for x in r['results'][:3]:
                print(f"      • {x['action']}")
        
        print("\n📍 Beaconing playbook...")
        r = self.execute("BEACONING", "5.6.7.8", {})
        if r:
            print(f"   ✅ Executed {r['actions_executed']} actions")
        
        print()
        self.status()


def main():
    if len(sys.argv) < 2:
        print("Usage: layer_response.py {test|status|exec <attack> <ip>}")
        return
    cmd = sys.argv[1]
    rp = ResponsePlaybook()
    
    if cmd == "test": rp.test()
    elif cmd == "status": rp.status()
    elif cmd == "exec" and len(sys.argv) > 3:
        r = rp.execute(sys.argv[2], sys.argv[3])
        print(json.dumps(r, indent=2, default=str))

if __name__ == "__main__":
    main()
