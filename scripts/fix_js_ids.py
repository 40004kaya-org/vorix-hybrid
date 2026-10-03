#!/usr/bin/env python3
import re

f = '/data/data/com.termux/files/home/vorix-hybrid/docs/mainboard.js'
with open(f) as fh:
    src = fh.read()

# ─── Fix 1: row1 → chipset1, row2 → chipset2 ───
src = src.replace("renderRow('row1', ROW1)", "renderRow('chipset1', ROW1)")
src = src.replace("renderRow('row2', ROW2)", "renderRow('chipset2', ROW2)")

# ─── Fix 2: b-stats → bottom ───
src = src.replace("getElementById('b-stats')", "getElementById('bottom')")

# ─── Fix 3: core-pct → core-percent (اگه هست) ───
src = src.replace("getElementById('core-pct')", "getElementById('core-percent')")

# ─── Fix 4: اضافه I/O ports rendering ───
if "renderIOPorts" not in src:
    io_func = '''
function renderIOPorts() {
  const el = document.getElementById('ioports');
  if (!el) return;
  const ports = [
    { name: 'Phone', icon: '📱' },
    { name: 'Web',   icon: '🌐' },
    { name: 'Bot',   icon: '🤖' },
    { name: 'API',   icon: '📊' }
  ];
  el.innerHTML = ports.map(p => 
    '<div class="ioport"><div class="ioport-led"></div><span>' + p.icon + '</span><span class="ioport-name">' + p.name + '</span></div>'
  ).join('');
}
'''
    # اضافه قبل از renderStats یا هرجای مناسب
    src = src.replace('function renderStats()', io_func + '\nfunction renderStats()')

# ─── Fix 5: اضافه renderIOPorts به load ───
if "renderIOPorts()" not in src.split("async function load")[1].split("}")[0] if "async function load" in src else "":
    src = src.replace("renderStats();\n    updateAlert();", "renderStats();\n    renderIOPorts();\n    updateAlert();")

# ─── Fix 6: اضافه core-percent به HTML IDs اگه نیست ───

with open(f, 'w') as fh:
    fh.write(src)

print("OK - JS IDs fixed")
print("  row1 → chipset1")
print("  row2 → chipset2")
print("  b-stats → bottom")
print("  core-pct → core-percent")
print("  + renderIOPorts added")
