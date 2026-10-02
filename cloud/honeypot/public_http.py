#!/usr/bin/env python3
"""VORIX Public Honeypot"""
import os, json, time, requests
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

API = os.getenv("API_URL", "http://vorix-api:8443")
KEY = os.getenv("API_KEY", "dev")

_geo = {}
def geoip(ip):
    if ip in _geo: return _geo[ip]
    if ip.startswith(("127.","10.","172.","192.168.")):
        r = {"country":"Local","city":"-","isp":"Local"}
    else:
        try:
            d = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,city,isp", timeout=3).json()
            r = d if d.get("status") == "success" else {}
        except: r = {}
    _geo[ip] = r
    return r

def send(ev):
    try:
        requests.post(f"{API}/api/v1/logs", json=ev,
                      headers={"X-API-Key": KEY}, timeout=5)
    except: pass

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def handle_all(self):
        ip = self.client_address[0]
        ua = self.headers.get("User-Agent", "?")
        path = self.path
        geo = geoip(ip)

        score = 40
        if any(x in path.lower() for x in ["admin","wp-",".env",".git","config"]):
            score += 30
        if any(x in ua.lower() for x in ["sqlmap","nikto","nmap","masscan"]):
            score += 30
        score = min(100, score)

        ev = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "agent_id": "public-honeypot",
            "severity": "CRITICAL" if score >= 70 else "WARN",
            "gate": "GATE01",
            "module": "PUBLIC_HONEYPOT",
            "event_type": "HTTP_HIT",
            "source_ip": ip,
            "country": geo.get("country", "?"),
            "message": f"{self.command} {path} from {ip}",
            "metadata": {"path": path, "ua": ua, "city": geo.get("city","?"), "score": score}
        }
        send(ev)

        self.send_response(200)
        self.send_header("Server", "nginx/1.18.0")
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><head><title>Welcome</title></head><body><h1>Server OK</h1></body></html>")

    do_GET = handle_all
    do_POST = handle_all
    do_HEAD = handle_all

if __name__ == "__main__":
    print("[*] Public Honeypot on :8080")
    HTTPServer(("0.0.0.0", 8080), H).serve_forever()
