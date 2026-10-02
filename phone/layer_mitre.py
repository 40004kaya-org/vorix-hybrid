#!/usr/bin/env python3
"""L-MITRE — ATT&CK Mapping"""
import os, sys, json, time
from datetime import datetime
from collections import defaultdict

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
STATE_FILE = os.path.join(BASE, "layer_mitre_state.json")

# MITRE ATT&CK Mapping
MITRE_MAP = {
    # Reconnaissance
    "PORT_SCAN": ("T1046", "Network Service Discovery", "Reconnaissance"),
    "FINGERPRINT": ("T1592", "Gather Victim Host Info", "Reconnaissance"),
    
    # Initial Access
    "SQLI": ("T1190", "Exploit Public-Facing Application", "Initial Access"),
    "SQL_INJECTION": ("T1190", "Exploit Public-Facing Application", "Initial Access"),
    "XSS": ("T1189", "Drive-by Compromise", "Initial Access"),
    "PHISHING": ("T1566", "Phishing", "Initial Access"),
    
    # Credential Access
    "BRUTE_FORCE": ("T1110", "Brute Force", "Credential Access"),
    "CREDENTIAL_STUFFING": ("T1110.004", "Credential Stuffing", "Credential Access"),
    "CRED_STUFFING": ("T1110.004", "Credential Stuffing", "Credential Access"),
    "PASSWORD_LEAK": ("T1552", "Unsecured Credentials", "Credential Access"),
    "LOGIN_ANALYZER": ("T1078", "Valid Accounts", "Credential Access"),
    
    # Execution
    "SUSPICIOUS_PROCESS": ("T1059", "Command and Scripting Interpreter", "Execution"),
    "SHELL": ("T1059.004", "Unix Shell", "Execution"),
    
    # Persistence
    "BACKDOOR": ("T1505", "Server Software Component", "Persistence"),
    "ROOTKIT": ("T1014", "Rootkit", "Persistence"),
    "BOOT_PERSISTENCE": ("T1542", "Pre-OS Boot", "Persistence"),
    
    # Defense Evasion
    "HIDDEN_PROCESS": ("T1014", "Rootkit", "Defense Evasion"),
    "LD_PRELOAD": ("T1574.006", "Dynamic Linker Hijacking", "Defense Evasion"),
    "LOG_DELETION": ("T1070", "Indicator Removal", "Defense Evasion"),
    
    # Discovery
    "NETWORK_MONITOR": ("T1040", "Network Sniffing", "Discovery"),
    
    # Lateral Movement
    "SESSION_HIJACK": ("T1563", "Session Hijacking", "Lateral Movement"),
    "MULTI_IP_SESSION": ("T1563", "Session Hijacking", "Lateral Movement"),
    
    # Command and Control
    "BEACONING": ("T1071", "Application Layer Protocol", "Command and Control"),
    "C2": ("T1071", "Application Layer Protocol", "Command and Control"),
    "DNS_TUNNEL": ("T1071.004", "DNS", "Command and Control"),
    
    # Exfiltration
    "DATA_EXFIL": ("T1041", "Exfil Over C2 Channel", "Exfiltration"),
    "EXFIL": ("T1041", "Exfil Over C2 Channel", "Exfiltration"),
    "DATA_QUARANTINE": ("T1041", "Data Exfiltration", "Exfiltration"),
    
    # Impact
    "DDoS": ("T1498", "Network DoS", "Impact"),
    "DOS": ("T1498", "Network DoS", "Impact"),
    "MALWARE": ("T1204", "User Execution", "Execution"),
    "RANSOMWARE": ("T1486", "Data Encrypted for Impact", "Impact"),
    "DESTRUCTION": ("T1485", "Data Destruction", "Impact"),
    
    # Others
    "RATE_LIMIT": ("T1499", "Endpoint DoS", "Impact"),
    "GEOIP_BLOCK": ("T1071", "Application Layer Protocol", "Command and Control"),
    "DNS_SINKHOLE": ("T1071.004", "DNS", "Command and Control"),
    "SSL_MONITOR": ("T1557", "Adversary-in-the-Middle", "Collection"),
    "COOKIE_ANOMALY": ("T1539", "Steal Web Session Cookie", "Credential Access"),
    "HEADER_ANALYSIS": ("T1190", "Exploit Public-Facing Application", "Initial Access"),
}


class MITREMapping:
    def __init__(self):
        self.techniques = defaultdict(int)
        self.tactics = defaultdict(int)
        self.stats = {"mapped": 0, "started": time.time()}
        self.load_state()

    def load_state(self):
        try:
            with open(STATE_FILE) as f:
                s = json.load(f)
                self.stats = s.get("stats", self.stats)
                self.techniques = defaultdict(int, s.get("techniques", {}))
                self.tactics = defaultdict(int, s.get("tactics", {}))
        except: pass

    def save_state(self):
        try:
            with open(STATE_FILE, "w") as f:
                json.dump({
                    "stats": self.stats,
                    "techniques": dict(self.techniques),
                    "tactics": dict(self.tactics),
                }, f, indent=2)
        except: pass

    def map_event(self, event_type):
        """نگاشت رویداد به ATT&CK (case-insensitive)"""
        key = event_type.upper().replace(" ", "_")
        
        # جستجوی مستقیم
        if key in MITRE_MAP:
            tid, name, tactic = MITRE_MAP[key]
            self.techniques[f"{tid}|{name}"] += 1
            self.tactics[tactic] += 1
            self.stats["mapped"] += 1
            self.save_state()
            return {"id": tid, "name": name, "tactic": tactic}
        
        # جستجوی case-insensitive
        for k, v in MITRE_MAP.items():
            if k.upper() == key:
                tid, name, tactic = v
                self.techniques[f"{tid}|{name}"] += 1
                self.tactics[tactic] += 1
                self.stats["mapped"] += 1
                self.save_state()
                return {"id": tid, "name": name, "tactic": tactic}
        
        return None

    def status(self):
        uptime = int(time.time() - self.stats["started"])
        print(f"\n🎯 L-MITRE ATT&CK")
        print(f"═══════════════════════════════")
        print(f"Mapped:      {self.stats['mapped']}")
        print(f"Techniques:  {len(self.techniques)}")
        print(f"Tactics:     {len(self.tactics)}")
        print(f"Uptime:      {uptime // 3600}h {(uptime // 60) % 60}m")
        print()
        if self.tactics:
            print(f"📊 Tactics covered:")
            for t, c in sorted(self.tactics.items(), key=lambda x: -x[1]):
                print(f"   • {t}: {c}")
        if self.techniques:
            print(f"\n🎯 Top Techniques:")
            for tech, c in sorted(self.techniques.items(), key=lambda x: -x[1])[:5]:
                tid, name = tech.split("|", 1)
                print(f"   • {tid}: {name} ({c})")

    def test(self):
        print("🧪 Testing MITRE Mapping\n")
        
        test_attacks = [
            "PORT_SCAN", "SQLI", "BRUTE_FORCE", "CRED_STUFFING",
            "BEACONING", "DNS_TUNNEL", "DATA_EXFIL", "DDoS",
        ]
        
        for atk in test_attacks:
            result = self.map_event(atk)
            if result:
                print(f"   ✅ {atk:<20} → {result['id']} ({result['tactic']})")
            else:
                print(f"   ⚠️  {atk:<20} → unmapped")
        
        print()
        self.status()


def main():
    if len(sys.argv) < 2:
        print("Usage: layer_mitre.py {status|test|map <event>}")
        return
    cmd = sys.argv[1]
    mm = MITREMapping()
    if cmd == "status": mm.status()
    elif cmd == "test": mm.test()
    elif cmd == "map" and len(sys.argv) > 2:
        result = mm.map_event(sys.argv[2])
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
