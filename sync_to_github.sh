#!/data/data/com.termux/files/usr/bin/bash

cd ~/vorix-hybrid/phone

# ساخت stats.json
python - << 'PYEOF'
import json, os
from datetime import datetime

events = []
for f in ["hash_chain.jsonl", "playbooks.jsonl", "layer10_events.jsonl"]:
    if os.path.exists(f):
        with open(f) as fh:
            for line in fh.readlines()[-100:]:
                try: events.append(json.loads(line))
                except: pass

stats = {
    "total": len(events),
    "critical": sum(1 for e in events if str(e.get("severity","")).upper() in ("CRITICAL","ERROR")),
    "blocked": len(json.load(open("blocklist.json"))) if os.path.exists("blocklist.json") else 0,
    "last_update": datetime.utcnow().isoformat() + "Z",
}

os.makedirs("../docs", exist_ok=True)
with open("../docs/stats.json", "w") as f:
    json.dump(stats, f, indent=2, ensure_ascii=False)

with open("../docs/events.json", "w") as f:
    json.dump(events[-50:], f, indent=2, ensure_ascii=False)

print(f"✓ {len(events)} events, {stats['critical']} critical")
PYEOF

# push به GitHub
cd ~/vorix-hybrid
git add docs/stats.json docs/events.json
git commit -m "sync: $(date +%H:%M)" 2>/dev/null
git push 2>&1 | tail -2
