#!/usr/bin/env python3
"""تولید وضعیت زنده لایه‌ها"""
import os, json, subprocess
from datetime import datetime

PHONE = os.path.expanduser("~/vorix-hybrid/phone")
OUT = os.path.expanduser("~/vorix-hybrid/docs/data/live.json")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

# ─── ۴۲ لایه با فایل و mode ───
LAYERS = [
    ("L01", "layer01_selfdefense",       "watch"),
    ("L02", "layer02_threat_intel",      "on-demand"),
    ("L03", "layer03_behavioral",        "watch"),
    ("L04", "layer04_auto_block",        "watch"),
    ("L05", "layer05_data_quarantine",   "on-demand"),
    ("L06", "layer06_geoip_block",       "watch"),
    ("L07", "layer07_network_behavior",  "on-demand"),
    ("L08", "layer08_network_monitor",   "watch"),
    ("L09", "layer09_rate_limiter",      "watch"),
    ("L10", "layer10_red_alert",         "watch"),
    ("L11", "layer11_dns_sinkhole",      "on-demand"),
    ("L12", "layer12_reverse_dns",       "on-demand"),
    ("L13", "layer13_ua_filter",         "on-demand"),
    ("L15", "layer15_fingerprint",       "on-demand"),
    ("L16", "layer16_killswitch",        "on-demand"),
    ("L17", "layer17_watchdog",          "watch"),
    ("L18", "layer18_backup_verifier",   "on-demand"),
    ("L19", "layer19_password_leak",     "watch"),
    ("L21", "layer21_ml_anomaly",        "watch"),
    ("L22", "layer22_header_analysis",   "on-demand"),
    ("L23", "layer23_cookie_anomaly",    "on-demand"),
    ("L24", "layer24_session_hijack",    "on-demand"),
    ("L25", "layer25_ssl_monitor",       "watch"),
    ("L26", "layer26_hsts",              "on-demand"),
    ("L29", "layer29_30_identity",       "watch"),
    ("L31", "layer31_log_encryption",    "on-demand"),
    ("L-FIM",  "layer_fim",              "watch"),
    ("L-Root", "layer_rootkit",          "watch"),
    ("L-MC",   "layer_multichannel",     "watch"),
    ("L-LF",   "layer_livefeed",         "watch"),
    ("L-MITRE","layer_mitre",            "on-demand"),
    ("L-Resp", "layer_response",         "on-demand"),
    ("L-Scor", "layer_scoring",          "on-demand"),
    ("L-Rep",  "layer_reports",          "on-demand"),
    ("L-Fore", "layer_forensics",        "on-demand"),
    ("L-Hash", "layer_hashchain",        "on-demand"),
    ("L-Mock", "layer_mocker",           "on-demand"),
    ("L-Voice","layer_voice",            "on-demand"),
    ("L-Bot",  "vorix_bot",              "watch"),
    ("L-Sync", "sync_loop",              "watch"),
    ("L-Keep", "keepalive",              "watch"),
    ("L-Agent","agent",                  "watch"),
]

def is_running(pattern):
    try:
        r = subprocess.run(["pgrep", "-f", pattern], capture_output=True, timeout=2)
        return r.returncode == 0
    except:
        return False

def get_pid(pattern):
    try:
        r = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True, timeout=2)
        pids = [p for p in r.stdout.strip().split("\n") if p]
        return pids[0] if pids else None
    except:
        return None

# ─── ساخت وضعیت ───
status = []
for lid, base, mode in LAYERS:
    pattern = f"python.*{base}" if base != "sync_loop" and base != "keepalive" else base
    running = is_running(pattern)
    pid = get_pid(pattern) if running else None
    
    if running:
        color = "green"
        label = "فعال"
    elif mode == "on-demand":
        color = "yellow"
        label = "آماده"
    else:
        color = "red"
        label = "قطع"
    
    status.append({
        "id": lid,
        "file": base,
        "running": running,
        "pid": pid,
        "mode": mode,
        "color": color,
        "label": label,
    })

# ─── آمار کلی ───
counts = {
    "green":  sum(1 for s in status if s["color"] == "green"),
    "yellow": sum(1 for s in status if s["color"] == "yellow"),
    "orange": 0,
    "red":    sum(1 for s in status if s["color"] == "red"),
    "total":  len(status),
}

out = {
    "ts": datetime.utcnow().isoformat() + "Z",
    "layers": status,
    "stats": counts,
}

with open(OUT, "w") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)

print(f"✅ live.json: {counts['green']} active, {counts['yellow']} standby, {counts['red']} down")
