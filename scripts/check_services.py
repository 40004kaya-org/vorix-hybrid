#!/usr/bin/env python3
"""چک سلامت سرویس‌ها — با ps aux"""
import subprocess, json, urllib.request
from pathlib import Path
from datetime import datetime, timezone

OUT = Path.home() / "vorix-hybrid/docs/data/services_status.json"

def is_running(pattern):
    """چک با ps aux (کار می‌کنه تو Termux)"""
    try:
        r = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=5)
        for line in r.stdout.splitlines():
            if pattern in line and 'grep' not in line:
                return True
        return False
    except:
        return False

def check_api():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8090/health", timeout=3) as r:
            d = json.loads(r.read())
            return d.get("ok", False)
    except: return False

def check_vault():
    return Path.home().joinpath("vorix-vault").exists()

def check_shield():
        return (Path.home() / "vorix-hybrid/shop-data/shield_state.json").exists() or \
           (Path.home() / "vorix-hybrid/phone/shop_shield_state.json").exists()

services = {
    "CORE":   {"running": is_running("mine.py"),         "label": "ربات فروشگاه"},
    "BRIDGE": {"running": is_running("shop-bridge-v2"),  "label": "جمع‌آورنده"},
    "API":    {"running": check_api(),                    "label": "API :8090"},
    "SHIELD": {"running": check_shield(),                 "label": "۱۰ لایه"},
    "VAULT":  {"running": check_vault(),                  "label": "بک‌آپ"},
    "BOT":    {"running": is_running("vorix_bot_v2"),    "label": "ربات VORIX"},
    "SYNC":   {"running": is_running("sync_loop"),        "label": "Sync"},
    "ORCH":   {"running": is_running("vorix-single"),     "label": "لایه‌ها"},
    "WATCH":  {"running": is_running("vorix-watchdog"),   "label": "نگهبان"},
}

alive = sum(1 for s in services.values() if s["running"])
total = len(services)

out = {
    "ts": datetime.now(timezone.utc).isoformat(),
    "services": services,
    "stats": {"alive": alive, "total": total, "health": round(alive/total*100)},
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
print(f"✅ {alive}/{total} سرویس فعال ({round(alive/total*100)}%)")
for name, s in services.items():
    icon = "🟢" if s["running"] else "🔴"
    print(f"  {icon} {name}: {s['label']}")
