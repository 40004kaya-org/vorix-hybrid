#!/usr/bin/env python3
"""VORIX — گرفتن آخرین لاگ‌های همه لایه‌ها"""
import json, os
from pathlib import Path
from datetime import datetime, timezone

PHONE = Path.home() / "vorix-hybrid/phone"
LOGS_DIR = PHONE / "logs"
OUT = Path.home() / "vorix-hybrid/docs/data/logs.json"

def tail(path, n=20):
    """آخرین n خط"""
    if not path.exists():
        return []
    try:
        with open(path, "r", errors="ignore") as f:
            lines = f.readlines()
        return [l.rstrip() for l in lines[-n:] if l.strip()]
    except:
        return []

entries = []
now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

# هر فایل .log رو بخون
if LOGS_DIR.exists():
    for f in sorted(LOGS_DIR.glob("*.log")):
        name = f.stem.replace(".py", "")
        for line in tail(f, 15):
            # تلاش برای پارس timestamp
            ts = ""
            sev = "info"
            msg = line
            # الگوی [HH:MM:SS] یا 2026-...
            if line.startswith("["):
                end = line.find("]")
                if end > 0 and end < 20:
                    ts = line[1:end]
                    msg = line[end+1:].strip()
            # تشخیص severity
            low = line.lower()
            if any(k in low for k in ["error", "critical", "fail", "dead"]):
                sev = "error"
            elif any(k in low for k in ["warn", "alert"]):
                sev = "warn"
            elif any(k in low for k in ["ok", "success", "clean", "started"]):
                sev = "ok"
            entries.append({
                "src": name,
                "ts": ts,
                "sev": sev,
                "msg": msg[:200]
            })

# آخرین 100 تا
entries = entries[-100:]

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w") as f:
    json.dump({
        "ts": now,
        "total": len(entries),
        "entries": entries,
    }, f, indent=1, ensure_ascii=False)

print(f"✅ logs.json: {len(entries)} entries")
