#!/data/data/com.termux/files/usr/bin/bash
CONFIG=~/vorix-hybrid/config/vorix.config.json

echo "VORIX Connection Test"
echo "===================="

echo -n "GitHub:    "
ssh -T git@github.com 2>&1 | head -1 | grep -q "successfully" && echo "OK" || echo "FAIL"

DASH=$(python3 -c "import json; print(json.load(open('$CONFIG'))['endpoints']['dashboard'])")
echo -n "Dashboard: "
CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$DASH")
echo "$CODE"

echo -n "Sync loop: "
pgrep -f sync_loop > /dev/null && echo "running" || echo "stopped"

LAYERS=$(pgrep -f "python layer" | wc -l)
echo "Layers:    $LAYERS active"
