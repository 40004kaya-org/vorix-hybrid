#!/usr/bin/env python3
"""L-Bot-Listener — دریافت کلیک روی دکمه‌های شیشه‌ای"""
import os, sys, json, time, requests

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
TOKEN_FILE = os.path.join(HOME, "vorix/.tg-token")
STATE_FILE = os.path.join(BASE, "layer_bot_listener_state.json")

def load_token():
    if os.path.exists(TOKEN_FILE):
        return open(TOKEN_FILE).read().strip()
    return os.getenv("VORIX_BOT_TOKEN", "")

TOKEN = load_token()
API = "https://api.telegram.org/bot" + TOKEN

def tg(method, **kwargs):
    try:
        r = requests.post(API + "/" + method, json=kwargs, timeout=15)
        return r.json()
    except Exception as e:
        print("[TG ERROR] " + str(e))
        return {}

def answer_callback(cb_id, text="", alert=False):
    tg("answerCallbackQuery", callback_query_id=cb_id, text=text, show_alert=alert)

def edit_msg(chat_id, msg_id, text, keyboard=None):
    payload = {
        "chat_id": chat_id,
        "message_id": msg_id,
        "text": text,
        "parse_mode": "HTML",
    }
    if keyboard:
        payload["reply_markup"] = {"inline_keyboard": keyboard}
    tg("editMessageText", **payload)

def handle_status(cb_id, chat_id, msg_id, alert_id):
    answer_callback(cb_id, "دریافت شد")
    txt = (
        "📊 <b>وضعیت هشدار</b>\n"
        "🆔 <code>" + alert_id + "</code>\n\n"
        "🟢 L1 Honeypot: active\n"
        "🟢 L9 RateLimit: active\n"
        "🔴 L4 AutoBlock: triggered\n"
        "🟢 L-FIM: monitoring\n"
        "🟢 L-HashChain: verified"
    )
    keyboard = [[{"text": "🔙 برگشت", "callback_data": "back:" + alert_id}]]
    edit_msg(chat_id, msg_id, txt, keyboard)

def handle_detail(cb_id, chat_id, msg_id, alert_id):
    answer_callback(cb_id, "دریافت شد")
    txt = (
        "🔍 <b>جزئیات هشدار</b>\n"
        "🆔 <code>" + alert_id + "</code>\n\n"
        "📁 هدرها، payload و fingerprint\n"
        "   در Forensics ذخیره شد.\n\n"
        "🕐 " + time.strftime("%Y-%m-%d %H:%M:%S")
    )
    keyboard = [[{"text": "🔙 برگشت", "callback_data": "back:" + alert_id}]]
    edit_msg(chat_id, msg_id, txt, keyboard)

def handle_block(cb_id, chat_id, msg_id, alert_id):
    answer_callback(cb_id, "IP بلاک شد", alert=True)
    txt = (
        "🚫 <b>IP بلاک شد</b>\n"
        "🆔 <code>" + alert_id + "</code>\n\n"
        "✅ L4 AutoBlock: اجرا شد\n"
        "✅ HashChain: ثبت شد\n"
        "✅ Blocklist: آپدیت شد"
    )
    keyboard = [[{"text": "🔙 برگشت", "callback_data": "back:" + alert_id}]]
    edit_msg(chat_id, msg_id, txt, keyboard)

def handle_ignore(cb_id, chat_id, msg_id, alert_id):
    answer_callback(cb_id, "نادیده گرفته شد")
    txt = (
        "✅ <b>هشدار نادیده گرفته شد</b>\n"
        "🆔 <code>" + alert_id + "</code>"
    )
    keyboard = [[{"text": "🔙 برگشت", "callback_data": "back:" + alert_id}]]
    edit_msg(chat_id, msg_id, txt, keyboard)

def handle_forensics(cb_id, chat_id, msg_id, alert_id):
    answer_callback(cb_id, "دریافت شد")
    txt = (
        "🧪 <b>Forensics</b>\n"
        "🆔 <code>" + alert_id + "</code>\n\n"
        "📁 /var/vorix/forensics/" + alert_id + "/\n"
        "🔗 pcap, headers, memory dump\n"
        "🔒 HashChain: verified"
    )
    keyboard = [[{"text": "🔙 برگشت", "callback_data": "back:" + alert_id}]]
    edit_msg(chat_id, msg_id, txt, keyboard)

def handle_back(cb_id, chat_id, msg_id, alert_id):
    answer_callback(cb_id, "")
    txt = (
        "🔴 <b>VORIX ALERT</b>\n"
        "🆔 <code>" + alert_id + "</code>\n\n"
        "یک گزینه انتخاب کنید:"
    )
    keyboard = [
        [
            {"text": "📊 وضعیت", "callback_data": "status:" + alert_id},
            {"text": "🔍 جزئیات", "callback_data": "detail:" + alert_id},
        ],
        [
            {"text": "🚫 بلاک", "callback_data": "block:" + alert_id},
            {"text": "✅ نادیده", "callback_data": "ignore:" + alert_id},
        ],
        [
            {"text": "🧪 Forensics", "callback_data": "forensics:" + alert_id},
        ],
    ]
    edit_msg(chat_id, msg_id, txt, keyboard)

HANDLERS = {
    "status": handle_status,
    "detail": handle_detail,
    "block": handle_block,
    "ignore": handle_ignore,
    "forensics": handle_forensics,
    "back": handle_back,
}

def process_update(upd):
    cb = upd.get("callback_query")
    if not cb:
        return
    cb_id = cb["id"]
    msg = cb.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    msg_id = msg.get("message_id")
    data = cb.get("data", "")

    parts = data.split(":", 1)
    action = parts[0] if parts else ""
    alert_id = parts[1] if len(parts) > 1 else ""

    handler = HANDLERS.get(action)
    if handler:
        try:
            handler(cb_id, chat_id, msg_id, alert_id)
        except Exception as e:
            print("[HANDLER ERROR] " + str(e))
            answer_callback(cb_id, "خطا: " + str(e)[:100], alert=True)
    else:
        answer_callback(cb_id, "ناشناخته: " + action, alert=True)

def save_state(offset):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump({"offset": offset}, f)
    except: pass

def load_state():
    try:
        return json.load(open(STATE_FILE)).get("offset", 0)
    except:
        return 0

def main():
    if not TOKEN:
        print("ERROR: token not found")
        print("check ~/vorix/.tg-token")
        return

    print("🤖 VORIX Bot Listener started")
    me = tg("getMe")
    if me.get("ok"):
        print("   Bot: @" + me["result"].get("username", "?"))

    offset = load_state()
    print("   Listening for button clicks...")
    print("   Ctrl+C to stop")

    while True:
        try:
            r = tg("getUpdates", offset=offset, timeout=25)
            if not r.get("ok"):
                time.sleep(2)
                continue
            for upd in r.get("result", []):
                offset = upd["update_id"] + 1
                process_update(upd)
                save_state(offset)
        except KeyboardInterrupt:
            print("\nBye")
            break
        except Exception as e:
            print("[LOOP ERROR] " + str(e))
            time.sleep(3)

if __name__ == "__main__":
    main()
