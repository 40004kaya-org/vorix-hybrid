#!/usr/bin/env python3
"""VORIX Vault — بک‌آپ خودکار (هفتگی/روزانه/لحظه‌ای)"""
import sys, json, shutil, gzip, sqlite3, hashlib, time
from pathlib import Path
from datetime import datetime, timezone

HOME = Path.home()
VAULT = HOME / "vorix-vault"
WEEKLY = VAULT / "weekly"
DAILY = VAULT / "daily"
SNAPS = VAULT / "snapshots"
DOWNLOADS = HOME / "storage/downloads/vorix-vault"
LOG = VAULT / "vault.log"

for d in [VAULT, WEEKLY, DAILY, SNAPS, DOWNLOADS]:
    d.mkdir(parents=True, exist_ok=True)

SOURCES = {
    "shop_db": HOME / "myproject/vorix.db",
    "shop_env": HOME / "myproject/.env",
    "shop_data": HOME / "vorix-hybrid/shop-data",
    "scripts": HOME / "vorix-hybrid/phone",
    "docs_data": HOME / "vorix-hybrid/docs/data",
    "bridge": HOME / "shop-bridge-v2.py",
    "shield": HOME / "vorix-hybrid/phone/vorix_shop_shield.py",
    "vault_script": HOME / "vorix-vault.py",
}

CRITICAL = ["shop_db", "shop_env", "bridge", "shield", "vault_script"]

CONFIG = {
    "weekly_keep": 8, "daily_keep": 30, "snapshot_keep": 100,
    "snapshot_min_interval": 5,
    "hourly_interval": 600, "daily_interval": 86400, "weekly_interval": 604800,
}

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def backup_db(src, dest):
    try:
        if not src.exists(): return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        s = sqlite3.connect(str(src), timeout=5)
        d = sqlite3.connect(str(dest))
        s.backup(d); d.close(); s.close()
        return True
    except Exception as e:
        log(f"❌ DB: {e}"); return False

def verify_db(path):
    try:
        conn = sqlite3.connect(str(path))
        r = conn.execute("PRAGMA integrity_check").fetchone()[0]
        conn.close()
        return r == "ok"
    except: return False

def file_hash(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()[:16]
    except: return "?"

_last_snap = 0
def snapshot(label="auto"):
    global _last_snap
    now = time.time()
    if now - _last_snap < CONFIG["snapshot_min_interval"]: return None
    _last_snap = now
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = SNAPS / f"{ts}-{label}.db"
    if backup_db(SOURCES["shop_db"], dest) and verify_db(dest):
        files = sorted(SNAPS.glob("*.db"))
        for old in files[:-CONFIG["snapshot_keep"]]:
            old.unlink()
        return str(dest)
    return None

def daily_backup():
    ts = datetime.now().strftime("%Y%m%d")
    dest = DAILY / ts
    dest.mkdir(parents=True, exist_ok=True)
    manifest = {"type": "daily", "date": ts,
                "ts": datetime.now(timezone.utc).isoformat(), "items": {}}
    for name in CRITICAL:
        src = SOURCES.get(name)
        if not src or not src.exists(): continue
        try:
            if src.is_dir():
                shutil.copytree(src, dest / name, dirs_exist_ok=True)
                manifest["items"][name] = {"type": "dir"}
            else:
                shutil.copy2(src, dest / src.name)
                manifest["items"][name] = {"type": "file",
                    "size": src.stat().st_size, "hash": file_hash(src)}
        except Exception as e:
            log(f"  ⚠️ {name}: {e}")
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    dirs = sorted([d for d in DAILY.iterdir() if d.is_dir()])
    for old in dirs[:-CONFIG["daily_keep"]]:
        shutil.rmtree(old, ignore_errors=True)
    return str(dest)

def weekly_backup():
    ts = datetime.now().strftime("%Y-W%V")
    dest = WEEKLY / ts
    dest.mkdir(parents=True, exist_ok=True)
    manifest = {"type": "weekly", "week": ts,
                "ts": datetime.now(timezone.utc).isoformat(), "items": {}}
    for name, src in SOURCES.items():
        if not src.exists(): continue
        try:
            if src.is_dir():
                shutil.copytree(src, dest / name, dirs_exist_ok=True)
                manifest["items"][name] = {"type": "dir"}
            else:
                shutil.copy2(src, dest / src.name)
                manifest["items"][name] = {"type": "file",
                    "size": src.stat().st_size, "hash": file_hash(src)}
        except Exception as e:
            log(f"  ⚠️ {name}: {e}")
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    try:
        import tarfile
        dl = DOWNLOADS / f"vault-{ts}.tar.gz"
        with tarfile.open(dl, "w:gz") as tar:
            tar.add(dest, arcname=f"vault-{ts}")
        log(f"  📤 {dl.name}")
    except Exception as e:
        log(f"  ⚠️ tar: {e}")
    dirs = sorted([d for d in WEEKLY.iterdir() if d.is_dir()])
    for old in dirs[:-CONFIG["weekly_keep"]]:
        shutil.rmtree(old, ignore_errors=True)
    return str(dest)

def restore(source="latest"):
    log(f"🔧 RESTORE: {source}")
    src_dir = None
    if source in ("latest", "weekly"):
        dirs = sorted([d for d in WEEKLY.iterdir() if d.is_dir()])
        if dirs: src_dir = dirs[-1]
    elif source == "daily":
        dirs = sorted([d for d in DAILY.iterdir() if d.is_dir()])
        if dirs: src_dir = dirs[-1]
    elif source.startswith("2026-W"):
        src_dir = WEEKLY / source
    else:
        src_dir = DAILY / source
    if not src_dir or not src_dir.exists():
        log("❌ not found"); return False
    db = src_dir / "vorix.db"
    if db.exists() and verify_db(db):
        backup_db(SOURCES["shop_db"], SNAPS / f"before-restore-{int(time.time())}.db")
        shutil.copy2(db, SOURCES["shop_db"])
        log("  ✅ DB")
    for name in ["shop_data", "docs_data"]:
        sub = src_dir / name
        if sub.exists() and sub.is_dir():
            target = SOURCES.get(name)
            if target:
                shutil.copytree(sub, target, dirs_exist_ok=True)
                log(f"  ✅ {name}")
    for name in ["bridge", "shield"]:
        sub = src_dir / SOURCES[name].name
        if sub.exists():
            shutil.copy2(sub, SOURCES[name])
            log(f"  ✅ {name}")
    return True

def status():
    def cnt(p):
        if not p.exists(): return 0, 0
        files = [f for f in p.rglob("*") if f.is_file()]
        return len(files), round(sum(f.stat().st_size for f in files) / 1024 / 1024, 2)
    w_n, w_sz = cnt(WEEKLY)
    d_n, d_sz = cnt(DAILY)
    s_n, s_sz = cnt(SNAPS)
    return {
        "vault": str(VAULT),
        "weekly": {"dirs": len(list(WEEKLY.iterdir())), "files": w_n, "size_mb": w_sz},
        "daily": {"dirs": len(list(DAILY.iterdir())), "files": d_n, "size_mb": d_sz},
        "snapshots": {"count": s_n, "size_mb": s_sz},
        "total_mb": round(w_sz + d_sz + s_sz, 2),
        "db_ok": verify_db(SOURCES["shop_db"]),
    }

def main():
    log("🛡️ VORIX Vault started")
    log(f"   weekly: هفتگی | daily: روزانه | snapshot: هر ۱۰ دقیقه")
    now = time.time()
    last_snap = now
    last_daily = now - CONFIG["daily_interval"] + 60
    last_weekly = now - CONFIG["weekly_interval"] + 120
    if not list(WEEKLY.iterdir()):
        log("  🚀 first: weekly...")
        weekly_backup()
        last_weekly = time.time()
    if not list(DAILY.iterdir()):
        log("  🚀 first: daily...")
        daily_backup()
        last_daily = time.time()
    while True:
        try:
            now = time.time()
            if now - last_snap > CONFIG["hourly_interval"]:
                r = snapshot("auto")
                if r: log(f"  💾 snapshot")
                last_snap = now
            if now - last_daily > CONFIG["daily_interval"]:
                h = datetime.now().hour
                if 3 <= h <= 5:
                    r = daily_backup()
                    if r: log(f"  📅 daily: {Path(r).name}")
                    last_daily = now
                else:
                    last_daily = now - CONFIG["daily_interval"] + 3600
            if now - last_weekly > CONFIG["weekly_interval"]:
                d = datetime.now()
                if d.weekday() == 5 and 3 <= d.hour <= 5:
                    r = weekly_backup()
                    if r: log(f"  📦 weekly: {Path(r).name}")
                    last_weekly = now
                else:
                    last_weekly = now - CONFIG["weekly_interval"] + 3600
            time.sleep(60)
        except Exception as e:
            log(f"❌ {e}")
            time.sleep(60)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        main()
    else:
        cmd = sys.argv[1]
        if cmd == "snapshot": print(snapshot(sys.argv[2] if len(sys.argv) > 2 else "manual"))
        elif cmd == "daily": print(daily_backup())
        elif cmd == "weekly": print(weekly_backup())
        elif cmd == "status": print(json.dumps(status(), indent=2, ensure_ascii=False))
        elif cmd == "restore":
            src = sys.argv[2] if len(sys.argv) > 2 else "latest"
            print("✅" if restore(src) else "❌")
        elif cmd == "test":
            print("=== Weekly ==="); print("  ", weekly_backup())
            print("\n=== Daily ==="); print("  ", daily_backup())
            print("\n=== Status ==="); print(json.dumps(status(), indent=2, ensure_ascii=False))
