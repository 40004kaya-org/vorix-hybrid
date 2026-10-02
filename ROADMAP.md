# VORIX Roadmap

آخرین آپدیت: 2026-10-02
Baseline: v1.0 (LOCKED)

## فاز 0 - پایه (تموم شد)

### 44 لایه امنیتی
- Ingress: L1, L2, L4, L6, L9, L13, L15, L-Rootkit
- Identity: L19, L29, L30
- Intelligence: L3, L21, L-MITRE
- Network: L7, L8, L11, L12, L25
- Application: L22, L23, L24, L26
- Data: L5, L31
- Self-Defense: L01, L-FIM
- SOAR: L-Response, L-Scoring, L-Reports, L-Multichannel, L-HashChain, L-Forensics, L-Mocker, L-Voice
- Infra: L-BOOT, L10, L16, L17, L18

### ربات تلگرام
- منوی 9 دکمه‌ای
- 7 دستور: /start /stats /history /layers /status /blocklist /hashchain
- Multichannel: Status, Detail, Block, Ignore, Forensics, Back

### LiveFeed
- پوش زنده <0.2s delay
- Watch: hash_chain, playbooks, layer10_events, killswitch_events, queue

### زیرساخت
- Keepalive + Crontab
- FIM alert-only
- Self-Defense 13 layer

## فاز 1 - Keepalive گسترش (10 دقیقه)

هدف: همه 12 لایه daemon خودکار restart شن

کارها:
- [ ] گسترش keepalive.sh
- [ ] اضافه 15 لایه به لیست watch
- [ ] تست: kill layer -> برگرده در 30s

## فاز 2 - Oracle Cloud (1 ساعت)

هدف: سرور 24/7 رایگان + IP خارجی

کارها:
- [ ] ثبت‌نام Oracle Free Tier
- [ ] ARM Ampere A1 (4 OCPU + 24GB)
- [ ] Ubuntu 22.04 + Docker
- [ ] Deploy VORIX Cloud
- [ ] Nginx + Let's Encrypt
- [ ] WireGuard Phone<->Cloud

## فاز 3 - دامنه + HTTPS (30 دقیقه)

کارها:
- [ ] خرید دامنه .xyz (~$1)
- [ ] DNS -> ArvanCloud (نه Cloudflare - تحریمه)
- [ ] Nginx + Let's Encrypt
- [ ] تست https://vorix.domain.xyz

## فاز 4 - ArvanCloud WAF (30 دقیقه)

کارها:
- [ ] ثبت‌نام ArvanCloud
- [ ] DNS + SSL + WAF + CDN
- [ ] تست از ایران

## فاز 5 - Kibana + Grafana (2 ساعت)

کارها:
- [ ] Docker: Elasticsearch + Kibana + Grafana
- [ ] اتصال به jsonl ها
- [ ] Dashboard: حملات زنده
- [ ] Alert rules

## فاز 6 - PWA موبایل (2 ساعت)

کارها:
- [ ] HTML + CSS + JS
- [ ] Service Worker
- [ ] Manifest + Push
- [ ] Login + Responsive

## فاز 7 - Phone<->Cloud Sync (1 ساعت)

کارها:
- [ ] Phone -> Cloud webhook
- [ ] Cloud -> Phone commands
- [ ] Fallback

## فاز 8 - CrowdSec (1 ساعت)

کارها:
- [ ] نصب CrowdSec
- [ ] Bouncers + Community blocklist
- [ ] اتصال به L2

## فاز 9 - تست نهایی (2 ساعت)

کارها:
- [ ] Pentest خارجی
- [ ] Load test
- [ ] Failover + Backup test
- [ ] Log rotation
- [ ] Documentation

## ساختار نهایی

~/vorix-hybrid/
  phone/     <- Termux (سنسور)
  cloud/     <- Oracle VPS
  shared/    <- مشترک
  docs/      <- مستندات
  ROADMAP.md

## اطلاعات کلیدی

- GitHub: 40004kaya-org/vorix-hybrid
- Bot: @vorix_security_bot
- Chat ID: 175160049
- Cloud: Oracle (بعد از فاز 2)
- Domain: vorix.??? (بعد از فاز 3)
- CDN: ArvanCloud (بعد از فاز 4)

## نکات مهم

### امنیت
- FIM alert-only (patch-safe)
- L01 محافظت 13 لایه
- keepalive + crontab مقاوم
- No hardcoded secrets

### تحریم
- X Cloudflare (بلاک IP ایران)
- OK ArvanCloud (ایرانی)
- OK Oracle Cloud (خارجی)

### Performance
- LiveFeed <0.2s
- 12 لایه daemon = 2% CPU
- RAM: 6GB/11GB

## نقطه شروع فعلی

الان: فاز 1 (Keepalive گسترش)
بعدش: فاز 2 (Oracle Cloud)
