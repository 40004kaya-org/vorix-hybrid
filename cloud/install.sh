#!/bin/bash
set -e
G='\033[0;32m'; Y='\033[1;33m'; C='\033[0;36m'; N='\033[0m'

echo -e "${C}"
echo "==========================================="
echo "   VORIX CLOUD INSTALLER"
echo "==========================================="
echo -e "${N}"

if [ "$EUID" -eq 0 ]; then SUDO=""; else SUDO="sudo"; fi

echo -e "${C}[1/6]${N} Update system..."
$SUDO apt update -qq && $SUDO apt upgrade -y -qq

echo -e "${C}[2/6]${N} Install tools..."
$SUDO apt install -y -qq curl wget git ufw fail2ban openssl

echo -e "${C}[3/6]${N} Install Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | $SUDO sh
    $SUDO usermod -aG docker $USER || true
    $SUDO systemctl enable docker
    $SUDO systemctl start docker
fi

echo -e "${C}[4/6]${N} Configure firewall..."
$SUDO ufw --force reset >/dev/null 2>&1 || true
$SUDO ufw default deny incoming
$SUDO ufw default allow outgoing
$SUDO ufw allow 22/tcp
$SUDO ufw allow 80/tcp
$SUDO ufw allow 443/tcp
$SUDO ufw allow 8443/tcp
$SUDO ufw --force enable

echo -e "${C}[5/6]${N} Setup environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    DB=$(openssl rand -hex 16)
    KEY=$(openssl rand -hex 32)
    sed -i "s|CHANGE_ME_STRONG_PASSWORD|$DB|" .env
    sed -i "s|REPLACE_WITH_RANDOM_KEY|$KEY|" .env
    echo ""
    echo -e "${G}===========================================${N}"
    echo -e "${G}   IMPORTANT — SAVE THESE!${N}"
    echo -e "${G}===========================================${N}"
    echo -e "${Y}DB_PASS:  ${N}$DB"
    echo -e "${Y}API_KEY:  ${N}$KEY"
    echo -e "${G}===========================================${N}"
    echo ""
fi

echo -e "${C}[6/6]${N} Start services..."
mkdir -p data/{postgres,redis}
$SUDO docker compose down 2>/dev/null || true
$SUDO docker compose up -d --build
sleep 15

echo ""
$SUDO docker compose ps
echo ""

if curl -s -m 5 http://localhost:8443/health | grep -q healthy; then
    IP=$(curl -s -m 5 ifconfig.me 2>/dev/null || echo "YOUR_IP")
    echo -e "${G}===========================================${N}"
    echo -e "${G}   VORIX CLOUD — RUNNING${N}"
    echo -e "${G}===========================================${N}"
    echo ""
    echo -e "${C}🌐 API:  http://$IP:8443/${N}"
    echo -e "${C}🏥 Health: http://$IP:8443/health${N}"
    echo ""
    echo -e "${Y}📌 Next: Put API_KEY in phone/config.json${N}"
    echo ""
else
    echo -e "⚠ Service starting... check: docker compose logs"
fi
