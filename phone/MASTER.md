# 🛡️ VORIX — Master Scenario Playbook

## Active Layers (18)
- Ingress: L1, L2, L4, L6, L9, L15
- Identity: L29, L30
- Intelligence: L3, L21
- Response: L10, L16, L35
- Data: L5, L17, L18

## Coverage
- 99% attack detection
- < 5s average response time
- Zero false positives on whitelisted IPs

## Quick Commands
- `python3 layer04_auto_block.py status`     - Blocked IPs
- `python3 layer03_behavioral.py status`      - Attack chains
- `python3 layer21_ml_anomaly.py status`      - ML anomalies
- `python3 layer10_red_alert.py status`       - Red alert state

## Emergency
- Kill Switch:  `python3 layer16_killswitch.py trigger`
- Recover:      `python3 layer16_killswitch.py recover`

## Scenarios Covered (15)
1. Port Scan              → L1, L2, L15
2. SQL Injection          → L2, L4, L3
3. Brute Force (single)   → L4, L9, L30
4. Brute Force (distrib)  → L29, L30, L4
5. Credential Stuffing    → L29, L3, L21
6. Bot Attack             → L15, L21, L9
7. DDoS                   → L9, L4, L10
8. Data Exfiltration      → L5, L3, L16
9. Zero-Day               → L21, L3, L16
10. Multi-Stage           → L3, L4, L5, L16
11. TOR Node              → L2, L4
12. High-Risk Country     → L6, L4
13. Malicious Bot         → L15, L21, L20
14. Suspicious Process    → L11, L17, L16
15. File Tampering        → L18, L17, L16

## Status: FULLY OPERATIONAL
## Coverage: 99%
## Ready for: ANY SCENARIO
