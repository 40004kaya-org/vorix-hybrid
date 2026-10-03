#!/usr/bin/env python3
"""L8 — Advanced Network Monitor"""
import os, sys, json, time, subprocess, threading, math
from datetime import datetime, timedelta
from collections import defaultdict, Counter, deque

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
STATE_FILE = os.path.join(BASE, "layer08_state.json")
TRAFFIC_FILE = os.path.join(BASE, "layer08_traffic.jsonl")

sys.path.insert(0, BASE)
from layer04_auto_block import AutoBlock

try:
    import requests
    with open(os.path.join(HOME, "vorix/.tg-token")) as f:
        TG = f.read().strip()
except:
    TG = ""
CHAT = "175160049"

# ═══════════════════════════════════════════════
#   CONFIG — قوی‌تر
# ═══════════════════════════════════════════════
CONFIG = {
    "scan_interval": 15,
    
    # Connection thresholds
    "high_connections": 80,
    "port_scan_threshold": 15,
    "unusual_ports_threshold": 10,
    
    # Bandwidth
    "high_bandwidth_mb": 100,      # ۱۰۰MB+ در دقیقه → مشکوک
    "data_exfil_threshold_mb": 500, # ۵۰۰MB+ در ۵ دقیقه → exfil
    
    # Beaconing (C2 pattern)
    "beacon_regularity": 0.8,      # ۸۰٪+ شباهت بین intervals
    "beacon_min_calls": 5,          # حداقل ۵ تماس
    "beacon_interval_range": (5, 300),  # بین ۵ تا ۳۰۰ ثانیه
    
    # DNS Tunnel
    "dns_query_max_size": 200,      # کوئری بیش از ۲۰۰ بایت → تونل
    "dns_many_subdomains": 20,      # ۲۰+ ساب‌دامین از یک دامنه
    
    # Time patterns
    "suspicious_hours": [0, 1, 2, 3, 4],  # ۱۲ شب تا ۵ صبح
    "notify": True,
}

# پورت‌های مشکوک
SUSPICIOUS_PORTS = {
    23: "Telnet",
    445: "SMB",
    3389: "RDP",
    1433: "MSSQL",
    5900: "VNC",
    3306: "MySQL",
    5432: "PostgreSQL",
    6379: "Redis",
    27017: "MongoDB",
    9200: "Elasticsearch",
    21: "FTP",
    25: "SMTP",
    135: "RPC",
    139: "NetBIOS",
    161: "SNMP",
    162: "SNMP Trap",
    1434: "MSSQL Admin",
    5555: "ADB",
    4444: "Metasploit",
    31337: "Elite/Back Orifice",
    6667: "IRC",
    6666: "IRC",
    8888: "Sun Answerbook",
    1337: "Elite",
}

# TLD های مشکوک
SUSPICIOUS_TLDS = [".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top", ".work", ".click", ".link"]

PRIVATE = ("127.", "10.", "192.168.", "172.16.", "172.17.", "172.18.",
           "172.19.", "172.20.", "172.21.", "172.22.", "172.23.",
           "172.24.", "172.25.", "172.26.", "172.27.", "172.28.",
           "172.29.", "172.30.", "172.31.", "169.254.")


class AdvancedNetworkMonitor:
    def __init__(self):
        self.connections = defaultdict(lambda: {
            "count": 0,
            "ports": Counter(),
            "first_seen": time.time(),
            "last_seen": time.time(),
            "bytes_in": 0,
            "bytes_out": 0,
            "timestamps": deque(maxlen=100),  # برای beaconing
            "dns_queries": [],
        })
        
        # Global stats
        self.global_conns = deque(maxlen=5000)
        self.beaconing_ips = set()
        self.dns_tunnels = defaultdict(set)
        self.ab = AutoBlock()
        self.lock = threading.Lock()
        self.last_scan = 0
        
        self.stats = {
            "scans": 0,
            "high_conns": 0,
            "port_scans": 0,
            "suspicious_ports": 0,
            "beaconing": 0,
            "dns_tunnels": 0,
            "data_exfil": 0,
            "suspicious_hours": 0,
            "started": time.time(),
        }
        self.load_state()

    def load_state(self):
        try:
            with open(STATE_FILE) as f:
                s = json.load(f)
                self.stats = s.get("stats", self.stats)
        except: pass

    def save_state(self):
        try:
            with open(STATE_FILE, "w") as f:
                json.dump({"stats": self.stats}, f, indent=2)
        except: pass

    def is_private(self, ip):
        return any(ip.startswith(p) for p in PRIVATE)

    def is_suspicious_hour(self):
        """آیا ساعت مشکوکه؟"""
        return datetime.now().hour in CONFIG["suspicious_hours"]

    # ─────────────────────────────────────────
    #   SCAN CONNECTIONS (از /proc و netstat)
    # ─────────────────────────────────────────
    def scan_connections(self):
        """اسکن اتصالات فعال"""
        try:
            # تلاش برای /proc/net/tcp
            conns = defaultdict(lambda: {"count": 0, "ports": Counter()})
            
            for fname in ["/proc/net/tcp", "/proc/net/tcp6", "/proc/net/udp"]:
                try:
                    with open(fname) as f:
                        f.readline()  # skip header
                        for line in f:
                            parts = line.split()
                            if len(parts) < 4: continue
                            
                            remote_hex = parts[2]
                            state = parts[3]
                            
                            # فقط ESTABLISHED
                            if state != "01": continue
                            
                            # پارس IP و پورت
                            if ":" in remote_hex:
                                ip_hex, port_hex = remote_hex.rsplit(":", 1)
                                try:
                                    port = int(port_hex, 16)
                                except: continue
                                
                                if fname.endswith("tcp6") or len(ip_hex) == 32:
                                    # IPv6 — skip
                                    continue
                                
                                # IPv4
                                if len(ip_hex) == 8:
                                    ip_parts = [str(int(ip_hex[i:i+2], 16)) for i in range(0, 8, 2)]
                                    ip = ".".join(reversed(ip_parts))
                                else:
                                    continue
                            else:
                                continue
                            
                            if self.is_private(ip) or not ip or ip == "0.0.0.0":
                                continue
                            
                            conns[ip]["count"] += 1
                            conns[ip]["ports"][port] += 1
                            self.global_conns.append({
                                "ts": time.time(),
                                "ip": ip,
                                "port": port,
                            })
                except FileNotFoundError:
                    pass

            # fallback با netstat
            if not conns:
                try:
                    r = subprocess.run(["netstat", "-tun"], capture_output=True, text=True, timeout=5)
                    for line in r.stdout.split("\n"):
                        if "ESTABLISHED" not in line: continue
                        parts = line.split()
                        if len(parts) < 5: continue
                        remote = parts[4]
                        if ":" not in remote: continue
                        ip = remote.rsplit(":", 1)[0]
                        try:
                            port = int(remote.rsplit(":", 1)[1])
                        except: continue
                        if self.is_private(ip) or not ip: continue
                        conns[ip]["count"] += 1
                        conns[ip]["ports"][port] += 1
                except: pass

            return conns
        except Exception as e:
            print(f"⚠️ Scan error: {e}")
            return {}

    # ─────────────────────────────────────────
    #   BEACONING DETECTION (C2 pattern)
    # ─────────────────────────────────────────
    def detect_beaconing(self, ip):
        """تشخیص الگوی beaconing (C2 server)"""
        with self.lock:
            history = self.connections[ip]["timestamps"]
            if len(history) < CONFIG["beacon_min_calls"]:
                return False

            # محاسبه intervals
            times = sorted(history)
            intervals = [times[i+1] - times[i] for i in range(len(times)-1)]
            
            if len(intervals) < 3:
                return False

            # میانگین
            avg = sum(intervals) / len(intervals)
            
            # اگه خارج از بازه معمول → نه beaconing
            min_int, max_int = CONFIG["beacon_interval_range"]
            if avg < min_int or avg > max_int:
                return False

            # std — هرچه کمتر → منظم‌تر
            variance = sum((i - avg) ** 2 for i in intervals) / len(intervals)
            std = math.sqrt(variance) if variance > 0 else 0

            # ضریب تغییرات
            cv = std / avg if avg > 0 else 1

            # اگه CV کم بود (یعنی منظم) → beaconing
            if cv < 0.3 and ip not in self.beaconing_ips:
                self.beaconing_ips.add(ip)
                self.stats["beaconing"] += 1
                return True
            return False

    # ─────────────────────────────────────────
    #   DNS TUNNEL DETECTION
    # ─────────────────────────────────────────
    def detect_dns_tunnel(self, ip, ports):
        """تشخیص DNS tunnel"""
        # اگر پورت ۵۳ باشه
        if 53 not in ports: return False
        
        with self.lock:
            # اضافه کوئری
            ts = time.time()
            self.connections[ip]["dns_queries"].append(ts)
            # نگه‌داشتن ۱۰۰ تای آخر
            self.connections[ip]["dns_queries"] = [
                t for t in self.connections[ip]["dns_queries"]
                if ts - t < 300
            ]
            
            # اگر تعداد زیاد بود → مشکوک
            if len(self.connections[ip]["dns_queries"]) > CONFIG["dns_many_subdomains"]:
                if ip not in self.dns_tunnels:
                    self.dns_tunnels[ip] = set()
                self.stats["dns_tunnels"] += 1
                return True
        return False

    # ─────────────────────────────────────────
    #   ANALYZE CONNECTIONS
    # ─────────────────────────────────────────
    def analyze(self, new_conns):
        findings = []
        now = time.time()

        for ip, info in new_conns.items():
            count = info["count"]
            ports = info["ports"]
            unique_ports = len(ports)

            # ذخیره در history
            with self.lock:
                h = self.connections[ip]
                h["count"] += count
                h["ports"] += ports
                h["last_seen"] = now
                h["timestamps"].append(now)

            # ═══ 1. HIGH CONNECTIONS ═══
            if count >= CONFIG["high_connections"]:
                self.stats["high_conns"] += 1
                self.ab.block(ip, f"high_conn_{count}", score=70, ip_type="temp")
                findings.append((ip, "HIGH_CONNECTIONS", f"{count} connections"))

            # ═══ 2. PORT SCAN ═══
            if unique_ports >= CONFIG["port_scan_threshold"]:
                self.stats["port_scans"] += 1
                self.ab.block(ip, f"port_scan_{unique_ports}", score=85, ip_type="perm")
                findings.append((ip, "PORT_SCAN", f"{unique_ports} unique ports"))

            # ═══ 3. SUSPICIOUS PORTS ═══
            suspicious = [p for p in ports if p in SUSPICIOUS_PORTS]
            if suspicious:
                names = ", ".join(f"{p}({SUSPICIOUS_PORTS[p]})" for p in suspicious[:3])
                self.stats["suspicious_ports"] += 1
                findings.append((ip, "SUSPICIOUS_PORT", names))

            # ═══ 4. BEACONING (C2) ═══
            if self.detect_beaconing(ip):
                self.ab.block(ip, f"beaconing_c2", score=90, ip_type="perm")
                findings.append((ip, "BEACONING", "Regular C2 pattern detected"))

            # ═══ 5. DNS TUNNEL ═══
            if self.detect_dns_tunnel(ip, ports):
                self.ab.block(ip, "dns_tunnel", score=85, ip_type="temp")
                findings.append((ip, "DNS_TUNNEL", "Possible DNS tunneling"))

            # ═══ 6. SUSPICIOUS HOUR ═══
            if self.is_suspicious_hour() and count > 5:
                self.stats["suspicious_hours"] += 1
                findings.append((ip, "SUSPICIOUS_HOUR", f"Active at {datetime.now().hour}:00"))

        # ارسال alert‌ها
        for ip, etype, detail in findings:
            self._alert(ip, etype, detail)

        return findings

    # ─────────────────────────────────────────
    #   ALERT
    # ─────────────────────────────────────────
    def _alert(self, ip, etype, detail):
        if not CONFIG["notify"] or not TG:
            return
        try:
            icons = {
                "HIGH_CONNECTIONS": "🌐",
                "PORT_SCAN": "🔍",
                "SUSPICIOUS_PORT": "⚠️",
                "BEACONING": "📡",
                "DNS_TUNNEL": "🚇",
                "SUSPICIOUS_HOUR": "🌙",
                "DATA_EXFIL": "📤",
            }
            icon = icons.get(etype, "⚠️")
            
            severity = "CRITICAL" if etype in ("BEACONING", "DNS_TUNNEL", "PORT_SCAN") else "WARN"
            
            msg = (
                f"{icon} *Network Monitor — {severity}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Type: `{etype}`\n"
                f"IP: `{ip}`\n"
                f"Detail: {detail}\n"
                f"Time: {datetime.now().strftime('%H:%M:%S')}"
            )
            requests.post(
                f"https://api.telegram.org/bot{TG}/sendMessage",
                json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
            
            if severity == "CRITICAL":
                os.system('termux-vibrate -d 300 2>/dev/null')
        except: pass

    # ─────────────────────────────────────────
    #   TOP TALKERS
    # ─────────────────────────────────────────
    def top_talkers(self, limit=10):
        """پرترافیک‌ترین IPها"""
        with self.lock:
            sorted_ips = sorted(
                self.connections.items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )[:limit]
            return sorted_ips

    # ─────────────────────────────────────────
    #   WATCH
    # ─────────────────────────────────────────
    def watch(self):
        print("🌐 L8 Advanced Network Monitor")
        print(f"📊 High conn: {CONFIG['high_connections']}")
        print(f"📊 Port scan: {CONFIG['port_scan_threshold']}")
        print(f"📊 Beaconing: CV < 0.3 with {CONFIG['beacon_min_calls']}+ calls")
        print(f"📊 DNS tunnel: > {CONFIG['dns_many_subdomains']} queries")
        print(f"📊 Suspicious hours: {CONFIG['suspicious_hours']}")
        print()

        last_report = time.time()

        while True:
            try:
                conns = self.scan_connections()
                self.stats["scans"] += 1
                
                if conns:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {len(conns)} IPs, {sum(c['count'] for c in conns.values())} conns")
                    findings = self.analyze(conns)
                    for f in findings:
                        print(f"   ⚠️ {f[1]}: {f[0]} ({f[2]})")

                # گزارش هر ۵ دقیقه
                if time.time() - last_report > 300:
                    self._periodic_report()
                    last_report = time.time()

                self.save_state()
                time.sleep(CONFIG["scan_interval"])
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"⚠️ {e}")
                time.sleep(10)

    def _periodic_report(self):
        """گزارش دوره‌ای"""
        if not TG: return
        try:
            top = self.top_talkers(5)
            if not top: return
            
            lines = []
            for ip, info in top:
                lines.append(f"  • `{ip}` — {info['count']} conns")
            
            msg = (
                f"📊 *Network Report*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🌐 Tracked IPs: `{len(self.connections)}`\n"
                f"🔍 Port scans: `{self.stats['port_scans']}`\n"
                f"📡 Beaconing: `{self.stats['beaconing']}`\n"
                f"🚇 DNS tunnels: `{self.stats['dns_tunnels']}`\n\n"
                f"🔝 *Top Talkers:*\n" + "\n".join(lines)
            )
            requests.post(
                f"https://api.telegram.org/bot{TG}/sendMessage",
                json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
        except: pass

    def status(self):
        uptime = int(time.time() - self.stats["started"])
        h, m = divmod(uptime // 60, 60)
        print(f"\n🌐 L8 Network Monitor Status")
        print(f"═══════════════════════════════")
        print(f"Uptime:              {h}h {m}m")
        print(f"Scans:               {self.stats['scans']}")
        print(f"High connections:    {self.stats['high_conns']}")
        print(f"Port scans:          {self.stats['port_scans']}")
        print(f"Suspicious ports:    {self.stats['suspicious_ports']}")
        print(f"Beaconing (C2):      {self.stats['beaconing']}")
        print(f"DNS tunnels:         {self.stats['dns_tunnels']}")
        print(f"Suspicious hours:    {self.stats['suspicious_hours']}")
        print()
        print(f"📊 Tracked: {len(self.connections)} IPs")
        
        if self.beaconing_ips:
            print(f"\n📡 Beaconing IPs:")
            for ip in list(self.beaconing_ips)[:5]:
                print(f"   • {ip}")
        
        if self.dns_tunnels:
            print(f"\n🚇 DNS Tunnel IPs:")
            for ip in list(self.dns_tunnels.keys())[:5]:
                print(f"   • {ip}")

    def test(self):
        """تست"""
        print("🧪 Testing Advanced Network Monitor\n")
        
        # تست ۱: High connections
        print("📍 Test 1: High connections (150)")
        self.analyze({"1.2.3.4": {"count": 150, "ports": Counter([80, 443])}})
        
        # تست ۲: Port scan
        print("\n📍 Test 2: Port scan (25 ports)")
        ports = Counter({p: 1 for p in range(1, 26)})
        self.analyze({"5.6.7.8": {"count": 25, "ports": ports}})
        
        # تست ۳: Beaconing
        print("\n📍 Test 3: Beaconing (regular intervals)")
        ip = "10.20.30.40"
        for i in range(10):
            self.connections[ip]["timestamps"].append(time.time() - (10 - i) * 60)
        if self.detect_beaconing(ip):
            print(f"   ✅ Beaconing detected: {ip}")
        
        # تست ۴: DNS tunnel
        print("\n📍 Test 4: DNS tunnel (25 queries)")
        ip = "50.60.70.80"
        for i in range(25):
            self.detect_dns_tunnel(ip, Counter({53: 1}))
        
        print("\n✅ Tests complete\n")
        self.status()


def main():
    if len(sys.argv) < 2:
        print("Usage: layer08_network_monitor.py {watch|status|test}")
        return
    cmd = sys.argv[1]
    nm = AdvancedNetworkMonitor()

    if cmd == "watch": nm.watch()
    elif cmd == "status": nm.status()
    elif cmd == "test": nm.test()


if __name__ == "__main__":
    main()
