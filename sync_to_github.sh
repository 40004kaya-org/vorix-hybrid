#!/data/data/com.termux/files/usr/bin/bash
# VORIX Sync v4 — همه داده‌ها

cd ~/vorix-hybrid/phone

# ۱. وضعیت لایه‌ها
python3 ~/vorix-hybrid/scripts/gen-live-status.py 2>&1 | grep -E "✅|❌" | head -1

# ۲. حملات
python3 ~/vorix-hybrid/scripts/gen-attacks.py 2>&1 | grep "✅" | head -1

# ۳. لاگ‌ها
python3 ~/vorix-hybrid/scripts/gen-logs.py 2>&1 | grep "✅" | head -1
python3 ~/vorix-hybrid/scripts/gen-live-global.py 2>&1 | grep "✅" | head -1
python3 ~/vorix-hybrid/scripts/gen-country-matrix.py 2>&1 | grep "✅" | head -1

# ۴. push
cd ~/vorix-hybrid
git add -f docs/data/live.json docs/data/attacks.json docs/data/logs.json docs/data/live_global.json docs/data/country_matrix.json 2>/dev/null
git commit -m "sync: $(date +%H:%M)" 2>/dev/null
git push 2>&1 | grep -E "main|rejected" | tail -1
