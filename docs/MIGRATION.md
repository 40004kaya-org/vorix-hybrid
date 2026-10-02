# VORIX Migration Guide

## Before Server
- Config: config/vorix.config.json
- Schema: shared/schemas/event.json
- Switch: scripts/switch-mode.sh
- Test: scripts/test-connection.sh

## DNS Subdomains
- @       -> Netlify
- www     -> Netlify
- api     -> [SERVER_IP]
- bot     -> [SERVER_IP]
- kibana  -> [SERVER_IP]

## When Server Arrives
1. ssh root@SERVER_IP
2. git clone https://github.com/40004kaya-org/vorix-hybrid
3. Edit config/vorix.config.json (set server.host)
4. ./scripts/switch-mode.sh hybrid
5. Update IRNIC DNS (A records for api/bot)
6. ./scripts/test-connection.sh

## Result
Phone -> Server API -> Dashboard
Zero downtime, fully automated.
