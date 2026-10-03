#!/usr/bin/env python3
import os, re

FILE = os.path.expanduser("~/vorix-hybrid/phone/vorix_bot.py")

with open(FILE) as f:
    src = f.read()

# اضافه import
if "layer_deep_link" not in src:
    src = src.replace(
        "from telegram import",
        "from layer_deep_link import handle_deep_link, diagnose, format_status_message, build_actions\nfrom telegram import",
        1
    )

# پیدا کردن تابع cmd_start یا proc_msg
# الگو: هرجایی که cmd == "/start" رو handle می‌کنه

old_pattern = 'if cmd in ("/start", "/menu"): show_main(c)'
new_pattern = '''if cmd in ("/start", "/menu"):
        # چک کن args داره (deep link)
        args = context.args if hasattr(context, 'args') else []
        if args and len(args) > 0:
            await handle_deep_link(update, context, args[0])
        else:
            show_main(c)'''

if old_pattern in src:
    src = src.replace(old_pattern, new_pattern)
    print("OK - deep link added")
else:
    print("Pattern not found. Searching...")
    for i, line in enumerate(src.split("\n"), 1):
        if "/start" in line or "show_main" in line:
            print(f"Line {i}: {line}")

with open(FILE, "w") as f:
    f.write(src)
