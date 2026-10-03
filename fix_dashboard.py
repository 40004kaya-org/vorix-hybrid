#!/usr/bin/env python3
import os

FILE = os.path.expanduser("~/vorix-hybrid/docs/index.html")

with open(FILE) as f:
    html = f.read()

# fix blocked counter
if "stats.blocked || 0" not in html:
    html = html.replace(
        "document.getElementById('critical').textContent = stats.critical || 0;",
        "document.getElementById('critical').textContent = stats.critical || 0;\n    document.getElementById('blocked').textContent = stats.blocked || 0;"
    )

# fix event formatting
OLD = """      const sev = String(e.severity || e.event_type || 'INFO').toUpperCase();
      const cls = sev.includes('CRIT') ? 'CRITICAL' : sev.includes('WARN') ? 'WARN' : 'INFO';
      const ts = e.ts || e.timestamp || '';
      const msg = e.message || e.event || e.event_type || JSON.stringify(e).slice(0,100);"""

NEW = """      const sev = String(e.severity || e.event_type || e.attack || 'INFO').toUpperCase();
      const cls = sev.includes('CRIT') ? 'CRITICAL' : sev.includes('WARN') ? 'WARN' : 'INFO';
      const ts = e.ts || e.timestamp || '';
      let msg = '';
      if (e.message) msg = e.message;
      else if (e.event) msg = e.event;
      else if (e.event_type) msg = e.event_type;
      else if (e.attack) msg = e.attack + (e.ip ? ' از ' + e.ip : '');
      else msg = JSON.stringify(e).slice(0, 100);"""

if OLD in html:
    html = html.replace(OLD, NEW)
    print("events: fixed")
else:
    print("events: pattern not found (maybe already fixed)")

with open(FILE, "w") as f:
    f.write(html)

print("OK")
