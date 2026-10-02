#!/usr/bin/env python3
import os

FILE = os.path.expanduser("~/vorix-hybrid/phone/layer_livefeed.py")

with open(FILE) as f:
    src = f.read()

# پیام start رو حذف کن
old = 'send("<b>Live Feed started</b>\\nAll events will appear here.")'
new = '# (start message removed)'

if old in src:
    src = src.replace(old, new)
    with open(FILE, "w") as f:
        f.write(src)
    print("OK - start message removed")
else:
    print("NOT FOUND - check the file manually")
    # نمایش خط حاوی send
    for i, line in enumerate(src.split("\n"), 1):
        if "Live Feed started" in line:
            print(f"Line {i}: {line}")
