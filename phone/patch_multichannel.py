#!/usr/bin/env python3
import os, re

FILE = os.path.expanduser("~/vorix-hybrid/phone/layer_multichannel.py")

with open(FILE, "r", encoding="utf-8") as f:
    src = f.read()

pattern = re.compile(
    r'    def _send_telegram\(self, title, message, severity\):.*?except: return False',
    re.DOTALL,
)

NEW_FUNC = r'''    def _send_telegram(self, title, message, severity):
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
            return False'''

# MAGIC: lambda m: NEW_FUNC -- inja re.subn dige backslash ro interpret nemikone
new_src, count = pattern.subn(lambda m: NEW_FUNC, src)

if count == 0:
    print("ERROR: function not found")
    exit(1)

if '"dashboard_url"' not in new_src:
    new_src = new_src.replace(
        '"min_severity": "WARN",',
        '"min_severity": "WARN",' + chr(10) + '    "dashboard_url": "",',
    )

with open(FILE, "w", encoding="utf-8") as f:
    f.write(new_src)

print("OK - patch v3 applied (lambda fix)")
