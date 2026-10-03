#!/usr/bin/env python3
"""VORIX — ساخت ۱۵ لایه جدید"""
import os

BASE = os.path.expanduser("~/vorix-hybrid/phone")
os.makedirs(BASE, exist_ok=True)

# ═══════════════════════════════════════════════
#  قالب مشترک همه لایه‌ها
# ═══════════════════════════════════════════════
TEMPLATE = '''#!/usr/bin/env python3
"""{title}"""
import os, sys, json, time, hashlib, subprocess, threading
from datetime import datetime

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
LOGS = os.path.join(BASE, "logs")
STATE = os.path.join(BASE, "{fname}_state.json")
TOKEN = open(os.path.join(HOME, "vorix/.tg-token")).read().strip() if os.path.exists(os.path.join(HOME, "vorix/.tg-token")) else ""
CHAT = "175160049"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = "[{ts}] {msg}"
    print(line)
    try:
        with open(os.path.join(LOGS, "{fname}.log"), "a") as f:
            f.write(line + "\\n")
    except: pass

def alert(msg):
    if not TOKEN: return
    try:
        import requests
        requests.post(
            "https://api.telegram.org/bot" + TOKEN + "/sendMessage",
            json={{"chat_id": CHAT, "text": msg, "parse_mode": "HTML"}},
            timeout=10
        )
    except: pass

def save_state(d):
    try:
        with open(STATE, "w") as f:
            json.dump(d, f, indent=2)
    except: pass

def load_state():
    try:
        with open(STATE) as f:
            return json.load(f)
    except:
        return {{}}

def pgrep(pattern):
    try:
        r = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True, timeout=2)
        return [p for p in r.stdout.strip().split("\\n") if p]
    except:
        return []

{body}

def main():
    if len(sys.argv) < 2:
        print("Usage: {fname}.py {{watch|status|test}}")
        return
    cmd = sys.argv[1]
    if cmd == "watch": watch()
    elif cmd == "status": status()
    elif cmd == "test": test()

if __name__ == "__main__":
    main()
'''

layers = {}

# ═══════════════════════════════════════════════
# ۱. L-Heartbeat — نبض سیستم
# ═══════════════════════════════════════════════
layers["layer_heartbeat"] = {
  "title": "L-Heartbeat — نبض سیستم",
  "fname": "layer_heartbeat",
  "body": '''
LAYERS = [
    "layer01_selfdefense","layer02_threat_intel","layer03_behavioral",
    "layer04_auto_block","layer05_data_quarantine","layer06_geoip_block",
    "layer08_network_monitor","layer09_rate_limiter","layer10_red_alert",
    "layer17_watchdog","layer19_password_leak","layer21_ml_anomaly",
    "layer25_ssl_monitor","layer29_30_identity","layer_fim","layer_rootkit",
    "layer_multichannel","layer_livefeed","vorix_bot","sync_loop",
]

def check_all():
    alive = []
    dead = []
    for l in LAYERS:
        if pgrep(l): alive.append(l)
        else: dead.append(l)
    return alive, dead

def watch():
    log("💓 Heartbeat started")
    while True:
        try:
            alive, dead = check_all()
            s = load_state()
            s["ts"] = datetime.now().isoformat()
            s["alive"] = len(alive)
            s["dead"] = len(dead)
            s["dead_list"] = dead
            save_state(s)
            
            if len(dead) >= 5:
                alert("💓 Heartbeat: " + str(len(dead)) + " layers dead!\\n" + "\\n".join(dead[:5]))
                log("⚠ " + str(len(dead)) + " dead layers")
            elif len(dead) > 0:
                log("😐 " + str(len(dead)) + " dead: " + ", ".join(dead[:3]))
            else:
                log("💚 all " + str(len(alive)) + " alive")
        except Exception as e:
            log("ERR: " + str(e))
        time.sleep(20)

def status():
    alive, dead = check_all()
    print("Alive: " + str(len(alive)))
    print("Dead:  " + str(len(dead)))
    if dead: print("Dead list: " + ", ".join(dead))

def test():
    alive, dead = check_all()
    print("OK - " + str(len(alive)) + " alive, " + str(len(dead)) + " dead")
'''
}

# ═══════════════════════════════════════════════
# ۲. L-Guard — محافظ درخواست
# ═══════════════════════════════════════════════
layers["layer_guard"] = {
  "title": "L-Guard — محافظ درخواست",
  "fname": "layer_guard",
  "body": '''
QUEUE = os.path.join(BASE, "guard_queue.jsonl")
SECRET = os.path.join(BASE, ".guard_secret")

def get_secret():
    if not os.path.exists(SECRET):
        with open(SECRET, "w") as f:
            f.write(hashlib.sha256(str(time.time()).encode()).hexdigest())
    return open(SECRET).read().strip()

def sign(cmd):
    s = get_secret()
    return hashlib.sha256((cmd + s).encode()).hexdigest()[:16]

def verify(cmd, sig):
    return sign(cmd) == sig

def watch():
    log("🛡️ Guard started")
    secret = get_secret()
    log("Secret: " + secret[:8] + "...")
    last_pos = 0
    while True:
        try:
            if not os.path.exists(QUEUE):
                time.sleep(2); continue
            size = os.path.getsize(QUEUE)
            if size < last_pos: last_pos = 0
            if size == last_pos:
                time.sleep(2); continue
            with open(QUEUE) as f:
                f.seek(last_pos)
                for line in f.readlines():
                    try:
                        item = json.loads(line)
                        cmd = item.get("cmd","")
                        sig = item.get("sig","")
                        if verify(cmd, sig):
                            log("✅ valid: " + cmd[:30])
                        else:
                            log("❌ INVALID signature: " + cmd[:30])
                            alert("🛡️ Guard: invalid signature\\n<code>" + cmd[:100] + "</code>")
                    except: pass
                last_pos = f.tell()
        except: pass
        time.sleep(3)

def status():
    print("Queue: " + QUEUE)
    print("Secret set: " + str(os.path.exists(SECRET)))

def test():
    s = get_secret()
    cmd = "test_command"
    sig = sign(cmd)
    print("Sign: " + sig)
    print("Verify valid: " + str(verify(cmd, sig)))
    print("Verify bad:   " + str(verify(cmd, "bad")))
'''
}

# ═══════════════════════════════════════════════
# ۳. L-Canary — طعمه هکر
# ═══════════════════════════════════════════════
layers["layer_canary"] = {
  "title": "L-Canary — طعمه هکر",
  "fname": "layer_canary",
  "body": '''
TRAP_DIR = os.path.join(BASE, "trap")
TRAPS = ["passwords.txt", "api_keys.json", "backup_codes.txt", "config_secret.env"]

def init_traps():
    os.makedirs(TRAP_DIR, exist_ok=True)
    for t in TRAPS:
        p = os.path.join(TRAP_DIR, t)
        if not os.path.exists(p):
            with open(p, "w") as f:
                f.write("# TRAP — DO NOT OPEN\\n")
                f.write("honeypot_token=" + hashlib.sha256(t.encode()).hexdigest()[:32] + "\\n")

def get_mtimes():
    m = {}
    for t in TRAPS:
        p = os.path.join(TRAP_DIR, t)
        if os.path.exists(p):
            m[t] = os.path.getmtime(p)
    return m

def watch():
    log("🪤 Canary started")
    init_traps()
    base = get_mtimes()
    while True:
        try:
            cur = get_mtimes()
            for t, m in cur.items():
                if t in base and m != base[t]:
                    log("🚨 TRAP TRIGGERED: " + t)
                    alert("🪤 <b>Canary triggered!</b>\\nFile: <code>" + t + "</code>\\nSomebody opened the trap!")
            base = cur
        except Exception as e:
            log("ERR: " + str(e))
        time.sleep(5)

def status():
    print("Traps: " + str(len(TRAPS)))
    for t in TRAPS:
        p = os.path.join(TRAP_DIR, t)
        print("  " + ("✅" if os.path.exists(p) else "❌") + " " + t)

def test():
    init_traps()
    print("Traps initialized:")
    for t in TRAPS:
        print("  " + t)
'''
}

# ═══════════════════════════════════════════════
# ۴. L-Seal — مهر اصالت
# ═══════════════════════════════════════════════
layers["layer_seal"] = {
  "title": "L-Seal — مهر اصالت فایل‌ها",
  "fname": "layer_seal",
  "body": '''
SEAL_FILE = os.path.join(BASE, "seal_hashes.json")

def hash_file(p):
    try:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except: return None

def collect():
    result = {}
    for f in os.listdir(BASE):
        if f.endswith(".py"):
            p = os.path.join(BASE, f)
            h = hash_file(p)
            if h: result[f] = h
    return result

def seal():
    result = collect()
    with open(SEAL_FILE, "w") as f:
        json.dump({"ts": datetime.now().isoformat(), "files": result}, f, indent=2)
    log("🔒 Sealed " + str(len(result)) + " files")
    return result

def watch():
    log("🔒 Seal started")
    if not os.path.exists(SEAL_FILE):
        base = seal()
    else:
        base = json.load(open(SEAL_FILE)).get("files", {})
    
    while True:
        try:
            cur = collect()
            for f, h in cur.items():
                if f in base and base[f] != h:
                    log("⚠ SEAL BROKEN: " + f)
                    alert("🔒 <b>Seal broken!</b>\\nFile: <code>" + f + "</code>")
                elif f not in base:
                    log("➕ new file: " + f)
            for f in base:
                if f not in cur:
                    log("➖ missing: " + f)
            base = cur
        except Exception as e:
            log("ERR: " + str(e))
        time.sleep(30)

def status():
    if os.path.exists(SEAL_FILE):
        d = json.load(open(SEAL_FILE))
        print("Sealed: " + d.get("ts","?"))
        print("Files:  " + str(len(d.get("files", {}))))
    else:
        print("Not sealed yet")

def test():
    r = seal()
    print("Sealed " + str(len(r)) + " files")
'''
}

# ═══════════════════════════════════════════════
# ۵. L-Quarantine — قرنطینه
# ═══════════════════════════════════════════════
layers["layer_quarantine"] = {
  "title": "L-Quarantine — قرنطینه فایل‌های مشکوک",
  "fname": "layer_quarantine",
  "body": '''
QUAR = os.path.join(BASE, "quarantine_locked")
TRIGGER = os.path.join(BASE, "quarantine_trigger.jsonl")

def init():
    os.makedirs(QUAR, exist_ok=True)

def quarantine(fpath, reason):
    init()
    if not os.path.exists(fpath):
        log("❌ file not exists: " + fpath)
        return False
    try:
        name = os.path.basename(fpath)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        dest = os.path.join(QUAR, ts + "_" + name)
        h = hash_file(fpath)
        subprocess.run(["mv", fpath, dest], timeout=5)
        with open(os.path.join(QUAR, "index.jsonl"), "a") as f:
            f.write(json.dumps({
                "ts": ts, "from": fpath, "to": dest,
                "hash": h, "reason": reason
            }) + "\\n")
        log("🔒 Quarantined: " + name)
        alert("🔒 <b>Quarantined</b>\\nFile: <code>" + name + "</code>\\nReason: " + reason)
        return True
    except Exception as e:
        log("ERR: " + str(e))
        return False

def hash_file(p):
    try:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for c in iter(lambda: f.read(8192), b""): h.update(c)
        return h.hexdigest()
    except: return None

def watch():
    log("🔒 Quarantine started")
    init()
    last = 0
    while True:
        try:
            if os.path.exists(TRIGGER):
                size = os.path.getsize(TRIGGER)
                if size > last:
                    with open(TRIGGER) as f:
                        f.seek(last)
                        for line in f.readlines():
                            try:
                                item = json.loads(line)
                                quarantine(item["path"], item.get("reason","?"))
                            except: pass
                        last = f.tell()
        except: pass
        time.sleep(5)

def status():
    init()
    files = [f for f in os.listdir(QUAR) if not f.endswith(".jsonl")]
    print("Quarantined: " + str(len(files)))
    for f in files[:10]: print("  " + f)

def test():
    init()
    print("Quarantine dir: " + QUAR)
'''
}

# ═══════════════════════════════════════════════
# ۶. L-Aegis — سپر کل
# ═══════════════════════════════════════════════
layers["layer_aegis"] = {
  "title": "L-Aegis — سپر کل سیستم",
  "fname": "layer_aegis",
  "body": '''
from collections import deque

HISTORY = deque(maxlen=20)
THRESHOLD = 5  # اگه ۵+ لایه مشکل داشتن → اضطراری

LAYERS = [
    "layer01_selfdefense","layer03_behavioral","layer04_auto_block",
    "layer06_geoip_block","layer08_network_monitor","layer09_rate_limiter",
    "layer10_red_alert","layer17_watchdog","layer19_password_leak",
    "layer21_ml_anomaly","layer25_ssl_monitor","layer29_30_identity",
    "layer_fim","layer_rootkit","layer_multichannel","layer_livefeed",
]

def count_dead():
    dead = 0
    for l in LAYERS:
        if not pgrep(l): dead += 1
    return dead

def trigger_emergency(dead_count):
    log("🚨 AEGIS EMERGENCY: " + str(dead_count) + " layers dead!")
    alert(
        "🚨 <b>AEGIS EMERGENCY</b>\\n\\n"
        + str(dead_count) + " لایه قطع شده‌اند!\\n"
        "سیستم در وضعیت بحرانی"
    )
    # Snapshot
    try:
        snapshot_dir = os.path.join(BASE, "aegis_snapshot")
        os.makedirs(snapshot_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        for f in ["hash_chain.jsonl", "blocklist.json"]:
            p = os.path.join(BASE, f)
            if os.path.exists(p):
                subprocess.run(["cp", p, os.path.join(snapshot_dir, ts + "_" + f)], timeout=5)
        log("📦 Snapshot saved: " + ts)
    except Exception as e:
        log("Snapshot err: " + str(e))

def watch():
    log("🛡️ Aegis started")
    emergency_active = False
    while True:
        try:
            dead = count_dead()
            HISTORY.append(dead)
            log("🛡️ Aegis: " + str(dead) + " dead, history avg: " + str(sum(HISTORY)/len(HISTORY)))
            
            # اگه ۳ بار پشت سر هم >= threshold
            if len(HISTORY) >= 3 and all(h >= THRESHOLD for h in list(HISTORY)[-3:]):
                if not emergency_active:
                    trigger_emergency(dead)
                    emergency_active = True
            elif dead < 2:
                emergency_active = False
        except Exception as e:
            log("ERR: " + str(e))
        time.sleep(15)

def status():
    dead = count_dead()
    print("Dead: " + str(dead) + "/" + str(len(LAYERS)))
    print("Threshold: " + str(THRESHOLD))
    print("History: " + str(list(HISTORY)))

def test():
    dead = count_dead()
    print("Test OK - " + str(dead) + " dead right now")
'''
}

# ═══════════════════════════════════════════════
# ۷. L-Beacon — شکار C2
# ═══════════════════════════════════════════════
layers["layer_beacon"] = {
  "title": "L-Beacon — شکار سیگنال خروجی (C2)",
  "fname": "layer_beacon",
  "body": '''
WHITELIST = ["telegram.org", "api.telegram.org", "github.com",
             "api.github.com", "raw.githubusercontent.com",
             "google.com", "cloudflare.com"]

def get_connections():
    try:
        r = subprocess.run(["ss", "-tunap"], capture_output=True, text=True, timeout=5)
        lines = r.stdout.split("\\n")
        conns = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 5 and parts[0] in ("tcp","udp"):
                peer = parts[4]
                proc = parts[-1] if len(parts) > 5 else "?"
                conns.append({"peer": peer, "proc": proc})
        return conns
    except: return []

def is_whitelisted(peer):
    for w in WHITELIST:
        if w in peer:
            return True
    return False

def watch():
    log("📡 Beacon started")
    seen = set()
    while True:
        try:
            conns = get_connections()
            for c in conns:
                key = c["peer"] + "|" + c["proc"]
                if key in seen: continue
                seen.add(key)
                if not is_whitelisted(c["peer"]):
                    log("📡 new outbound: " + c["peer"] + " (" + c["proc"] + ")")
                    # فقط اگه پروتکل عجیب بود
                    port = 0
                    try: port = int(c["peer"].split(":")[-1])
                    except: pass
                    if port and port not in (80, 443, 53, 22):
                        alert("📡 <b>Suspicious outbound</b>\\nPeer: <code>" + c["peer"] + "</code>\\nProc: " + c["proc"] + "\\nPort: " + str(port))
            if len(seen) > 1000: seen.clear()
        except Exception as e:
            log("ERR: " + str(e))
        time.sleep(20)

def status():
    conns = get_connections()
    print("Active: " + str(len(conns)))

def test():
    conns = get_connections()
    print("Test OK - " + str(len(conns)) + " connections")
'''
}

# ═══════════════════════════════════════════════
# ۸. L-Whitelist — لیست سفید
# ═══════════════════════════════════════════════
layers["layer_whitelist"] = {
  "title": "L-Whitelist — لیست سفید IP",
  "fname": "layer_whitelist",
  "body": '''
WL_FILE = os.path.join(BASE, "whitelist.json")

DEFAULT = {
    "ips": ["127.0.0.1", "::1"],
    "cidrs": ["192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12"],
    "updated": datetime.now().isoformat()
}

def ensure():
    if not os.path.exists(WL_FILE):
        with open(WL_FILE, "w") as f:
            json.dump(DEFAULT, f, indent=2)

def is_safe(ip):
    ensure()
    try:
        wl = json.load(open(WL_FILE))
        if ip in wl.get("ips", []): return True
        # چک /8 /16 ساده
        for cidr in wl.get("cidrs", []):
            net = cidr.split("/")[0]
            if ip.startswith(net.rsplit(".", 1)[0] + "."):
                return True
    except: pass
    return False

def watch():
    log("✅ Whitelist started")
    ensure()
    log("Loaded " + str(len(json.load(open(WL_FILE)).get("ips", []))) + " IPs")
    while True:
        time.sleep(60)

def status():
    ensure()
    wl = json.load(open(WL_FILE))
    print("IPs:   " + str(len(wl.get("ips", []))))
    print("CIDRs: " + str(len(wl.get("cidrs", []))))

def test():
    print("127.0.0.1: " + str(is_safe("127.0.0.1")))
    print("8.8.8.8:   " + str(is_safe("8.8.8.8")))
    print("192.168.1.5: " + str(is_safe("192.168.1.5")))
'''
}

# ═══════════════════════════════════════════════
# ۹. L-Resurrect — خودترمیمی
# ═══════════════════════════════════════════════
layers["layer_resurrect"] = {
  "title": "L-Resurrect — خودترمیمی",
  "fname": "layer_resurrect",
  "body": '''
WATCH = {
    "layer01_selfdefense.py": "watch",
    "layer03_behavioral.py": "watch",
    "layer04_auto_block.py": "watch",
    "layer06_geoip_block.py": "watch",
    "layer08_network_monitor.py": "watch",
    "layer09_rate_limiter.py": "watch",
    "layer10_red_alert.py": "watch",
    "layer17_watchdog.py": "watch",
    "layer19_password_leak.py": "watch",
    "layer21_ml_anomaly.py": "watch",
    "layer25_ssl_monitor.py": "watch",
    "layer29_30_identity.py": "watch",
    "layer_fim.py": "watch",
    "layer_rootkit.py": "watch",
    "layer_multichannel.py": "watch",
}

def restart(fname, sub):
    base = fname.replace(".py", "")
    try:
        subprocess.Popen(["python", fname, sub], cwd=BASE,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log("♻️ Restarted: " + fname)
        return True
    except Exception as e:
        log("ERR: " + str(e))
        return False

def watch():
    log("♻️ Resurrect started")
    attempts = {}
    while True:
        try:
            for fname, sub in WATCH.items():
                base = fname.replace(".py", "")
                if not pgrep(base):
                    n = attempts.get(fname, 0)
                    if n < 10:
                        restart(fname, sub)
                        attempts[fname] = n + 1
                    else:
                        log("❌ Gave up on " + fname)
                else:
                    attempts[fname] = 0
        except Exception as e:
            log("ERR: " + str(e))
        time.sleep(30)

def status():
    for f in WATCH:
        base = f.replace(".py", "")
        print(("✅" if pgrep(base) else "❌") + " " + f)

def test():
    print("Watching " + str(len(WATCH)) + " layers")
'''
}

# ═══════════════════════════════════════════════
# ۱۰. L-Feed — تغذیه تهدید
# ═══════════════════════════════════════════════
layers["layer_feed"] = {
  "title": "L-Feed — تغذیه تهدید (Threat Intel)",
  "fname": "layer_feed",
  "body": '''
FEED_FILE = os.path.join(BASE, "threat_feed.json")
BL_FILE = os.path.join(BASE, "blocklist.json")
FEEDS = [
    "https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt",
]

def download(url):
    try:
        import requests
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            return r.text
    except: pass
    return None

def parse(text):
    ips = []
    if not text: return ips
    for line in text.split("\\n"):
        line = line.strip()
        if not line or line.startswith("#"): continue
        parts = line.split("\\t")
        if parts and parts[0].count(".") == 3:
            ips.append(parts[0])
    return ips[:5000]

def update():
    log("🌐 Feed: downloading...")
    all_ips = []
    for url in FEEDS:
        text = download(url)
        ips = parse(text)
        all_ips.extend(ips)
        log("  " + str(len(ips)) + " from " + url.split("/")[-1])
    
    with open(FEED_FILE, "w") as f:
        json.dump({"ts": datetime.now().isoformat(), "count": len(all_ips), "ips": all_ips}, f)
    log("🌐 Feed updated: " + str(len(all_ips)) + " IPs")

def watch():
    log("🌐 Feed started")
    update()
    while True:
        try:
            time.sleep(6 * 3600)
            update()
        except: time.sleep(600)

def status():
    if os.path.exists(FEED_FILE):
        d = json.load(open(FEED_FILE))
        print("IPs: " + str(d.get("count", 0)))
        print("Ts:  " + d.get("ts", "?"))
    else:
        print("Not downloaded")

def test():
    text = "1.2.3.4\\t1\\n5.6.7.8\\t2"
    ips = parse(text)
    print("Parse test: " + str(ips))
'''
}

# ═══════════════════════════════════════════════
# ۱۱. L-Honeytoken — رمز طعمه
# ═══════════════════════════════════════════════
layers["layer_honeytoken"] = {
  "title": "L-Honeytoken — رمزهای طعمه",
  "fname": "layer_honeytoken",
  "body": '''
TOKENS = os.path.join(BASE, "honey_tokens")
TRAPS = {
    "credentials.txt": """# PRODUCTION CREDENTIALS
DB_PASSWORD=Admin@Prod2026!
API_KEY=sk_live_honeypot_trap_xxxxx
AWS_ACCESS=AKIAHONEYTRAP
""",
    "ssh_keys/id_rsa": "# SSH Private Key (honeypot)\\n",
    "wallet.txt": "BTC: bc1qHoneypotAddressxxxxx\\nETH: 0xHoneypotAddressxxxxx\\n",
}

def init():
    os.makedirs(TOKENS, exist_ok=True)
    for name, content in TRAPS.items():
        p = os.path.join(TOKENS, name)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if not os.path.exists(p):
            with open(p, "w") as f:
                f.write(content)

def get_mtimes():
    m = {}
    for name in TRAPS:
        p = os.path.join(TOKENS, name)
        if os.path.exists(p):
            m[name] = os.path.getmtime(p)
    return m

def watch():
    log("🍯 Honeytokens started")
    init()
    base = get_mtimes()
    while True:
        try:
            cur = get_mtimes()
            for k in cur:
                if k in base and cur[k] != base[k]:
                    log("🍯 HONEYTOKEN TRIGGERED: " + k)
                    alert("🍯 <b>Honeytoken triggered!</b>\\nFile: <code>" + k + "</code>")
            base = cur
        except: pass
        time.sleep(5)

def status():
    init()
    print("Tokens: " + str(len(TRAPS)))

def test():
    init()
    for n in TRAPS:
        p = os.path.join(TOKENS, n)
        print("  " + ("✅" if os.path.exists(p) else "❌") + " " + n)
'''
}

# ═══════════════════════════════════════════════
# ۱۲. L-Tarpit — چاله قطران
# ═══════════════════════════════════════════════
layers["layer_tarpit"] = {
  "title": "L-Tarpit — کند کردن هکر",
  "fname": "layer_tarpit",
  "body": '''
import socket, threading

PORT = 9999
SLOW = 30  # ثانیه

def handle(conn, addr):
    log("🕸️ Tarpit: connection from " + addr[0])
    try:
        conn.settimeout(2)
        try: conn.recv(1024)
        except: pass
        # فقط نگه‌دار
        time.sleep(SLOW)
        conn.close()
    except: pass
    log("🕸️ Tarpit: released " + addr[0])

def server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("0.0.0.0", PORT))
        s.listen(50)
        log("🕸️ Tarpit listening on " + str(PORT))
        while True:
            try:
                conn, addr = s.accept()
                threading.Thread(target=handle, args=(conn, addr), daemon=True).start()
            except: pass
    except Exception as e:
        log("ERR: " + str(e))

def watch():
    server()

def status():
    print("Port: " + str(PORT))
    print("Delay: " + str(SLOW) + "s")

def test():
    print("Tarpit would listen on port " + str(PORT))
'''
}

# ═══════════════════════════════════════════════
# ۱۳. L-Mirror — آینه زنده
# ═══════════════════════════════════════════════
layers["layer_mirror"] = {
  "title": "L-Mirror — آینه زنده State",
  "fname": "layer_mirror",
  "body": '''
MIRROR = os.path.join(BASE, "mirror")
FILES = ["hash_chain.jsonl", "blocklist.json", "playbooks.jsonl",
         "layer10_events.jsonl", "fim_baseline.json"]

def init():
    os.makedirs(MIRROR, exist_ok=True)

def sync():
    init()
    for f in FILES:
        src = os.path.join(BASE, f)
        if os.path.exists(src):
            dst = os.path.join(MIRROR, f)
            try:
                subprocess.run(["cp", src, dst], timeout=5)
            except: pass
    # بک‌آپ تاریخ‌دار
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    try:
        arc = os.path.join(MIRROR, "snap_" + ts + ".tar.gz")
        subprocess.run(["tar","czf",arc,"-C",BASE] + FILES,
                     timeout=15, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log("📦 Mirror snapshot: " + os.path.basename(arc))
    except: pass

def watch():
    log("🪞 Mirror started")
    while True:
        try:
            sync()
        except Exception as e:
            log("ERR: " + str(e))
        time.sleep(300)  # هر ۵ دقیقه

def status():
    init()
    snaps = [f for f in os.listdir(MIRROR) if f.startswith("snap_")]
    print("Mirror: " + MIRROR)
    print("Snapshots: " + str(len(snaps)))

def test():
    sync()
    print("Synced " + str(len(FILES)) + " files")
'''
}

# ═══════════════════════════════════════════════
# ۱۴. L-Watchtower — برج دیده‌بانی
# ═══════════════════════════════════════════════
layers["layer_watchtower"] = {
  "title": "L-Watchtower — برج دیده‌بانی",
  "fname": "layer_watchtower",
  "body": '''
WT_LOG = os.path.join(BASE, "watchtower.jsonl")
SOURCES = ["hash_chain.jsonl", "playbooks.jsonl", "layer10_events.jsonl"]

def ingest():
    last = load_state().get("offsets", {})
    count = 0
    for src in SOURCES:
        p = os.path.join(BASE, src)
        if not os.path.exists(p): continue
        size = os.path.getsize(p)
        pos = last.get(src, 0)
        if size < pos: pos = 0
        if size == pos: continue
        try:
            with open(p) as f:
                f.seek(pos)
                for line in f.readlines():
                    try:
                        ev = json.loads(line)
                        ev["_src"] = src
                        ev["_ts"] = datetime.now().isoformat()
                        with open(WT_LOG, "a") as out:
                            out.write(json.dumps(ev) + "\\n")
                        count += 1
                    except: pass
                last[src] = f.tell()
        except: pass
    save_state({"offsets": last})
    return count

def watch():
    log("🗼 Watchtower started")
    while True:
        try:
            n = ingest()
            if n: log("🗼 Ingested " + str(n))
        except Exception as e:
            log("ERR: " + str(e))
        time.sleep(10)

def status():
    if os.path.exists(WT_LOG):
        size = os.path.getsize(WT_LOG)
        print("Watchtower log: " + str(size) + " bytes")

def test():
    n = ingest()
    print("Test: ingested " + str(n))
'''
}

# ═══════════════════════════════════════════════
# ۱۵. L-Chaos — تست خودکار
# ═══════════════════════════════════════════════
layers["layer_chaos"] = {
  "title": "L-Chaos — تست خودکار حمله",
  "fname": "layer_chaos",
  "body": '''
TESTS = [
    {"name": "sql_injection", "event": {"severity":"CRITICAL","event_type":"SQL_INJECTION","src_ip":"127.0.0.1","message":"chaos test"}},
    {"name": "brute_force",   "event": {"severity":"CRITICAL","event_type":"BRUTE_FORCE","src_ip":"127.0.0.1","message":"50 attempts"}},
    {"name": "port_scan",     "event": {"severity":"WARN","event_type":"PORT_SCAN","src_ip":"127.0.0.1","message":"nmap"}},
]

def fire(ev):
    q = os.path.join(BASE, "queue.jsonl")
    with open(q, "a") as f:
        f.write(json.dumps(ev) + "\\n")

def watch():
    log("🎲 Chaos started")
    while True:
        try:
            # هر ۱ ساعت
            time.sleep(3600)
            for t in TESTS:
                log("🎲 Firing: " + t["name"])
                fire(t["event"])
                time.sleep(2)
        except: time.sleep(600)

def status():
    print("Tests: " + str(len(TESTS)))
    for t in TESTS: print("  " + t["name"])

def test():
    for t in TESTS:
        fire(t["event"])
        log("🎲 fired: " + t["name"])
    print("Fired " + str(len(TESTS)) + " test events")
'''
}

# ═══════════════════════════════════════════════
#  ساخت همه فایل‌ها
# ═══════════════════════════════════════════════
created = 0
for fname, data in layers.items():
    path = os.path.join(BASE, fname + ".py")
    content = TEMPLATE.replace("{title}", data["title"])
    content = content.replace("{fname}", data["fname"])
    content = content.replace("{body}", data["body"])
    with open(path, "w") as f:
        f.write(content)
    os.chmod(path, 0o755)
    created += 1
    print("✅ " + fname + ".py")

print("")
print("🎉 " + str(created) + " layers created in " + BASE)
