#!/usr/bin/env python3
"""L-Mocker — Taunt Engine"""
import os, sys, json, time, socket, threading, random
from datetime import datetime

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
STATE_FILE = os.path.join(BASE, "layer_mocker_state.json")

try:
    import requests
    with open(os.path.join(HOME, "vorix/.tg-token")) as f:
        TG = f.read().strip()
except:
    TG = ""
CHAT = "175160049"

# پیام‌های مسخره
TAUNTS = {
    "opening": [
        "Welcome, hacker! 🎉 Nice to meet you.",
        "Oh look, a hacker! How original. 🙄",
        "Congratulations! You found our honeypot. 🍯",
        "Hi! Are you a script kiddie? You seem like one. 😏",
        "Slow news day? You're here bothering us. 📰",
    ],
    "generic": [
        "Try harder 😏",
        "Is that all you've got?",
        "My grandma hacks better than you.",
        "You know we're logging everything, right? 📸",
        "Don't you have a real job? 💼",
        "Your mom would be so proud. 😢",
        "Hackers these days... so predictable. 🤦",
        "This is the most fun I've had all day! 🎢",
    ],
    "sqli": [
        "SQL injection! So 2005 of you. 💅",
        "Bobby Tables would be disappointed. 📊",
        "' OR 1=1 -- ? Really? That's like... so basic.",
    ],
    "bruteforce": [
        "Brute force? That's not very elegant. 🐢",
        "You could be here for years. I have 2 million users. 😴",
        "Have you tried the 'forgot password' link?",
    ],
    "warning": [
        "⚠️ Last warning. We've logged your IP.",
        "🚨 You've been reported to 47 security agencies. Just kidding. Or am I?",
        "🎯 One more try and we take action.",
    ],
    "final": [
        "OK, fun time is over. Goodbye! 👋",
        "Your IP has been blocked. Have a nice day! 🚫",
        "Thanks for playing! You lost. 🎮",
    ],
}


class Mocker:
    def __init__(self):
        self.stats = {"taunts_sent": 0, "ips_taunted": 0, "started": time.time()}
        self.history = {}
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

    def pick(self, category):
        return random.choice(TAUNTS.get(category, TAUNTS["generic"]))

    def detect_category(self, data):
        """تشخیص دسته پیام"""
        if not data: return "generic"
        d = data.lower()
        if any(x in d for x in ["sql", "or 1=1", "union"]): return "sqli"
        if any(x in d for x in ["brute", "pass", "login"]): return "bruteforce"
        return "generic"

    def taunt(self, ip, data=""):
        """ارسال پاسخ مسخره"""
        with self.lock:
            category = self.detect_category(data)
            
            if ip not in self.history:
                self.history[ip] = {"count": 0, "first": time.time()}
            self.history[ip]["count"] += 1
            count = self.history[ip]["count"]
            
            # تصمیم دسته
            if count == 1:
                taunt = self.pick("opening")
            elif count >= 5:
                taunt = self.pick("final")
            elif count >= 3:
                taunt = self.pick("warning")
            else:
                taunt = self.pick(category)
            
            self.stats["taunts_sent"] += 1
            if count == 1:
                self.stats["ips_taunted"] += 1
            self.save_state()
            
            return taunt

    def status(self):
        uptime = int(time.time() - self.stats["started"])
        print(f"\n🎭 L-Mocker")
        print(f"═══════════════════════════════")
        print(f"Taunts sent:   {self.stats['taunts_sent']}")
        print(f"IPs taunted:   {self.stats['ips_taunted']}")
        print(f"Uptime:        {uptime // 3600}h {(uptime // 60) % 60}m")

    def test(self):
        print("🧪 Testing Mocker\n")
        
        print("📍 Taunting 1.2.3.4...")
        for i in range(6):
            msg = self.taunt("1.2.3.4", "' OR 1=1 --")
            print(f"   {i+1}. {msg}")
            time.sleep(0.1)
        
        print()
        self.status()


def main():
    if len(sys.argv) < 2:
        print("Usage: layer_mocker.py {test|status}")
        return
    cmd = sys.argv[1]
    mk = Mocker()
    if cmd == "test": mk.test()
    elif cmd == "status": mk.status()

if __name__ == "__main__":
    main()
