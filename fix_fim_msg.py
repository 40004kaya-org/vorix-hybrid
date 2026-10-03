#!/usr/bin/env python3
import os

FILE = os.path.expanduser("~/vorix-hybrid/phone/layer_fim.py")

with open(FILE) as f:
    src = f.read()

# fix خط 245
src = src.replace(
    'print(f"   ✅ Auto-restored from baseline")',
    'print(f"   ⚠️  Modified (alert-only, no restore)")'
)

# fix خط 169
src = src.replace(
    'f"Action: Auto-restored\\n"',
    'f"Action: Alert-only (no restore)\\n"'
)

with open(FILE, "w") as f:
    f.write(src)

print("OK - FIM messages fixed")
