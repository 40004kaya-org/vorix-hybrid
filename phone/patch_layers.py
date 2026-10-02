#!/usr/bin/env python3
import os, re

FILE = os.path.expanduser("~/vorix-hybrid/phone/vorix-all")

with open(FILE) as f:
    src = f.read()

# آرایه جدید LAYERS
NEW_LAYERS = '''LAYERS=(
    "layer01_selfdefense.py:L01 Anti-Kill:watch"
    "layer03_behavioral.py:L3 Behavioral:watch"
    "layer04_auto_block.py:L4 Auto-Block:watch"
    "layer06_geoip_block.py:L6 GeoIP Block:watch"
    "layer08_network_monitor.py:L8 Net Monitor:watch"
    "layer09_rate_limiter.py:L9 Rate Limiter:watch"
    "layer10_red_alert.py:L10 Red Alert:watch"
    "layer17_watchdog.py:L17 Watchdog:watch"
    "layer18_backup_verifier.py:L18 Backup Verifier:check"
    "layer19_password_leak.py:L19 Password Leak:watch"
    "layer21_ml_anomaly.py:L21 ML Anomaly:watch"
    "layer25_ssl_monitor.py:L25 SSL Monitor:watch"
    "layer29_30_identity.py:L29-30 Identity:watch"
    "layer_multichannel.py:L-Multichannel:watch"
    "layer_fim.py:L-FIM:watch"
    "layer_rootkit.py:L-Rootkit:watch"
    "layer_mitre.py:L-MITRE"
    "layer_mocker.py:L-Mocker"
    "layer_reports.py:L-Reports"
    "layer_response.py:L-Response"
    "layer_scoring.py:L-Scoring"
    "layer_forensics.py:L-Forensics"
    "layer_hashchain.py:L-HashChain"
    "layer_voice.py:L-Voice"
)'''

pattern = re.compile(r'LAYERS=\(.*?\n\)', re.DOTALL)
new_src, count = pattern.subn(lambda m: NEW_LAYERS, src)

if count == 0:
    print("ERROR: LAYERS array not found")
    exit(1)

# اصلاح حلقه start که subcommand رو از entry بگیره
new_src = new_src.replace(
    '''        cd "$BASE"
        nohup python "$fname" >> "$LOGS/${fname}.log" 2>&1 &''',
    '''        cd "$BASE"
        local sub="${label##*:}"
        [ "$sub" = "$label" ] && sub=""
        if [ -n "$sub" ]; then
            nohup python "$fname" "$sub" >> "$LOGS/${fname}.log" 2>&1 &
        else
            nohup python "$fname" >> "$LOGS/${fname}.log" 2>&1 &
        fi'''
)

with open(FILE, "w") as f:
    f.write(new_src)

print("OK - LAYERS patched to 24 layers")
