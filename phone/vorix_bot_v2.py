#!/usr/bin/env python3
"""VORIX Bot v2 — کنترل کامل از تلگرام"""
import os, json, time, requests
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
BASE = HOME / "vorix-hybrid/phone"
DOCS = HOME / "vorix-hybrid/docs/data"
TOKEN_FILE = HOME / "vorix/.tg-token"
CHAT_ID = 175160049

def load_token():
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    return os.getenv("VORIX_BOT_TOKEN", "")

TOKEN = load_token()
API = f"https://api.telegram.org/bot{TOKEN}"

def tg(method, **kwargs):
    try:
        r = requests.post(f"{API}/{method}", json=kwargs, timeout=15)
        return r.json()
    except Exception as e:
        print(f"[TG ERROR] {e}")
        return {}

def send(chat_id, text, kb=None):
    p = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if kb:
        p["reply_markup"] = {"inline_keyboard": kb}
    return tg("sendMessage", **p)

def edit(chat_id, msg_id, text, kb=None):
    p = {"chat_id": chat_id, "message_id": msg_id, "text": text, "parse_mode": "HTML"}
    if kb:
        p["reply_markup"] = {"inline_keyboard": kb}
    return tg("editMessageText", **p)

def answer_cb(cb_id, text=""):
    return tg("answerCallbackQuery", callback_query_id=cb_id, text=text)

# ─── LOAD DATA ─────────────────────────────
def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return None

def live_data():
    return load_json(DOCS / "live.json")

def attacks_data():
    return load_json(DOCS / "attacks.json")

def global_data():
    return load_json(DOCS / "live_global.json")

def logs_data():
    return load_json(DOCS / "logs.json")

# ─── FORMATTERS ────────────────────────────
def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def fmt_num(n):
    try:
        return f"{int(n):,}"
    except:
        return "0"

def status_text():
    d = live_data()
    if not d:
        return "❌ <b>live.json</b> در دسترس نیست"
    L = d.get("layers", [])
    active = sum(1 for x in L if x.get("running"))
    standby = sum(1 for x in L if not x.get("running") and x.get("color") == "yellow")
    down = sum(1 for x in L if not x.get("running") and x.get("color") == "red")
    ts = d.get("ts", "?")[:19].replace("T", " ")

    txt = f"""🛡️ <b>VORIX STATUS</b>

🟢 فعال: <b>{active}</b>
🟡 آماده: <b>{standby}</b>
🔴 خاموش: <b>{down}</b>
📊 کل: <b>{len(L)}</b>

🕐 آخرین آپدیت: <code>{ts}</code>
"""
    return txt

def attacks_text():
    d = attacks_data()
    if not d:
        return "❌ <b>attacks.json</b> در دسترس نیست"
    s = d.get("stats", {})
    at = d.get("attacks", [])
    txt = f"""🎯 <b>ATTACKS LOG</b>

🔴 کل: <b>{s.get('total', 0)}</b>
🚫 بلاک شده: <b>{s.get('blocked', 0)}</b>
⚠️ Critical: <b>{s.get('critical', 0)}</b>
🟠 High: <b>{s.get('high', 0)}</b>

📋 آخرین {min(5, len(at))} رویداد:
"""
    for a in at[:5]:
        sev = (a.get("severity") or "low").upper()
        typ = a.get("attack_type", "?")
        ts = (a.get("ts", "") or "")[:16].replace("T", " ")
        txt += f"• <code>{esc(ts)}</code> [{sev}] {esc(typ)}\n"
    return txt

def global_text():
    d = global_data()
    if not d:
        return "❌ <b>live_global.json</b> در دسترس نیست"
    s = d.get("stats", {})
    attacks = d.get("attacks", [])
    countries = d.get("countries", {})
    ts = d.get("ts", "?")[:19].replace("T", " ")

    txt = f"""🌐 <b>GLOBAL ATTACKS</b>

💥 کل حمله: <b>{fmt_num(s.get('total_attacks', 0))}</b>
🎯 IP فعال: <b>{s.get('unique_ips', 0)}</b>
🌍 کشورها: <b>{s.get('unique_countries', 0)}</b>
🦠 C2 سرور: <b>{s.get('c2_count', 0)}</b>

🕐 {ts}

🔥 <b>Top 5 مهاجم:</b>
"""
    for i, a in enumerate(attacks[:5], 1):
        txt += f"{i}. <code>{esc(a.get('ip', '?'))}</code> [{esc(a.get('country', '??'))}] <b>{fmt_num(a.get('count', 0))}</b>\n"
    return txt

def c2_text():
    d = global_data()
    if not d:
        return "❌ <b>live_global.json</b> در دسترس نیست"
    c2 = d.get("feodo", [])
    if not c2:
        return "✅ هیچ سرور C2 فعالی نیست"
    txt = f"🦠 <b>C2 Servers ({len(c2)})</b>\n\n"
    for x in c2[:15]:
        ip = x.get("ip", "?")
        port = x.get("port", "?")
        mw = x.get("malware", "?")
        cc = x.get("country", "??")
        txt += f"• <code>{esc(ip)}:{port}</code> — <b>{esc(mw)}</b> [{cc}]\n"
    return txt

def logs_text():
    d = logs_data()
    if not d:
        return "❌ <b>logs.json</b> در دسترس نیست"
    entries = d.get("entries", [])
    if not entries:
        return "📋 هیچ لاگی نیست"
    txt = f"📋 <b>آخرین {min(10, len(entries))} لاگ</b>\n\n"
    for e in entries[-10:]:
        sev = (e.get("sev") or "info").upper()
        src = e.get("src", "?")[:25]
        msg = (e.get("msg", "") or "")[:60]
        icon = {"ERROR": "🔴", "WARN": "🟡", "OK": "🟢", "INFO": "🔵"}.get(sev, "⚪")
        txt += f"{icon} <code>{esc(src)}</code>\n   {esc(msg)}\n"
    return txt

def dashboard_text():
    return """🔗 <b>VORIX DASHBOARD</b>

🌐 <a href="https://40004kaya-org.github.io/vorix-hybrid/vx7k2main/">داشبورد اصلی</a>
🌍 <a href="https://40004kaya-org.github.io/vorix-hybrid/vx7k2main/world.html">نقشه جهانی</a>
🔍 <a href="https://40004kaya-org.github.io/vorix-hybrid/vx7k2main/discover.html">Discover (Kibana)</a>
📊 <a href="https://40004kaya-org.github.io/vorix-hybrid/vx7k2main/metrics.html">Metrics</a>

⚠️ برای دسترسی، VPN روشن باشه
"""

# ─── MENU ──────────────────────────────────
def main_menu():
    return [
        [
            {"text": "🛡️ وضعیت", "callback_data": "status"},
            {"text": "🎯 حملات", "callback_data": "attacks"},
        ],
        [
            {"text": "🌐 جهانی", "callback_data": "global"},
            {"text": "🦠 C2", "callback_data": "c2"},
        ],
        [
            {"text": "📋 لاگ‌ها", "callback_data": "logs"},
            {"text": "🔗 داشبورد", "callback_data": "dashboard"},
        ],
        [
            {"text": "🔄 بروزرسانی", "callback_data": "refresh"},
        ],
    ]

def welcome():
    return """🛡️ <b>VORIX SECURITY BOT</b>

منوی کنترل VORIX:
• 🛡️ وضعیت لایه‌ها
• 🎯 حملات لوکال
• 🌐 حملات جهانی زنده
• 🦠 سرورهای C2
• 📋 لاگ‌های سیستم
• 🔗 لینک داشبورد

از دکمه‌ها استفاده کن 👇"""

# ─── HANDLERS ──────────────────────────────
def handle_command(chat_id, text):
    cmd = text.split()[0].lower() if text else ""
    
    if cmd in ("/start", "/menu", "/help"):
        send(chat_id, welcome(), main_menu())
    elif cmd == "/status":
        send(chat_id, status_text(), main_menu())
    elif cmd == "/attacks":
        send(chat_id, attacks_text(), main_menu())
    elif cmd == "/global" or cmd == "/world":
        send(chat_id, global_text(), main_menu())
    elif cmd == "/c2":
        send(chat_id, c2_text(), main_menu())
    elif cmd == "/logs":
        send(chat_id, logs_text(), main_menu())
    elif cmd == "/dashboard" or cmd == "/link":
        send(chat_id, dashboard_text(), main_menu())
    elif cmd == "/id":
        send(chat_id, f"🆔 Chat ID: <code>{chat_id}</code>")
    else:
        send(chat_id, "❓ دستور ناشناخته. /start رو بزن", main_menu())

def handle_callback(cb_id, chat_id, msg_id, data):
    answer_cb(cb_id)
    if data == "status":
        edit(chat_id, msg_id, status_text(), main_menu())
    elif data == "attacks":
        edit(chat_id, msg_id, attacks_text(), main_menu())
    elif data == "global":
        edit(chat_id, msg_id, global_text(), main_menu())
    elif data == "c2":
        edit(chat_id, msg_id, c2_text(), main_menu())
    elif data == "logs":
        edit(chat_id, msg_id, logs_text(), main_menu())
    elif data == "dashboard":
        edit(chat_id, msg_id, dashboard_text(), main_menu())
    elif data == "refresh":
        edit(chat_id, msg_id, status_text(), main_menu())

# ─── MAIN LOOP ─────────────────────────────
def main():
    print(f"🤖 VORIX Bot starting... (token: {TOKEN[:15]}...)")
    me = tg("getMe")
    if not me.get("ok"):
        print(f"❌ getMe failed: {me}")
        return
    print(f"✅ Bot: @{me['result']['username']}")
    
    offset = 0
    print("👂 Listening...")
    
    while True:
        try:
            r = tg("getUpdates", offset=offset, timeout=30)
            if not r.get("ok"):
                time.sleep(3)
                continue
            for u in r.get("result", []):
                offset = u["update_id"] + 1
                
                # پیام معمولی
                if "message" in u:
                    msg = u["message"]
                    chat_id = msg["chat"]["id"]
                    text = msg.get("text", "")
                    print(f"📩 [{chat_id}] {text[:50]}")
                    handle_command(chat_id, text)
                
                # کلیک دکمه
                elif "callback_query" in u:
                    cb = u["callback_query"]
                    cb_id = cb["id"]
                    chat_id = cb["message"]["chat"]["id"]
                    msg_id = cb["message"]["message_id"]
                    data = cb["data"]
                    print(f"🔘 [{chat_id}] {data}")
                    handle_callback(cb_id, chat_id, msg_id, data)
        except KeyboardInterrupt:
            print("\n👋 Bye")
            break
        except Exception as e:
            print(f"❌ Loop error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
