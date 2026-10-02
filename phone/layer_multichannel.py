#!/usr/bin/env python3
"""L-Multichannel — Multi-Channel Alert System"""
import os, sys, json, time, smtplib, threading
from email.mime.text import MIMEText
from datetime import datetime
from collections import deque

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
STATE_FILE = os.path.join(BASE, "layer_multichannel_state.json")
QUEUE_FILE = os.path.join(BASE, "alerts_queue.jsonl")

CONFIG = {
    "channels": {
        "telegram": {
            "enabled": True,
            "token": open(os.path.join(HOME, "vorix/.tg-token")).read().strip() if os.path.exists(os.path.join(HOME, "vorix/.tg-token")) else "",
            "chat_id": "175160049",
        },
        "email": {
            "enabled": False,
            "smtp": "smtp.gmail.com",
            "port": 587,
            "user": "",
            "password": "",
            "to": "",
        },
        "webhook": {
            "enabled": False,
            "url": "",  # Discord/Slack webhook
        },
    },
    "min_severity": "WARN",
}


class MultiChannel:
    def __init__(self):
        self.queue = deque(maxlen=5000)
        self.lock = threading.Lock()
        self.stats = {"sent": 0, "failed": 0, "started": time.time()}
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

    def send(self, title, message, severity="INFO"):
        """ارسال به همه کانال‌ها"""
        with self.lock:
            sev_order = {"INFO": 0, "WARN": 1, "ERROR": 2, "CRITICAL": 3}
            if sev_order.get(severity, 0) < sev_order.get(CONFIG["min_severity"], 1):
                return
            
            results = {}
            
            # Telegram
            if CONFIG["channels"]["telegram"]["enabled"]:
                results["telegram"] = self._send_telegram(title, message, severity)
            
            # Email
            if CONFIG["channels"]["email"]["enabled"]:
                results["email"] = self._send_email(title, message, severity)
            
            # Webhook
            if CONFIG["channels"]["webhook"]["enabled"]:
                results["webhook"] = self._send_webhook(title, message, severity)
            
            # ذخیره در queue
            self.queue.append({
                "ts": datetime.now().isoformat(),
                "title": title,
                "message": message,
                "severity": severity,
                "results": results,
            })
            
            success = any(v for v in results.values())
            if success:
                self.stats["sent"] += 1
            else:
                self.stats["failed"] += 1
            self.save_state()
            
            return results

    def _send_telegram(self, title, message, severity):
        cfg = CONFIG["channels"]["telegram"]
        if not cfg["token"]: return False
        try:
            import requests
            icons = {"INFO": "i", "WARN": "!", "ERROR": "!!", "CRITICAL": "!!!"}
            icon = icons.get(severity, "i")
            full_msg = icon + " <b>" + title + "</b>\n\n" + message

            alert_id = "ALT-" + str(int(time.time()))

            buttons = [
                [
                    {"text": "Status", "callback_data": "status:" + alert_id},
                    {"text": "Detail", "callback_data": "detail:" + alert_id},
                ],
                [
                    {"text": "Block IP", "callback_data": "block:" + alert_id},
                    {"text": "Ignore", "callback_data": "ignore:" + alert_id},
                ],
            ]
            if severity in ("CRITICAL", "ERROR"):
                buttons.insert(2, [
                    {"text": "Forensics", "callback_data": "forensics:" + alert_id}
                ])

            dash = CONFIG.get("dashboard_url", "").strip()
            if dash.startswith("https://"):
                buttons.append([
                    {"text": "Dashboard", "url": dash + "/alert/" + alert_id}
                ])

            r = requests.post(
                "https://api.telegram.org/bot" + cfg["token"] + "/sendMessage",
                json={
                    "chat_id": cfg["chat_id"],
                    "text": full_msg,
                    "parse_mode": "HTML",
                    "reply_markup": {"inline_keyboard": buttons},
                    "disable_web_page_preview": True,
                },
                timeout=10,
            )
            return r.status_code == 200
        except Exception as e:
            print("[TG ERROR] " + str(e))
            return False

    def _send_email(self, title, message, severity):
        cfg = CONFIG["channels"]["email"]
        if not cfg["user"] or not cfg["password"]: return False
        try:
            msg = MIMEText(message)
            msg["Subject"] = f"[VORIX {severity}] {title}"
            msg["From"] = cfg["user"]
            msg["To"] = cfg["to"]
            
            with smtplib.SMTP(cfg["smtp"], cfg["port"]) as server:
                server.starttls()
                server.login(cfg["user"], cfg["password"])
                server.send_message(msg)
            return True
        except: return False

    def _send_webhook(self, title, message, severity):
        cfg = CONFIG["channels"]["webhook"]
        if not cfg["url"]: return False
        try:
            import requests
            r = requests.post(
                cfg["url"],
                json={"content": f"**{title}**\n{message}"},
                timeout=10
            )
            return r.status_code in (200, 204)
        except: return False

    def watch_queue(self):
        """پایش queue.jsonl و ارسال خودکار"""
        qfile = os.path.join(BASE, "queue.jsonl")
        last_pos = 0
        
        print("📢 Multi-Channel watcher started")
        
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
                    try:
                        e = json.loads(line)
                        sev = e.get("severity", "INFO")
                        if sev in ("CRITICAL", "ERROR", "WARN"):
                            self.send(
                                title=f"{e.get('event_type', 'Event')}",
                                message=e.get("message", ""),
                                severity=sev
                            )
                    except: pass
            except KeyboardInterrupt: break
            except: time.sleep(5)

    def status(self):
        uptime = int(time.time() - self.stats["started"])
        print(f"\n📢 L-Multichannel")
        print(f"═══════════════════════════════")
        print(f"Sent:        {self.stats['sent']}")
        print(f"Failed:      {self.stats['failed']}")
        print(f"Uptime:      {uptime // 3600}h {(uptime // 60) % 60}m")
        print()
        print(f"📡 Channels:")
        for name, cfg in CONFIG["channels"].items():
            icon = "✅" if cfg["enabled"] else "❌"
            print(f"   {icon} {name}")

    def test(self):
        print("🧪 Testing Multi-Channel\n")
        
        result = self.send(
            title="Test Alert",
            message="This is a test from VORIX multichannel",
            severity="CRITICAL"
        )
        print(f"Results: {result}")
        print()
        self.status()


def main():
    if len(sys.argv) < 2:
        print("Usage: layer_multichannel.py {test|status|watch}")
        return
    cmd = sys.argv[1]
    mc = MultiChannel()
    
    if cmd == "test": mc.test()
    elif cmd == "status": mc.status()
    elif cmd == "watch": mc.watch_queue()

if __name__ == "__main__":
    main()
