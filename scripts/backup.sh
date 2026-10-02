#!/data/data/com.termux/files/usr/bin/bash
# VORIX Backup Script

BACKUP_DIR=~/vorix-backups
DATE=$(date +%Y%m%d-%H%M%S)
NAME="vorix-backup-$DATE"
TMP="/data/data/com.termux/files/home/$NAME"

mkdir -p "$BACKUP_DIR"
mkdir -p "$TMP"

echo "🛡️ VORIX Backup"
echo "================"

# ─── ۱. Config و Scripts ───
echo "[1/5] Config + Scripts..."
cp -r ~/vorix-hybrid/config "$TMP/"
cp -r ~/vorix-hybrid/scripts "$TMP/"
cp -r ~/vorix-hybrid/shared "$TMP/"
cp -r ~/vorix-hybrid/docs "$TMP/"

# ─── ۲. Phone (کد + لاگ‌های مهم) ───
echo "[2/5] Phone files..."
mkdir -p "$TMP/phone"

# Python files
find ~/vorix-hybrid/phone -maxdepth 1 -name "*.py" -exec cp {} "$TMP/phone/" \;
find ~/vorix-hybrid/phone -maxdepth 1 -name "*.sh" -exec cp {} "$TMP/phone/" \;
find ~/vorix-hybrid/phone -maxdepth 1 -name "vorix-all" -exec cp {} "$TMP/phone/" \;

# Config files
cp ~/vorix-hybrid/phone/config.json "$TMP/phone/" 2>/dev/null
cp ~/vorix-hybrid/phone/fim_baseline.json "$TMP/phone/" 2>/dev/null
cp ~/vorix-hybrid/phone/blocklist.json "$TMP/phone/" 2>/dev/null

# Logs
mkdir -p "$TMP/phone/logs"
cp ~/vorix-hybrid/phone/*.jsonl "$TMP/phone/" 2>/dev/null
cp ~/vorix-hybrid/phone/*.log "$TMP/phone/" 2>/dev/null
cp -r ~/vorix-hybrid/phone/logs "$TMP/phone/" 2>/dev/null

# ─── ۳. Root files ───
echo "[3/5] Root files..."
cp ~/vorix-hybrid/ROADMAP.md "$TMP/" 2>/dev/null
cp ~/vorix-hybrid/QUICK_ACCESS.md "$TMP/" 2>/dev/null
cp ~/vorix-hybrid/.gitignore "$TMP/" 2>/dev/null

# ─── ۴. توکن (مهم) ───
echo "[4/5] Token..."
mkdir -p "$TMP/secrets"
cp ~/vorix/.tg-token "$TMP/secrets/" 2>/dev/null

# ─── ۵. Metadata ───
echo "[5/5] Metadata..."
cat > "$TMP/README.txt" << EOF
VORIX Backup
=============
Date: $(date)
Host: $(hostname)
Uptime: $(uptime)

Files:
- config/       config مرکزی
- scripts/      switch-mode, test-connection
- shared/       schemas
- docs/         dashboard + migration
- phone/        کد لایه‌ها + لاگ‌ها
- secrets/      توکن تلگرام

Restore:
  tar xzf vorix-backup-*.tar.gz -C ~/
  cp secrets/.tg-token ~/vorix/.tg-token
  cd ~/vorix-hybrid && ./scripts/test-connection.sh
EOF

# ─── ساخت tar.gz ───
echo ""
echo "Creating archive..."
cd /data/data/com.termux/files/home
tar czf "$BACKUP_DIR/$NAME.tar.gz" "$NAME"
rm -rf "$TMP"

SIZE=$(du -h "$BACKUP_DIR/$NAME.tar.gz" | awk '{print $1}')
echo ""
echo "✅ Backup complete!"
echo "   File: $BACKUP_DIR/$NAME.tar.gz"
echo "   Size: $SIZE"
