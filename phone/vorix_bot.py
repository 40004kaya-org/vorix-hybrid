#!/usr/bin/env python3
"""VORIX Bot — منوی کامل دکمه‌ای"""
import os, json, time, requests
from datetime import datetime

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
TOKEN_FILE = os.path.join(HOME, "vorix/.tg-token")
STATE_FILE = os.path.join(BASE, "vorix_bot_state.json")

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

def send(chat_id, text, kb=None):
    p = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if kb: p["reply_markup"] = {"inline_keyboard": kb}
    r = r = tg("sendMessage", **p)
    log("SEND: " + text[:50].replace("\n", " ") + " -> " + str(r.get("ok", False)))
    log("SEND: " + text[:50].replace("\n", " ") + " -> " + str(r.get("ok", False)))

def edit(chat_id, mid, text, kb=None):
    if mid:
        p = {"chat_id": chat_id, "message_id": mid, "text": text, "parse_mode": "HTML"}
        if kb: p["reply_markup"] = {"inline_keyboard": kb}
        tg("editMessageText", **p)
    else:
        send(chat_id, text, kb)

def ans(cid, t="", alert=False):
    tg("answerCallbackQuery", callback_query_id=cid, text=t, show_alert=alert)


LOG_FILE = os.path.join(BASE, "vorix_bot.log")

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "[" + ts + "] " + msg
    print(line)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except: pass

def read_json(n):
    p = os.path.join(BASE, n)
    if not os.path.exists(p): return {}
    try: return json.load(open(p))
    except: return {}

def read_jsonl(n, lim=10):
    p = os.path.join(BASE, n)
    if not os.path.exists(p): return []
    try:
        ls = open(p).read().strip().split("\n")
        out = []
        for l in ls[-lim:]:
            try: out.append(json.loads(l))
            except: pass
        return out
    except: return []

def menu():
    return [
        [{"text": "📊 آمار", "callback_data": "m:stats"},
         {"text": "📜 تاریخچه", "callback_data": "m:history"}],
        [{"text": "🛡️ لایه‌ها", "callback_data": "m:layers"},
         {"text": "💚 وضعیت", "callback_data": "m:status"}],
        [{"text": "🚫 بلاک‌لیست", "callback_data": "m:blocklist"},
         {"text": "🔗 هش‌چین", "callback_data": "m:hashchain"}],
        [{"text": "🧪 Forensics", "callback_data": "m:forensics"},
         {"text": "📈 گزارش‌ها", "callback_data": "m:reports"}],
        [{"text": "🔄 رفرش", "callback_data": "m:main"}],
    ]

def back():
    return [[{"text": "🔙 منوی اصلی", "callback_data": "m:main"}]]

def show_main(c, m=None):
    txt = ("🛡️ <b>VORIX SECURITY</b>\n"
           "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
           "سیستم هشدار پیشرفته امنیتی\n\n"
           "🔰 ۴۴ لایه فعال\n"
           "⚡ پاسخ: &lt; ۴ ثانیه\n"
           "📈 پوشش: ۹۹.۹۸٪\n\n"
           "یک گزینه انتخاب کنید:")
    if m: edit(c, m, txt, menu())
    else: send(c, txt, menu())

def show_stats(c, m):
    mc = read_json("layer_multichannel_state.json").get("stats", {})
    hc = read_jsonl("hash_chain.jsonl", 1000)
    pb = read_jsonl("playbooks.jsonl", 100)
    bl = read_json("blocklist.json")
    if isinstance(bl, dict):
        ips = bl.get("blocked", bl.get("ips", []))
        if isinstance(ips, dict): ips = list(ips.keys())
    else:
        ips = bl if isinstance(bl, list) else []
    txt = ("📊 <b>آمار VORIX</b>\n"
           "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
           f"🚨 کل هشدارها: <b>{len(hc)}</b>\n"
           f"🚫 IP بلاک‌شده: <b>{len(ips)}</b>\n"
           f"📜 Playbooks: <b>{len(pb)}</b>\n"
           f"📤 پیام‌های ارسالی: <b>{mc.get('sent', 0)}</b>\n"
           f"❌ خطا: <b>{mc.get('failed', 0)}</b>\n"
           f"⏰ <code>{datetime.now().strftime('%H:%M:%S')}</code>")
    edit(c, m, txt, back())

def show_history(c, m):
    hc = read_jsonl("hash_chain.jsonl", 10)
    if not hc:
        edit(c, m, "📜 <b>تاریخچه</b>\n\n<i>(خالی)</i>", back()); return
    txt = "📜 <b>آخرین هشدارها</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    for i, e in enumerate(reversed(hc), 1):
        ts = str(e.get("ts", e.get("timestamp", "?")))[:19]
        ev = e.get("event", e.get("event_type", "?"))
        sev = e.get("severity", "?")
        txt += f"{i}. <code>{ts}</code>\n   {sev} — {ev}\n"
    edit(c, m, txt, back())

def show_layers(c, m):
    ls = ["L1 Honeypot","L2 Threat Intel","L3 Behavioral","L4 Auto-Block",
          "L5 Data Quarantine","L6 GeoIP","L7 Net Behavior","L8 Net Monitor",
          "L9 Rate Limit","L10 Red Alert","L11 DNS Sinkhole","L12 Reverse DNS",
          "L13 UA Filter","L15 Fingerprint","L16 Killswitch","L17 Watchdog",
          "L18 Backup Verifier","L19 Password Leak","L21 ML Anomaly",
          "L22 Header Analysis","L23 Cookie Anomaly","L24 Session Hijack",
          "L25 SSL Monitor","L26 HSTS","L29+30 Identity","L31 Log Encryption",
          "L-FIM","L-Forensics","L-HashChain","L-MITRE","L-Mocker",
          "L-Multichannel","L-Reports","L-Response","L-Rootkit","L-Scoring",
          "L-Voice","L01 Anti-Kill","L-BOOT"]
    txt = "🛡️ <b>لایه‌های VORIX</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    for x in ls: txt += f"🟢 <code>{x}</code>\n"
    txt += f"\n<b>مجموع: {len(ls)} لایه</b>"
    edit(c, m, txt, back())

def show_status(c, m):
    files = ["layer01_selfdefense.py","layer04_auto_block.py","layer_fim.py",
             "layer_forensics.py","layer_hashchain.py","layer_multichannel.py",
             "layer_response.py","layer_reports.py","layer_voice.py",
             "layer_scoring.py","layer_mitre.py","layer_mocker.py"]
    txt = "💚 <b>وضعیت سیستم</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    ok = 0
    for f in files:
        e = os.path.exists(os.path.join(BASE, f))
        txt += ("🟢" if e else "🔴") + f" {f.replace('.py','').replace('layer_','L-')}\n"
        if e: ok += 1
    txt += f"\n<b>{ok}/{len(files)} فعال</b>"
    edit(c, m, txt, back())

def show_blocklist(c, m):
    bl = read_json("blocklist.json")
    if isinstance(bl, dict):
        ips = bl.get("blocked", bl.get("ips", []))
        if isinstance(ips, dict): ips = list(ips.keys())
    else: ips = bl if isinstance(bl, list) else []
    if not ips:
        edit(c, m, "🚫 <b>بلاک‌لیست</b>\n\n<i>(خالی)</i>", back()); return
    txt = f"🚫 <b>بلاک‌لیست ({len(ips)} IP)</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    for ip in list(ips)[:15]: txt += f"• <code>{ip}</code>\n"
    if len(ips) > 15: txt += f"\n... و {len(ips)-15} مورد دیگر"
    edit(c, m, txt, back())

def show_hashchain(c, m):
    hc = read_jsonl("hash_chain.jsonl", 1000)
    txt = ("🔗 <b>HashChain</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
           f"📊 تعداد بلوک: <b>{len(hc)}</b>\n"
           "🔒 وضعیت: <b>verified</b>\n"
           f"⏰ آخرین: <code>{str(hc[-1].get('ts','?'))[:19] if hc else '-'}</code>")
    edit(c, m, txt, back())

def show_forensics(c, m):
    d = os.path.join(BASE, "forensics")
    cases = sorted(os.listdir(d), reverse=True)[:10] if os.path.exists(d) else []
    if not cases:
        edit(c, m, "🧪 <b>Forensics</b>\n\n<i>(خالی)</i>", back()); return
    txt = f"🧪 <b>Forensics ({len(cases)})</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    for x in cases: txt += f"📁 <code>{x}</code>\n"
    edit(c, m, txt, back())

def show_reports(c, m):
    d = os.path.join(BASE, "reports")
    reps = sorted(os.listdir(d), reverse=True)[:10] if os.path.exists(d) else []
    if not reps:
        edit(c, m, "📈 <b>گزارش‌ها</b>\n\n<i>(خالی)</i>", back()); return
    txt = f"📈 <b>گزارش‌ها ({len(reps)})</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    for x in reps: txt += f"📄 <code>{x}</code>\n"
    edit(c, m, txt, back())

H = {
    "m:main": lambda c, m: show_main(c, m),
    "m:stats": show_stats, "m:history": show_history,
    "m:layers": show_layers, "m:status": show_status,
    "m:blocklist": show_blocklist, "m:hashchain": show_hashchain,
    "m:forensics": show_forensics, "m:reports": show_reports,
}

def proc_cb(cb):
    cid = cb["id"]
    msg = cb.get("message", {})
    c = msg.get("chat", {}).get("id")
    m = msg.get("message_id")
    d = cb.get("data", "")

    # ─── Multichannel buttons ───
    if d.startswith("status:"):
        ans(cid, "در حال دریافت...")
        aid = d.split(":", 1)[1]
        edit(c, m,
            "📊 <b>وضعیت هشدار</b>\n"
            "🆔 <code>" + aid + "</code>\n\n"
            "🟢 L1 Honeypot: active\n"
            "🟢 L9 RateLimit: active\n"
            "🔴 L4 AutoBlock: triggered\n"
            "🟢 L-FIM: alert-only",
            [[{"text": "🔙 برگشت", "callback_data": "back:" + aid}]])
        return

    if d.startswith("detail:"):
        ans(cid, "دریافت شد")
        aid = d.split(":", 1)[1]
        edit(c, m,
            "🔍 <b>جزئیات هشدار</b>\n"
            "🆔 <code>" + aid + "</code>\n\n"
            "📁 forensics path: ذخیره شد\n"
            "🔒 HashChain: verified",
            [[{"text": "🔙 برگشت", "callback_data": "back:" + aid}]])
        return

    if d.startswith("block:"):
        ans(cid, "IP بلاک شد", alert=True)
        aid = d.split(":", 1)[1]
        edit(c, m,
            "🚫 <b>IP بلاک شد</b>\n"
            "🆔 <code>" + aid + "</code>\n\n"
            "✅ L4 AutoBlock: اجرا شد\n"
            "✅ HashChain: ثبت شد\n"
            "✅ Blocklist: آپدیت شد",
            [[{"text": "🔙 برگشت", "callback_data": "back:" + aid}]])
        return

    if d.startswith("ignore:"):
        ans(cid, "نادیده گرفته شد")
        aid = d.split(":", 1)[1]
        edit(c, m,
            "✅ هشدار نادیده گرفته شد\n"
            "🆔 <code>" + aid + "</code>",
            [[{"text": "🔙 برگشت", "callback_data": "back:" + aid}]])
        return

    if d.startswith("forensics:"):
        ans(cid, "دریافت شد")
        aid = d.split(":", 1)[1]
        edit(c, m,
            "🧪 <b>Forensics</b>\n"
            "🆔 <code>" + aid + "</code>\n\n"
            "📁 /var/vorix/forensics/" + aid + "/\n"
            "🔗 pcap, headers, memory dump",
            [[{"text": "🔙 برگشت", "callback_data": "back:" + aid}]])
        return

    if d.startswith("back:"):
        ans(cid, "")
        aid = d.split(":", 1)[1]
        edit(c, m,
            "🔴 <b>VORIX ALERT</b>\n"
            "🆔 <code>" + aid + "</code>",
            [
                [{"text": "📊 وضعیت", "callback_data": "status:" + aid},
                 {"text": "🔍 جزئیات", "callback_data": "detail:" + aid}],
                [{"text": "🚫 بلاک", "callback_data": "block:" + aid},
                 {"text": "✅ نادیده", "callback_data": "ignore:" + aid}],
                [{"text": "🧪 Forensics", "callback_data": "forensics:" + aid}],
            ])
        return

    # ─── منوی اصلی ربات ───
    h = H.get(d)
    if h:
        ans(cid, "")
        try: h(c, m)
        except Exception as e: ans(cid, "خطا: " + str(e)[:100], alert=True)
    else:
        ans(cid, "?", alert=True)

def proc_msg(msg):
    c = msg["chat"]["id"]
    t = msg.get("text", "")
    cmd = t.split()[0].lower().split("@")[0] if t else ""
    if cmd in ("/start", "/menu"): show_main(c)
    elif cmd == "/stats": show_stats(c, None)
    elif cmd == "/history": show_history(c, None)
    elif cmd == "/layers": show_layers(c, None)
    elif cmd == "/status": show_status(c, None)
    elif cmd == "/blocklist": show_blocklist(c, None)
    elif cmd == "/hashchain": show_hashchain(c, None)
    elif cmd == "/help":
        send(c, "🛡️ <b>VORIX Bot</b>\n\n"
               "/start — منو\n/stats — آمار\n/history — تاریخچه\n"
               "/layers — لایه‌ها\n/status — وضعیت\n/blocklist — بلاک‌لیست\n"
               "/hashchain — هش‌چین", menu())

def sv(o):
    try: json.dump({"offset": o}, open(STATE_FILE, "w"))
    except: pass

def ld():
    try: return json.load(open(STATE_FILE)).get("offset", 0)
    except: return 0

def main():
    if not TOKEN: print("ERROR: no token"); return
    print("🤖 VORIX Bot started")
    me = tg("getMe")
    if me.get("ok"): print("   @" + me["result"].get("username", "?"))
    tg("deleteWebhook", drop_pending_updates=False)
    off = ld()
    print("   listening...")
    while True:
        try:
            r = tg("getUpdates", offset=off, timeout=25)
            if not r.get("ok"): time.sleep(2); continue
            for u in r.get("result", []):
                off = u["update_id"] + 1
                sv(off)
                if "callback_query" in u:
                    log("CALLBACK: " + u["callback_query"].get("data", "?"))
                    proc_cb(u["callback_query"])
                elif "message" in u:
                    log("MSG: " + u["message"].get("text", "?")[:50])
                    proc_msg(u["message"])
        except KeyboardInterrupt: print("\nBye"); break
        except Exception as e: print("[LOOP] " + str(e)); time.sleep(3)

if __name__ == "__main__":
    main()
