#!/usr/bin/env python3
"""VORIX — ساخت attacks.json از رخدادهای لایه‌ها"""
import json, os, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

PHONE = Path.home() / "vorix-hybrid/phone"
OUT = Path.home() / "vorix-hybrid/docs/data/attacks.json"

def read_jsonl(path, limit=200):
    events = []
    if not os.path.exists(path):
        return events
    with open(path) as f:
        for line in f.readlines()[-limit:]:
            try:
                events.append(json.loads(line))
            except: pass
    return events

# خواندن همه منابع
events = []
for f in ["hash_chain.jsonl", "playbooks.jsonl", "layer10_events.jsonl", "killswitch_events.jsonl"]:
    events.extend(read_jsonl(PHONE / f))

# آخرین ۵۰ رویداد
recent = sorted(events, key=lambda e: e.get("ts", ""), reverse=True)[:50]

# استخراج IPها
attacks = []
for e in recent:
    ip = e.get("ip") or e.get("src_ip") or e.get("source") or "unknown"
    attacks.append({
        "ts": e.get("ts", ""),
        "ip": ip,
        "attack_type": e.get("type") or e.get("attack") or e.get("event") or "unknown",
        "severity": e.get("severity", "low"),
        "layer": e.get("layer", "unknown"),
        "country": e.get("country", "??"),
        "mitre": e.get("mitre", ""),
        "action": e.get("action", "detected"),
    })

# آمار
stats = {
    "total": len(attacks),
    "blocked": sum(1 for a in attacks if "block" in str(a.get("action","")).lower()),
    "critical": sum(1 for a in attacks if str(a.get("severity","")).lower() == "critical"),
    "high": sum(1 for a in attacks if str(a.get("severity","")).lower() == "high"),
    "top_countries": {},
    "top_types": {},
}

for a in attacks:
    c = a.get("country", "??")
    stats["top_countries"][c] = stats["top_countries"].get(c, 0) + 1
    t = a.get("attack_type", "unknown")
    stats["top_types"][t] = stats["top_types"].get(t, 0) + 1

# مرتب‌سازی
stats["top_countries"] = dict(sorted(stats["top_countries"].items(), key=lambda x: -x[1])[:5])
stats["top_types"] = dict(sorted(stats["top_types"].items(), key=lambda x: -x[1])[:5])

# MITRE mapping
mitre_counts = {}
for a in attacks:
    m = a.get("mitre", "")
    if m: mitre_counts[m] = mitre_counts.get(m, 0) + 1

# خروجی نهایی
output = {
    "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "attacks": attacks,
    "stats": stats,
    "mitre": mitre_counts,
}

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"✅ attacks.json: {len(attacks)} attacks, {stats['blocked']} blocked")
