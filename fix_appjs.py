#!/usr/bin/env python3
import os

FILE = os.path.expanduser("~/vorix-hybrid/docs/app.js")

with open(FILE) as f:
    src = f.read()

# ۱. اضافه کردن safeBtoa helper
if "function safeBtoa" not in src:
    safe_helper = '''
// ─── SAFE BTOA (Unicode) ───
function safeBtoa(str) {
  try {
    return btoa(unescape(encodeURIComponent(str)));
  } catch(e) {
    return 'evt-' + Math.random().toString(36).slice(2) + '-' + Date.now();
  }
}
'''
    src = src.replace("// ─── HELPERS ───", safe_helper + "\n// ─── HELPERS ───")

# ۲. جایگزینی btoa با safeBtoa
src = src.replace(
    "const id = btoa(JSON.stringify(e)).slice(0, 20) + '-' + i;",
    "const id = 'evt-' + i + '-' + Date.now();"
)

# ۳. رفع باگ index (i) — در map بدون index کار نمی‌کنه
src = src.replace(
    """  const latest = events.slice(0, 10);
  container.innerHTML = latest.length 
    ? latest.map(renderEventHTML).join('')
    : '<div class="empty"><div class="empty-icon">📭</div>رویدادی ثبت نشده</div>';""",
    """  const latest = events.slice(0, 10);
  container.innerHTML = latest.length 
    ? latest.map((e, i) => renderEventHTML(e, i)).join('')
    : '<div class="empty"><div class="empty-icon">📭</div>رویدادی ثبت نشده</div>';"""
)

src = src.replace(
    """  allContainer.innerHTML = filtered.length
    ? filtered.map(renderEventHTML).join('')
    : '<div class="empty"><div class="empty-icon">🔍</div>رویدادی مطابق فیلتر پیدا نشد</div>';""",
    """  allContainer.innerHTML = filtered.length
    ? filtered.map((e, i) => renderEventHTML(e, i)).join('')
    : '<div class="empty"><div class="empty-icon">🔍</div>رویدادی مطابق فیلتر پیدا نشد</div>';"""
)

# ۴. رفع data-event-json با encodeURIComponent
src = src.replace(
    '''data-event-json='${JSON.stringify(e).replace(/'/g, "&#39;")}' ''',
    '''data-event-json='${encodeURIComponent(JSON.stringify(e))}' '''
)

# ۵. رفع showEventDetail برای decode
src = src.replace(
    "const e = JSON.parse(el.dataset.eventJson);",
    "const e = JSON.parse(decodeURIComponent(el.dataset.eventJson));"
)

# ۶. حذف تابع قدیمی safeBtoa (چون دیگه استفاده نمی‌کنیم)
src = src.replace(
    "const id = btoa(JSON.stringify(e)).slice(0, 20) + '-' + i;",
    ""
)

with open(FILE, "w") as f:
    f.write(src)

print("OK - app.js patched")

# نمایش بخش‌های تغییر یافته
print("\n--- renderEventHTML function ---")
for i, line in enumerate(src.split("\n"), 1):
    if "renderEventHTML" in line or "safeBtoa" in line or "evt-" in line:
        print(f"Line {i}: {line[:80]}")
