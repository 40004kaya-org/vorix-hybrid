#!/usr/bin/env python3
"""
VORIX Deep Link Handler
وقتی کاربر از داشبورد کلیک می‌کنه → ربات تحلیل می‌کنه چرا خرابه
"""
import os, subprocess, json
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

HOME = os.path.expanduser("~")
PHONE = os.path.join(HOME, "vorix-hybrid", "phone")
LOGS = os.path.join(PHONE, "logs")
LIVE = os.path.join(HOME, "vorix-hybrid", "docs", "data", "live.json")

LAYER_NAMES = {
  "L01":"Anti-Kill","L02":"Threat Intel","L03":"Behavioral","L04":"Auto-Block",
  "L05":"Data Quarantine","L06":"GeoIP Block","L07":"Net Behavior","L08":"Net Monitor",
  "L09":"Rate Limiter","L10":"Red Alert","L11":"DNS Sinkhole","L12":"Reverse DNS",
  "L13":"UA Filter","L15":"Fingerprint","L16":"Killswitch","L17":"Watchdog",
  "L18":"Backup Verifier","L19":"Password Leak","L21":"ML Anomaly",
  "L22":"Header Analysis","L23":"Cookie Anomaly","L24":"Session Hijack",
  "L25":"SSL Monitor","L26":"HSTS","L29":"Identity","L31":"Log Encryption",
  "L-FIM":"FIM","L-Root":"Rootkit","L-MC":"Multichannel","L-LF":"LiveFeed",
  "L-MITRE":"MITRE","L-Resp":"Response","L-Scor":"Scoring","L-Rep":"Reports",
  "L-Fore":"Forensics","L-Hash":"HashChain","L-Mock":"Mocker","L-Voice":"Voice",
  "L-Bot":"Bot","L-Sync":"Sync","L-Keep":"Keepalive","L-Agent":"Agent",
}

LAYER_FILES = {
  "L01":"layer01_selfdefense.py","L02":"layer02_threat_intel.py",
  "L03":"layer03_behavioral.py","L04":"layer04_auto_block.py",
  "L05":"layer05_data_quarantine.py","L06":"layer06_geoip_block.py",
  "L07":"layer07_network_behavior.py","L08":"layer08_network_monitor.py",
  "L09":"layer09_rate_limiter.py","L10":"layer10_red_alert.py",
  "L11":"layer11_dns_sinkhole.py","L12":"layer12_reverse_dns.py",
  "L13":"layer13_ua_filter.py","L15":"layer15_fingerprint.py",
  "L16":"layer16_killswitch.py","L17":"layer17_watchdog.py",
  "L18":"layer18_backup_verifier.py","L19":"layer19_password_leak.py",
  "L21":"layer21_ml_anomaly.py","L22":"layer22_header_analysis.py",
  "L23":"layer23_cookie_anomaly.py","L24":"layer24_session_hijack.py",
  "L25":"layer25_ssl_monitor.py","L26":"layer26_hsts.py",
  "L29":"layer29_30_identity.py","L31":"layer31_log_encryption.py",
  "L-FIM":"layer_fim.py","L-Root":"layer_rootkit.py",
  "L-MC":"layer_multichannel.py","L-LF":"layer_livefeed.py",
  "L-MITRE":"layer_mitre.py","L-Resp":"layer_response.py",
  "L-Scor":"layer_scoring.py","L-Rep":"layer_reports.py",
  "L-Fore":"layer_forensics.py","L-Hash":"layer_hashchain.py",
  "L-Mock":"layer_mocker.py","L-Voice":"layer_voice.py",
  "L-Bot":"vorix_bot.py","L-Sync":"sync_loop.sh",
  "L-Keep":"keepalive.sh","L-Agent":"agent.py",
}

LAYER_CMDS = {
  "layer01_selfdefense.py":"watch",
  "layer03_behavioral.py":"watch",
  "layer04_auto_block.py":"watch",
  "layer06_geoip_block.py":"watch",
  "layer08_network_monitor.py":"watch",
  "layer09_rate_limiter.py":"watch",
  "layer10_red_alert.py":"watch",
  "layer17_watchdog.py":"watch",
  "layer19_password_leak.py":"watch",
  "layer21_ml_anomaly.py":"watch",
  "layer25_ssl_monitor.py":"watch",
  "layer29_30_identity.py":"watch",
  "layer_fim.py":"watch",
  "layer_rootkit.py":"watch",
  "layer_multichannel.py":"watch",
  "layer_livefeed.py":"",
  "vorix_bot.py":"",
  "sync_loop.sh":"",
  "keepalive.sh":"",
  "agent.py":"",
}



# ─── Helper functions (sync) ───
import requests
HOME_T = os.path.expanduser("~")
TOKEN_T = open(os.path.join(HOME_T, "vorix/.tg-token")).read().strip() if os.path.exists(os.path.join(HOME_T, "vorix/.tg-token")) else ""
API_T = "https://api.telegram.org/bot" + TOKEN_T

def tg_send(chat_id, text, parse_mode=None, reply_markup=None):
    data = {"chat_id": chat_id, "text": text}
    if parse_mode: data["parse_mode"] = parse_mode
    if reply_markup: data["reply_markup"] = reply_markup
    try:
        r = requests.post(API_T + "/sendMessage", json=data, timeout=10)
        return r.json().get("result", {})
    except: return {}

def tg_edit(chat_id, message_id, text, parse_mode=None, reply_markup=None):
    data = {"chat_id": chat_id, "message_id": message_id, "text": text}
    if parse_mode: data["parse_mode"] = parse_mode
    if reply_markup: data["reply_markup"] = reply_markup
    try:
        r = requests.post(API_T + "/editMessageText", json=data, timeout=10)
        return r.json()
    except: return {}


def load_live():
    try:
        with open(LIVE) as f:
            return json.load(f)
    except:
        return {"layers": [], "stats": {}}


def get_layer_info(layer_id):
    """اطلاعات یه لایه از live.json"""
    data = load_live()
    for l in data.get("layers", []):
        if l["id"] == layer_id:
            return l
    return None


def check_process(layer_id):
    """آیا process در حال اجراست؟"""
    fname = LAYER_FILES.get(layer_id)
    if not fname:
        return False, None
    pattern = fname.replace(".py", "").replace(".sh", "")
    
    try:
        r = subprocess.run(["pgrep", "-f", pattern],
                          capture_output=True, text=True, timeout=3)
        pids = [p for p in r.stdout.strip().split("\n") if p]
        return (len(pids) > 0), (pids[0] if pids else None)
    except:
        return False, None


def get_recent_log(layer_id, lines=15):
    """آخرین خطوط لاگ"""
    fname = LAYER_FILES.get(layer_id)
    if not fname:
        return ""
    logfile = os.path.join(LOGS, fname + ".log")
    if not os.path.exists(logfile):
        return ""
    try:
        with open(logfile) as f:
            content = f.readlines()[-lines:]
        return "".join(content)
    except:
        return ""


def get_last_errors(layer_id, count=5):
    """آخرین خطاها"""
    fname = LAYER_FILES.get(layer_id)
    if not fname:
        return []
    logfile = os.path.join(LOGS, fname + ".log")
    if not os.path.exists(logfile):
        return []
    try:
        with open(logfile) as f:
            lines = f.readlines()[-200:]
        errors = [l.strip() for l in lines 
                  if "ERROR" in l or "Traceback" in l or "Exception" in l 
                  or "FAILED" in l or "FATAL" in l]
        return errors[-count:]
    except:
        return []


def diagnose(layer_id):
    """تشخیص دقیق مشکل"""
    info = get_layer_info(layer_id)
    running, pid = check_process(layer_id)
    fname = LAYER_FILES.get(layer_id, "?")
    name = LAYER_NAMES.get(layer_id, fname)
    
    # تعیین mode
    cmd = LAYER_CMDS.get(fname, "")
    mode = "watch" if cmd == "watch" else ("on-demand" if cmd == "" else cmd)
    
    # base result
    result = {
        "id": layer_id,
        "name": name,
        "file": fname,
        "mode": mode,
        "running": running,
        "pid": pid,
        "status": "unknown",
        "color": "gray",
        "problems": [],
        "suggestions": [],
        "errors": [],
    }
    
    # ─── ۱. چک وجود فایل ───
    filepath = os.path.join(PHONE, fname)
    if not os.path.exists(filepath):
        result["status"] = "missing"
        result["color"] = "red"
        result["problems"].append(f"❌ فایل {fname} وجود نداره")
        result["suggestions"].append("فایل گم‌شده — باید بازیابی شه")
        return result
    
    # ─── ۲. چک اجرا ───
    if running:
        # فعال — چک خطا
        errors = get_last_errors(layer_id, 3)
        if errors:
            result["status"] = "warning"
            result["color"] = "orange"
            result["errors"] = errors
            result["problems"].append(f"⚠️ فعاله ولی {len(errors)} خطا در لاگ")
            result["suggestions"].append("لاگ رو ببین و fix کن")
        else:
            result["status"] = "active"
            result["color"] = "green"
    else:
        # غیرفعال
        if mode == "watch":
            result["status"] = "down"
            result["color"] = "red"
            result["problems"].append(f"❌ لایه mode=watch هست ولی اجرا نمی‌شه")
            result["suggestions"].append("باید دستی راه بندازی یا مشکل رو fix کنی")
            
            # چک خطاهای اخیر
            errors = get_last_errors(layer_id, 5)
            if errors:
                result["errors"] = errors
                result["problems"].append(f"📛 {len(errors)} خطا در آخرین اجرا")
        else:
            result["status"] = "standby"
            result["color"] = "yellow"
            result["problems"].append("ℹ️ on-demand هست — فقط با event فعال می‌شه")
            result["suggestions"].append("نیاز به اجرا نیست مگه event بیاد")
    
    return result


def format_status_message(d):
    """پیام نهایی"""
    emoji = {
        "green": "🟢", "yellow": "🟡", "orange": "🟠",
        "red": "🔴", "gray": "⚫"
    }.get(d["color"], "❓")
    
    label = {
        "active": "فعال و سالم",
        "warning": "فعال با خطا",
        "standby": "آماده (on-demand)",
        "down": "قطع شده",
        "missing": "فایل گم‌شده",
    }.get(d["status"], "نامشخص")
    
    text = f"{emoji} <b>{d['id']} — {d['name']}</b>\n"
    text += "━━━━━━━━━━━━━━━━━━━━\n"
    text += f"📁 <code>{d['file']}</code>\n"
    text += f"🎯 mode: <code>{d['mode']}</code>\n"
    text += f"📍 وضعیت: <b>{label}</b>\n"
    if d["pid"]:
        text += f"🔢 PID: <code>{d['pid']}</code>\n"
    
    # مشکلات
    if d["problems"]:
        text += "\n🔍 <b>مشکلات:</b>\n"
        for p in d["problems"]:
            text += f"  {p}\n"
    
    # خطاها
    if d["errors"]:
        text += "\n📛 <b>آخرین خطاها:</b>\n"
        for err in d["errors"][:3]:
            err_short = err[:100] + ("..." if len(err) > 100 else "")
            text += f"  <code>{err_short}</code>\n"
    
    # پیشنهاد
    if d["suggestions"]:
        text += "\n💡 <b>پیشنهاد:</b>\n"
        for s in d["suggestions"]:
            text += f"  • {s}\n"
    
    return text


def build_actions(layer_id, status):
    """دکمه‌های اکشن"""
    rows = []
    
    if status in ("down", "missing"):
        rows.append([
            InlineKeyboardButton("🔧 راه‌اندازی مجدد", callback_data=f"act:restart:{layer_id}"),
            InlineKeyboardButton("📋 مشاهده لاگ", callback_data=f"act:log:{layer_id}"),
        ])
    elif status == "warning":
        rows.append([
            InlineKeyboardButton("🔄 ریستارت", callback_data=f"act:restart:{layer_id}"),
            InlineKeyboardButton("📋 لاگ کامل", callback_data=f"act:log:{layer_id}"),
        ])
    elif status == "standby":
        rows.append([
            InlineKeyboardButton("▶️ اجرا کن", callback_data=f"act:start:{layer_id}"),
            InlineKeyboardButton("📋 وضعیت", callback_data=f"act:refresh:{layer_id}"),
        ])
    else:  # active
        rows.append([
            InlineKeyboardButton("🔄 ریستارت", callback_data=f"act:restart:{layer_id}"),
            InlineKeyboardButton("⏹️ قطع", callback_data=f"act:stop:{layer_id}"),
        ])
    
    rows.append([
        InlineKeyboardButton("🔙 منوی اصلی", callback_data="act:menu"),
    ])
    
    return InlineKeyboardMarkup(rows)


def handle_deep_link(chat_id, arg):
    """هندل کردن start با argument"""
    # layer_L04 → تحلیل
    # fix_L04 → راه‌اندازی
    # start_L04 → راه‌اندازی
    # stop_L04 → قطع
    # log_L04 → لاگ
    
    parts = arg.split("_", 1)
    if len(parts) != 2:
        tg_send(chat_id,
            f"❓ دستور ناشناخته: <code>{arg}</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    action = parts[0]  # layer, fix, start, stop, log
    layer_id = parts[1]  # L04, L-Sync, ...
    
    if action == "layer":
        # تحلیل کامل
        d = diagnose(layer_id)
        text = format_status_message(d)
        kb = build_actions(layer_id, d["status"])
        tg_send(chat_id,text, parse_mode=ParseMode.HTML, reply_markup=kb)
    
    elif action in ("fix", "start"):
        # راه‌اندازی
        msg = tg_send(chat_id,
            f"⏳ در حال راه‌اندازی <b>{layer_id}</b>...",
            parse_mode=ParseMode.HTML
        )
        ok, output = restart_layer(layer_id)
        if ok:
            tg_edit(chat_id, msg_id,
                f"✅ <b>{layer_id}</b> راه‌اندازی شد\n\n"
                f"<code>{output[:200]}</code>",
                parse_mode=ParseMode.HTML
            )
        else:
            tg_edit(chat_id, msg_id,
                f"❌ خطا در راه‌اندازی <b>{layer_id}</b>\n\n"
                f"<code>{output[:300]}</code>",
                parse_mode=ParseMode.HTML
            )
    
    elif action == "stop":
        ok, output = stop_layer(layer_id)
        if ok:
            tg_send(chat_id,
                f"⏹️ <b>{layer_id}</b> قطع شد",
                parse_mode=ParseMode.HTML
            )
        else:
            tg_send(chat_id,
                f"❌ خطا: {output[:200]}",
                parse_mode=ParseMode.HTML
            )
    
    elif action == "log":
        log = get_recent_log(layer_id, 20)
        if log:
            text = f"📋 <b>لاگ {layer_id}</b>\n\n<pre>{log[-1500:]}</pre>"
        else:
            text = f"📭 لاگ <b>{layer_id}</b> خالیه"
        tg_send(chat_id,text, parse_mode=ParseMode.HTML)
    
    else:
        tg_send(chat_id,f"❓ دستور ناشناخته: {arg}")


def restart_layer(layer_id):
    """ریستارت یه لایه"""
    fname = LAYER_FILES.get(layer_id)
    if not fname:
        return False, f"فایل {layer_id} ناشناخته"
    
    filepath = os.path.join(PHONE, fname)
    if not os.path.exists(filepath):
        return False, f"فایل {fname} وجود نداره"
    
    # اول kill کن
    pattern = fname.replace(".py", "").replace(".sh", "")
    subprocess.run(["pkill", "-9", "-f", pattern], timeout=3)
    
    # بعد start کن
    cmd = LAYER_CMDS.get(fname, "")
    try:
        if fname.endswith(".sh"):
            subprocess.Popen(["bash", fname],
                           cwd=PHONE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif cmd:
            subprocess.Popen(["python", fname, cmd],
                           cwd=PHONE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(["python", fname],
                           cwd=PHONE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True, f"{fname} restart شد"
    except Exception as e:
        return False, str(e)


def stop_layer(layer_id):
    """قطع یه لایه"""
    fname = LAYER_FILES.get(layer_id)
    if not fname:
        return False, f"فایل {layer_id} ناشناخته"
    
    pattern = fname.replace(".py", "").replace(".sh", "")
    try:
        r = subprocess.run(["pkill", "-9", "-f", pattern], timeout=3)
        return True, "قطع شد"
    except Exception as e:
        return False, str(e)
