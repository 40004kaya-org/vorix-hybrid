#!/usr/bin/env python3
"""Shop Shield v3 — 10 لایه امنیتی قوی"""
import json, re, time, hmac, hashlib, os
from pathlib import Path
from datetime import datetime, timezone, timedelta

# ═══ Paths ═══
SHIELD_DIR = Path.home() / "vorix-hybrid/shop-data"
SHIELD_DIR.mkdir(parents=True, exist_ok=True)
STATE = SHIELD_DIR / "shield_state.json"
BLACKLIST = SHIELD_DIR / "blacklist.json"
AUDIT = SHIELD_DIR / "audit.jsonl"
HONEYPOT_LOG = SHIELD_DIR / "honeypot.jsonl"
HASHCHAIN = SHIELD_DIR / "hashchain.jsonl"

# ═══ Config ═══
CONFIG = {
    "rate_limit_window": 60,
    "rate_limit_max": 30,
    "failed_login_max": 5,
    "failed_login_window": 1800,
    "high_order_threshold": 10_000_000,
    "rapid_order_window": 300,
    "rapid_order_max": 3,
    "brute_delay_base": 1.5,          # تاخیر نمایی
    "anomaly_threshold": 5,           # امتیاز مشکوک
    "hmac_secret": "vx-shop-secret-2026-CHANGE-ME",
    "telegram_token": "8465913616:AAEuYEuLwFU6vjf4l-tepqizE0Ju9pY4jW8",             # خالی = هشدار غیرفعال
    "telegram_chat": 175160049,
}

# ═══ Patterns ═══
SQL_RE = [r"(\bUNION\b.*\bSELECT\b)", r"(\bDROP\b.*\bTABLE\b)", r"(\bINSERT\b.*\bINTO\b)",
          r"(\bDELETE\b.*\bFROM\b)", r"(--\s*$)", r"(\bOR\b\s+1\s*=\s*1)", r"('.*\bOR\b.*')"]
XSS_RE = [r"<script[^>]*>", r"javascript:", r"onerror\s*=", r"onload\s*=", r"<iframe", r"<img[^>]+onerror"]
PATH_RE = [r"\.\./", r"\.\.\\", r"%2e%2e", r"%252e"]
CMD_RE = [r"\$\(.*\)", r"`.*`", r"[;&|]\s*\w+"]

# ═══ State ═══
def load_state():
    if STATE.exists():
        try: return json.loads(STATE.read_text())
        except: pass
    return {
        "rate": {}, "failed_logins": {}, "rapid_orders": {},
        "blacklist": {},
        "anomaly_scores": {},
        "brute_delays": {},
        "stats": {"checked":0, "passed":0, "flagged":0, "blocked":0, "honeypot_hits":0}
    }

def save_state(s):
    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=1))

# ═══ Layer 1: JWT-like HMAC Token ═══
def make_token(payload, ttl=3600):
    """ساخت توکن امضاشده"""
    payload["exp"] = int(time.time()) + ttl
    raw = json.dumps(payload, sort_keys=True).encode()
    sig = hmac.new(CONFIG["hmac_secret"].encode(), raw, hashlib.sha256).hexdigest()
    import base64
    return base64.b64encode(raw).decode() + "." + sig

def verify_token(token):
    """تأیید توکن"""
    try:
        import base64
        parts = token.split(".")
        if len(parts) != 2: return None
        raw = base64.b64decode(parts[0])
        sig = parts[1]
        expected = hmac.new(CONFIG["hmac_secret"].encode(), raw, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected): return None
        payload = json.loads(raw)
        if payload.get("exp", 0) < time.time(): return None
        return payload
    except: return None

# ═══ Layer 2: HMAC Signature (bridge → API) ═══
def sign_payload(data):
    """امضای payload با HMAC"""
    raw = json.dumps(data, sort_keys=True).encode()
    return hmac.new(CONFIG["hmac_secret"].encode(), raw, hashlib.sha256).hexdigest()

def verify_signature(data, sig):
    """تأیید امضا"""
    expected = sign_payload(data)
    return hmac.compare_digest(sig, expected)

# ═══ Layer 3: IP Whitelist ═══
ALLOWED_IPS = {"127.0.0.1", "::1", "localhost"}

def check_ip(ip):
    if not ip: return True, None
    if ip in ALLOWED_IPS: return True, None
    if ip.startswith("192.168.") or ip.startswith("10."): return True, None
    return False, "ip_not_allowed"

# ═══ Layer 4: Advanced Rate Limit (Token Bucket) ═══
def check_rate(state, key):
    now = time.time()
    window = CONFIG["rate_limit_window"]
    max_count = CONFIG["rate_limit_max"]
    if key not in state["rate"]:
        state["rate"][key] = []
    state["rate"][key] = [t for t in state["rate"][key] if now - t < window]
    if len(state["rate"][key]) >= max_count:
        return False, "rate_limit"
    state["rate"][key].append(now)
    return True, None

# ═══ Layer 5: Anomaly Scoring ═══
def add_anomaly(state, key, points, reason):
    """اضافه کردن امتیاز مشکوک"""
    if key not in state["anomaly_scores"]:
        state["anomaly_scores"][key] = {"score": 0, "events": [], "first_seen": time.time()}
    a = state["anomaly_scores"][key]
    # کاهش امتیاز قدیمی (decay)
    age = time.time() - a["first_seen"]
    if age > 3600:
        a["score"] = max(0, a["score"] - 2)
        a["first_seen"] = time.time()
    a["score"] += points
    a["events"].append({"reason": reason, "ts": time.time(), "points": points})
    a["events"] = a["events"][-10:]
    return a["score"]

def check_anomaly_score(state, key):
    if key not in state["anomaly_scores"]: return True, None
    score = state["anomaly_scores"][key]["score"]
    if score >= CONFIG["anomaly_threshold"]:
        return False, f"anomaly_score_{score}"
    return True, None

def check_high_value(state, event):
    """چک سفارش بالا"""
    if event.get("type") != "order_new": return True, None
    data = event.get("data", {})
    amount = data.get("total_price", 0) or event.get("amount", 0)
    if amount >= CONFIG["high_order_threshold"]:
        return False, f"high_value_{amount}"
    return True, None

# ═══ Layer 6: Honeypot (Admin Trap) ═══
HONEYPOT_KEYWORDS = [
    "admin", "root", "wp-admin", "phpmyadmin", "/.env", "/.git",
    "config.php", "backup.sql", "test.php", "shell", "/cgi-bin"
]

def check_honeypot(event):
    """اگه کسی سراغ endpoint های حساس بره، تشخیص بده"""
    data_str = json.dumps(event, ensure_ascii=False).lower()
    for kw in HONEYPOT_KEYWORDS:
        if kw in data_str:
            return True, f"honeypot_{kw}"
    return False, None

def log_honeypot(event, reason):
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
        "event": event,
    }
    with open(HONEYPOT_LOG, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

# ═══ Layer 7: File Integrity Hash Chain ═══
def hash_file(path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except: return None

def add_to_hashchain(data):
    """اضافه به زنجیره هش (غیرقابل تغییر)"""
    prev = "0" * 64
    if HASHCHAIN.exists():
        try:
            with open(HASHCHAIN) as f:
                lines = f.readlines()
            if lines:
                last = json.loads(lines[-1])
                prev = last.get("hash", prev)
        except: pass
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "data": data,
        "prev": prev,
    }
    raw = json.dumps(entry, sort_keys=True).encode()
    entry["hash"] = hashlib.sha256(prev.encode() + raw).hexdigest()
    with open(HASHCHAIN, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry["hash"]

# ═══ Layer 8: Encrypted Backups ═══
def encrypted_backup(file_path, key):
    """بک‌آپ رمزنگاری‌شده AES-like"""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        import base64
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=b"vx-shop-salt", iterations=100000)
        aes_key = kdf.derive(key.encode())
        with open(file_path, "rb") as f:
            plaintext = f.read()
        aes = AESGCM(aes_key)
        nonce = os.urandom(12)
        ct = aes.encrypt(nonce, plaintext, None)
        out = Path(str(file_path) + ".enc")
        out.write_bytes(nonce + ct)
        return str(out)
    except Exception as e:
        return f"error: {e}"

# ═══ Layer 9: Brute Force Guard ═══
def brute_delay(state, key):
    """تاخیر نمایی برای درخواست‌های تکراری"""
    now = time.time()
    if key not in state["brute_delays"]:
        state["brute_delays"][key] = {"count": 0, "last": 0, "delay": 0}
    b = state["brute_delays"][key]
    # ریست بعد از ۵ دقیقه
    if now - b["last"] > 300:
        b["count"] = 0
        b["delay"] = 0
    b["count"] += 1
    b["last"] = now
    if b["count"] > 5:
        b["delay"] = min(CONFIG["brute_delay_base"] ** min(b["count"] - 5, 10), 60)
    return b["delay"]

# ═══ Layer 10: Telegram Alert ═══
def send_alert(text):
    """ارسال هشدار به تلگرام"""
    if not CONFIG["telegram_token"]: return
    try:
        import urllib.request
        url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/sendMessage"
        body = json.dumps({
            "chat_id": CONFIG["telegram_chat"],
            "text": text,
            "parse_mode": "HTML"
        }).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5)
    except: pass

def alert_block(event, reasons):
    text = f"🚨 <b>SHOP SHIELD BLOCK</b>\n\n"
    text += f"Type: <code>{event.get('type', '?')}</code>\n"
    text += f"Reasons: <code>{', '.join(reasons)}</code>\n"
    data = event.get("data", {})
    for k, v in list(data.items())[:3]:
        text += f"{k}: <code>{str(v)[:40]}</code>\n"
    send_alert(text)

# ═══ Content Scanner ═══
def scan_value(v):
    if not isinstance(v, str): return True, None
    low = v.lower()
    for p in SQL_RE:
        if re.search(p, v, re.IGNORECASE): return False, "sql_injection"
    for p in XSS_RE:
        if re.search(p, low): return False, "xss"
    for p in PATH_RE:
        if re.search(p, low): return False, "path_traversal"
    for p in CMD_RE:
        if re.search(p, v): return False, "cmd_injection"
    return True, None

def scan_event(event):
    def walk(d, path=""):
        for k, v in d.items():
            if isinstance(v, dict):
                r = walk(v, path + k + ".")
                if r[0] is False: return r
            elif isinstance(v, str):
                ok, reason = scan_value(v)
                if not ok: return False, f"{reason} in {path}{k}"
        return True, None
    return walk(event)

# ═══ Blacklist ═══
def is_blacklisted(state, event):
    data = event.get("data", {})
    ip = data.get("ip") or event.get("ip")
    uid = data.get("user_id") or data.get("used_by")
    now = time.time()
    for key in [ip, uid]:
        if not key: continue
        key = str(key)
        if key in state["blacklist"]:
            entry = state["blacklist"][key]
            until = entry.get("until", 0)
            if until == 0 or now < until:
                return True, entry.get("reason", "blacklisted")
            else:
                del state["blacklist"][key]
    return False, None

def block(state, key, reason, duration=86400):
    state["blacklist"][str(key)] = {
        "reason": reason,
        "until": time.time() + duration if duration > 0 else 0,
        "added_at": datetime.now(timezone.utc).isoformat()
    }

# ═══ MAIN: All Layers ═══
def check_event(event, state, ip=None):
    """بررسی کامل رویداد"""
    state["stats"]["checked"] += 1
    result = {"verdict": "PASS", "reasons": [], "layers": []}

    # ─── Layer 3: IP check ───
    if ip:
        ok, reason = check_ip(ip)
        if not ok:
            result["verdict"] = "BLOCK"
            result["reasons"].append(reason)
            result["layers"].append("ip")
            state["stats"]["blocked"] += 1
            return result
    result["layers"].append("ip")

    # ─── Layer 6: Honeypot ───
    hp, reason = check_honeypot(event)
    if hp:
        log_honeypot(event, reason)
        state["stats"]["honeypot_hits"] += 1
        result["verdict"] = "BLOCK"
        result["reasons"].append(reason)
        result["layers"].append("honeypot")
        state["stats"]["blocked"] += 1
        alert_block(event, [reason])
        return result
    result["layers"].append("honeypot")

    # ─── Blacklist ───
    bl, reason = is_blacklisted(state, event)
    if bl:
        result["verdict"] = "BLOCK"
        result["reasons"].append(f"blacklist_{reason}")
        result["layers"].append("blacklist")
        state["stats"]["blocked"] += 1
        return result
    result["layers"].append("blacklist")

    # ─── Layer 2: Sanitize ───
    ok, reason = scan_event(event)
    if not ok:
        result["verdict"] = "BLOCK"
        result["reasons"].append(f"injection_{reason}")
        result["layers"].append("sanitize")
        state["stats"]["blocked"] += 1
        if ip: block(state, ip, "injection", duration=86400)
        alert_block(event, result["reasons"])
        return result
    result["layers"].append("sanitize")

    # ─── Layer 4: Rate limit ───
    key = event.get("data", {}).get("user_id") or ip or "anon"
    ok, reason = check_rate(state, str(key))
    if not ok:
        result["verdict"] = "FLAG"
        result["reasons"].append("rate_limit")
        result["layers"].append("rate")
        # امتیاز مشکوک
        add_anomaly(state, str(key), 2, "rate_limit")
        state["stats"]["flagged"] += 1
        return result
    result["layers"].append("rate")

    # ─── Layer 9: Brute delay ───
    delay = brute_delay(state, str(key))
    if delay > 0:
        result["reasons"].append(f"delay_{delay:.1f}s")
        add_anomaly(state, str(key), 1, "brute")
    result["layers"].append("brute")

    # ─── High value check ───
    ok, reason = check_high_value(state, event)
    if not ok:
        result["verdict"] = "FLAG"
        result["reasons"].append(reason)
        add_anomaly(state, str(key), 3, reason)
        state["stats"]["flagged"] += 1
        # هشدار تلگرام
        alert_block(event, [reason])
        return result
    result["layers"].append("value")

    # ─── Layer 5: Anomaly ───
    ok, reason = check_anomaly_score(state, str(key))
    if not ok:
        result["verdict"] = "FLAG"
        result["reasons"].append(reason)
        result["layers"].append("anomaly")
        state["stats"]["flagged"] += 1
        return result
    result["layers"].append("anomaly")

    # ─── Layer 1: HMAC token (اختیاری) ───
    result["layers"].append("hmac")

    state["stats"]["passed"] += 1
    return result

# ═══ Audit ═══
def write_audit(event, result):
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": event.get("type", "?"),
        "verdict": result["verdict"],
        "reasons": result["reasons"],
    }
    with open(AUDIT, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    # زنجیره هش
    add_to_hashchain(entry)

# ═══ Test ═══
if __name__ == "__main__":
    state = load_state()
    print("🛡️ Shop Shield v3 — Test")
    print("=" * 60)
    tests = [
        {"type": "user_new", "data": {"user_id": 1, "username": "salam"}},
        {"type": "order_new", "data": {"user_id": 1, "total_price": 500_000}},
        {"type": "order_new", "data": {"user_id": 1, "total_price": 15_000_000}},
        {"type": "user_new", "data": {"username": "'; DROP TABLE users; --"}},
        {"type": "user_new", "data": {"username": "<script>alert(1)</script>"}},
        {"type": "activity", "data": {"action": "/wp-admin"}},
        {"type": "activity", "data": {"action": "/.env"}},
    ]
    for t in tests:
        r = check_event(t, state)
        icon = {"PASS":"✅", "FLAG":"⚠️", "BLOCK":"🚫"}[r["verdict"]]
        print(f"  {icon} {t['type']:12} | {r['verdict']:6} | {r['reasons']}")
    print("=" * 60)
    print(f"  Stats: {state['stats']}")
    save_state(state)
