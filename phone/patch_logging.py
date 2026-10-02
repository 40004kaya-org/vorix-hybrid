#!/usr/bin/env python3
import os, re

FILE = os.path.expanduser("~/vorix-hybrid/phone/vorix_bot.py")

with open(FILE) as f:
    src = f.read()

# ─── اضافه کردن log function ───
LOG_FUNC = '''
LOG_FILE = os.path.join(BASE, "vorix_bot.log")

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "[" + ts + "] " + msg
    print(line)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\\n")
    except: pass
'''

if "def log(" not in src:
    src = src.replace(
        'def read_json(n):',
        LOG_FUNC + '\ndef read_json(n):'
    )

# ─── log در getUpdates ───
src = src.replace(
    'if "callback_query" in u: proc_cb(u["callback_query"])',
    'if "callback_query" in u:\n                    log("CALLBACK: " + u["callback_query"].get("data", "?"))\n                    proc_cb(u["callback_query"])'
)
src = src.replace(
    'elif "message" in u: proc_msg(u["message"])',
    'elif "message" in u:\n                    log("MSG: " + u["message"].get("text", "?")[:50])\n                    proc_msg(u["message"])'
)

# ─── log در ارسال ───
src = src.replace(
    'tg("sendMessage", **p)',
    'r = tg("sendMessage", **p)\n    log("SEND: " + text[:50].replace("\\n", " ") + " -> " + str(r.get("ok", False)))'
)

with open(FILE, "w") as f:
    f.write(src)

print("OK - logging added")
