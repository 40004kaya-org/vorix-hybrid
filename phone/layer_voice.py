#!/usr/bin/env python3
"""L-Voice — Voice Alerts"""
import os, sys, json, time, threading, subprocess
from datetime import datetime
from collections import deque

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
STATE_FILE = os.path.join(BASE, "layer_voice_state.json")

CONFIG = {
    "min_interval": 30,          # حداقل ۳۰ ثانیه بین پیام‌ها
    "critical_priority": True,
    "quiet_hours": (23, 7),      # ۲۳ شب تا ۷ صبح بدون صدا (مگر critical)
}

class VoiceAlert:
    def __init__(self):
        self.last_spoken = 0
        self.queue = deque(maxlen=100)
        self.stats = {"spoken": 0, "skipped": 0, "started": time.time()}
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

    def is_quiet_hour(self):
        """چک ساعت سکوت"""
        h = datetime.now().hour
        start, end = CONFIG["quiet_hours"]
        if start > end:
            return h >= start or h < end
        return start <= h < end

    def speak(self, text, priority="normal"):
        """پخش صوتی"""
        now = time.time()
        
        # Rate limit
        if now - self.last_spoken < CONFIG["min_interval"]:
            self.stats["skipped"] += 1
            return False
        
        # ساعت سکوت
        if self.is_quiet_hour() and priority != "critical":
            self.stats["skipped"] += 1
            return False
        
        try:
            # پیام فارسی + انگلیسی
            os.system(f'termux-tts-speak "{text}" 2>/dev/null')
            self.last_spoken = now
            self.stats["spoken"] += 1
            self.save_state()
            return True
        except Exception as e:
            print(f"⚠️ TTS error: {e}")
            return False

    def alert_critical(self, message):
        """هشدار بحرانی"""
        self.speak(f"Critical alert. {message}", priority="critical")
        # ویبره الگو
        for _ in range(3):
            os.system('termux-vibrate -d 500 2>/dev/null')
            time.sleep(0.3)

    def alert_warning(self, message):
        """هشدار متوسط"""
        self.speak(f"Warning. {message}")
        os.system('termux-vibrate -d 200 2>/dev/null')

    def status(self):
        uptime = int(time.time() - self.stats["started"])
        print(f"\n🔊 L-Voice Alerts")
        print(f"═══════════════════════════════")
        print(f"Spoken:     {self.stats['spoken']}")
        print(f"Skipped:    {self.stats['skipped']}")
        print(f"Uptime:     {uptime // 3600}h {(uptime // 60) % 60}m")
        print(f"Quiet now:  {'✅' if self.is_quiet_hour() else '❌'}")

    def test(self):
        print("🧪 Testing Voice Alert\n")
        print("📍 Testing normal...")
        self.speak("VORIX voice alert test", priority="normal")
        print("📍 Testing critical...")
        time.sleep(2)
        self.alert_critical("Test critical alert")
        print()
        self.status()


def main():
    if len(sys.argv) < 2:
        print("Usage: layer_voice.py {test|status|speak <text>}")
        return
    cmd = sys.argv[1]
    va = VoiceAlert()
    if cmd == "test": va.test()
    elif cmd == "status": va.status()
    elif cmd == "speak" and len(sys.argv) > 2:
        va.speak(" ".join(sys.argv[2:]), priority="critical")

if __name__ == "__main__":
    main()
