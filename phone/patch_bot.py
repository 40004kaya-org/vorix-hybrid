#!/usr/bin/env python3
import os, re

FILE = os.path.expanduser("~/vorix-hybrid/phone/vorix_bot.py")

with open(FILE) as f:
    src = f.read()

# ─── تابع edit قدیمی ───
pattern = re.compile(
    r'def edit\(chat_id, mid, text, kb=None\):.*?tg\("editMessageText", \*\*p\)',
    re.DOTALL,
)

NEW_EDIT = '''def edit(chat_id, mid, text, kb=None):
    if mid:
        p = {"chat_id": chat_id, "message_id": mid, "text": text, "parse_mode": "HTML"}
        if kb: p["reply_markup"] = {"inline_keyboard": kb}
        tg("editMessageText", **p)
    else:
        send(chat_id, text, kb)'''

new_src, count = pattern.subn(lambda m: NEW_EDIT, src)

if count == 0:
    print("ERROR: edit function not found")
    exit(1)

with open(FILE, "w") as f:
    f.write(new_src)

print("OK - patched edit()")
print("now falls back to sendMessage if message_id is None")
