#!/usr/bin/env python3
"""اضافه کردن ۱۵ لایه جدید به vorix-all و keepalive"""
import os, re

PHONE = os.path.expanduser("~/vorix-hybrid/phone")
VORIX_ALL = os.path.join(PHONE, "vorix-all")
KEEPALIVE = os.path.join(PHONE, "keepalive.sh")

NEW_LAYERS = [
    ("layer_heartbeat.py",     "L-Heartbeat",     "watch"),
    ("layer_guard.py",         "L-Guard",         "watch"),
    ("layer_canary.py",        "L-Canary",        "watch"),
    ("layer_seal.py",          "L-Seal",          "watch"),
    ("layer_quarantine.py",    "L-Quarantine",    "watch"),
    ("layer_aegis.py",         "L-Aegis",         "watch"),
    ("layer_beacon.py",        "L-Beacon",        "watch"),
    ("layer_whitelist.py",     "L-Whitelist",     "watch"),
    ("layer_resurrect.py",     "L-Resurrect",     "watch"),
    ("layer_feed.py",          "L-Feed",          "watch"),
    ("layer_honeytoken.py",    "L-Honeytoken",    "watch"),
    ("layer_tarpit.py",        "L-Tarpit",        "watch"),
    ("layer_mirror.py",        "L-Mirror",        "watch"),
    ("layer_watchtower.py",    "L-Watchtower",    "watch"),
    ("layer_chaos.py",         "L-Chaos",         "watch"),
]

# ─── vorix-all: پیدا کردن آرایه LAYERS ───
with open(VORIX_ALL) as f:
    src = f.read()

# پیدا کردن آخرین خط ")"
pattern = re.compile(r'(LAYERS=\([\s\S]*?)(\n\))', re.MULTILINE)
match = pattern.search(src)

if match:
    insert_lines = ""
    for fname, label, sub in NEW_LAYERS:
        insert_lines += f'    "{fname}|{sub}|{label}"\n'
    
    new_layers = match.group(1) + "\n" + insert_lines.rstrip() + match.group(2)
    src = src[:match.start()] + new_layers + src[match.end():]
    
    with open(VORIX_ALL, "w") as f:
        f.write(src)
    print("✅ 15 layers added to vorix-all")
else:
    print("❌ LAYERS array not found in vorix-all")

# ─── keepalive.sh: اضافه به لیست ───
with open(KEEPALIVE) as f:
    ksrc = f.read()

# پیدا کردن آرایه LAYERS تو keepalive
pattern2 = re.compile(r'(LAYERS=\([\s\S]*?)(\n\))', re.MULTILINE)
match2 = pattern2.search(ksrc)

if match2:
    insert_lines = ""
    for fname, label, sub in NEW_LAYERS:
        insert_lines += f'    "{fname}|{sub}"\n'
    
    new_layers = match2.group(1) + "\n" + insert_lines.rstrip() + match2.group(2)
    ksrc = ksrc[:match2.start()] + new_layers + ksrc[match2.end():]
    
    with open(KEEPALIVE, "w") as f:
        f.write(ksrc)
    print("✅ 15 layers added to keepalive")
else:
    print("⚠ LAYERS array not found in keepalive (skipped)")

print("")
print("🎉 Done")
