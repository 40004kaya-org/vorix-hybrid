#!/data/data/com.termux/files/usr/bin/bash

LOCKFILE=/data/data/com.termux/files/home/vorix-hybrid/phone/keepalive.lock

if [ -f "$LOCKFILE" ]; then
    OLDPID=$(cat "$LOCKFILE")
    if kill -0 "$OLDPID" 2>/dev/null; then
        exit 0
    fi
fi

echo $$ > "$LOCKFILE"
trap "rm -f $LOCKFILE" EXIT

cd /data/data/com.termux/files/home/vorix-hybrid/phone
LOGS="$PWD/logs"
mkdir -p "$LOGS"

SERVICES=(
    "vorix_bot.py"
    "layer_livefeed.py"
)

LAYERS=(
    "layer01_selfdefense.py|watch"
    "layer03_behavioral.py|watch"
    "layer04_auto_block.py|watch"
    "layer06_geoip_block.py|watch"
    "layer08_network_monitor.py|watch"
    "layer09_rate_limiter.py|watch"
    "layer10_red_alert.py|watch"
    "layer17_watchdog.py|watch"
    "layer19_password_leak.py|watch"
    "layer21_ml_anomaly.py|watch"
    "layer25_ssl_monitor.py|watch"
    "layer29_30_identity.py|watch"
    "layer_fim.py|watch"
    "layer_rootkit.py|watch"
    "layer_multichannel.py|watch"
)

while true; do
    for svc in "${SERVICES[@]}"; do
        pattern="${svc%.py}"
        if ! pgrep -f "python.*$pattern" > /dev/null; then
            nohup python "$svc" >> "$LOGS/${svc}.log" 2>&1 &
        fi
    done

    for entry in "${LAYERS[@]}"; do
        fname="${entry%%|*}"
        sub="${entry##*|}"
        pattern="${fname%.py}"
        if ! pgrep -f "python.*$pattern" > /dev/null; then
            nohup python "$fname" "$sub" >> "$LOGS/${fname}.log" 2>&1 &
        fi
    done

    sleep 30
done
