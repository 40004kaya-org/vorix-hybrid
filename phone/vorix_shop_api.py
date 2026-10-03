#!/usr/bin/env python3
"""VORIX Shop API — دریافت + export رویدادهای فروشگاه"""
from flask import Flask, request, jsonify
from pathlib import Path
from datetime import datetime, timezone
import json, sqlite3

app = Flask(__name__)
EVENTS = Path.home() / "vorix-hybrid/phone/shop_events.jsonl"
STATS = Path.home() / "vorix-hybrid/docs/data/shop_stats.json"
SHOP_DB = Path.home() / "myproject/vorix.db"
PORT = 8090

# ═══════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════
def load_events(limit=500):
    if not EVENTS.exists(): return []
    out = []
    with open(EVENTS) as f:
        for l in f.readlines()[-limit:]:
            try: out.append(json.loads(l))
            except: pass
    return out

def query(sql, params=(), limit=500):
    if not SHOP_DB.exists():
        return []
    try:
        conn = sqlite3.connect(str(SHOP_DB), timeout=5)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()[:limit]]
        conn.close()
        return rows
    except Exception as e:
        return [{"error": str(e)}]

def analyze(event):
    flags = []
    t = event.get("type", "")
    if t == "login_failed": flags.append("failed_login")
    if t == "order_new" and event.get("amount", 0) > 5000000:
        flags.append("high_order")
    if t == "user_new": flags.append("new_user")
    if t == "payment" and event.get("status") == "failed":
        flags.append("failed_payment")
    return flags

# ═══════════════════════════════════════
#  Ingest
# ═══════════════════════════════════════
@app.route("/ingest", methods=["POST"])
def ingest():
    try:
        event = request.json
        event["received_at"] = datetime.now(timezone.utc).isoformat()
        event["flags"] = analyze(event)

        EVENTS.parent.mkdir(parents=True, exist_ok=True)
        with open(EVENTS, "a") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

        return jsonify({"ok": True, "flags": event["flags"]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

# ═══════════════════════════════════════
#  Stats
# ═══════════════════════════════════════
@app.route("/stats", methods=["GET"])
def stats():
    events = load_events(500)
    by_type = {}
    flags_all = []
    for e in events:
        t = e.get("type", "?")
        by_type[t] = by_type.get(t, 0) + 1
        flags_all.extend(e.get("flags", []))

    out = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "total_events": len(events),
        "by_type": by_type,
        "users": sum(1 for e in events if e.get("type") == "user_new"),
        "orders": sum(1 for e in events if e.get("type") == "order_new"),
        "payments": sum(1 for e in events if e.get("type") == "payment"),
        "suspicious": sum(1 for f in flags_all if f in ["failed_login", "high_order", "failed_payment"]),
        "recent": events[-30:]
    }
    STATS.parent.mkdir(parents=True, exist_ok=True)
    STATS.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    return jsonify(out)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "port": PORT, "db_exists": SHOP_DB.exists()})

# ═══════════════════════════════════════
#  Shop Export Endpoints
# ═══════════════════════════════════════
@app.route("/shop/users", methods=["GET"])
def shop_users():
    rows = query("SELECT user_id, username, first_name, phone, city, customer_code FROM users ORDER BY user_id DESC LIMIT 200")
    return jsonify({"users": rows, "count": len(rows)})

@app.route("/shop/orders", methods=["GET"])
def shop_orders():
    rows = query("SELECT id, user_id, total_price, status, created_at, invoice_number, customer_username, customer_name FROM orders ORDER BY id DESC LIMIT 200")
    return jsonify({"orders": rows, "count": len(rows)})

@app.route("/shop/payments", methods=["GET"])
def shop_payments():
    rows = query("SELECT id, user_id, amount_toman, status, plan_key, created_at FROM pending_payments ORDER BY id DESC LIMIT 200")
    return jsonify({"payments": rows, "count": len(rows)})

@app.route("/shop/activity", methods=["GET"])
def shop_activity():
    rows = query("SELECT id, user_id, action, details, created_at FROM activity_log ORDER BY id DESC LIMIT 300")
    return jsonify({"activity": rows, "count": len(rows)})

@app.route("/shop/receipts", methods=["GET"])
def shop_receipts():
    rows = query("SELECT id, order_id, user_id, invoice_number, status FROM shop_payment_receipts ORDER BY id DESC LIMIT 100")
    return jsonify({"receipts": rows, "count": len(rows)})

@app.route("/shop/all", methods=["GET"])
def shop_all():
    return jsonify({
        "ts": datetime.now(timezone.utc).isoformat(),
        "users": query("SELECT user_id, username, first_name, phone, city, customer_code FROM users ORDER BY user_id DESC LIMIT 200"),
        "orders": query("SELECT id, user_id, total_price, status, created_at, invoice_number, customer_username FROM orders ORDER BY id DESC LIMIT 200"),
        "payments": query("SELECT id, user_id, amount_toman, status, plan_key, created_at FROM pending_payments ORDER BY id DESC LIMIT 200"),
        "activity": query("SELECT id, user_id, action, details, created_at FROM activity_log ORDER BY id DESC LIMIT 300"),
        "receipts": query("SELECT id, order_id, user_id, invoice_number, status FROM shop_payment_receipts ORDER BY id DESC LIMIT 100"),
    })

@app.route("/shop/security", methods=["GET"])
def shop_security():
    events = load_events(1000)
    suspicious = []
    attackers = {}
    for e in events:
        flags = e.get("flags", [])
        if any(f in flags for f in ["failed_login", "high_order", "failed_payment"]):
            ip = e.get("ip", "unknown")
            suspicious.append(e)
            attackers[ip] = attackers.get(ip, 0) + 1
    return jsonify({
        "ts": datetime.now(timezone.utc).isoformat(),
        "suspicious_count": len(suspicious),
        "suspicious_recent": suspicious[-50:],
        "attackers": attackers,
        "total_events": len(events),
    })

# ═══════════════════════════════════════
#  Main
# ═══════════════════════════════════════
if __name__ == "__main__":
    print(f"🚀 VORIX Shop API on http://0.0.0.0:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
