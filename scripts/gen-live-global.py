#!/usr/bin/env python3
"""VORIX — حملات زنده جهانی از DShield"""
import json, urllib.request, ssl
from pathlib import Path
from datetime import datetime, timezone

OUT = Path.home() / "vorix-hybrid/docs/data/live_global.json"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
HEADERS = {"User-Agent": "Mozilla/5.0 VORIX/1.0"}

def get_json(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_err": str(e)}

def post_json(url, payload, timeout=15):
    try:
        body = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=body, headers={
            "Content-Type": "application/json", "User-Agent": "VORIX/1.0"
        })
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_err": str(e)}

def fetch_top_ips():
    d = get_json("https://isc.sans.edu/api/topips/records/100?json")
    return d if isinstance(d, list) else []

def batch_geo(ips):
    if not ips: return {}
    d = post_json("http://ip-api.com/batch?fields=query,countryCode,country,as,isp", ips)
    if isinstance(d, list):
        return {x.get("query"): x for x in d}
    return {}

def fetch_feodo():
    d = get_json("https://feodotracker.abuse.ch/downloads/ipblocklist.json")
    if isinstance(d, list):
        return [{
            "ip": x.get("ip_address"), "port": x.get("port"),
            "malware": x.get("malware", "?"),
            "country": (x.get("country") or "??")[:2],
        } for x in d[:40]]
    return []

def main():
    print("🌐 Fetching...")
    top = fetch_top_ips()
    print(f"   DShield top: {len(top)}")

    if not top:
        print("❌ no top IPs"); return

    # فیلد واقعی: "source" نه "ip"
    ips = [r.get("source") for r in top[:50] if r.get("source")]
    print(f"   geo lookup for {len(ips)} IPs...")

    geo = batch_geo(ips)
    print(f"   got geo for {len(geo)} IPs")

    enriched = []
    for r in top[:50]:
        ip = r.get("source")
        if not ip: continue
        g = geo.get(ip, {})
        # "reports" نه "count"
        cnt = int(r.get("reports", 0) or 0)
        enriched.append({
            "ip": ip,
            "rank": r.get("rank", 0),
            "count": cnt,
            "targets": r.get("targets", 0),
            "country": g.get("countryCode", "??"),
            "country_name": g.get("country", ""),
            "isp": (g.get("isp") or "")[:40],
            "asn": (g.get("as") or "").split()[0] if g.get("as") else "",
        })

    countries = {}
    for e in enriched:
        c = e["country"]
        if c == "??": continue
        countries[c] = countries.get(c, 0) + e["count"]

    fe = fetch_feodo()
    print(f"   Feodo C2: {len(fe)}")

    output = {
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "SANS DShield + ip-api + Feodo",
        "attacks": enriched,
        "countries": dict(sorted(countries.items(), key=lambda x: -x[1])),
        "feodo": fe,
        "stats": {
            "total_attacks": sum(e["count"] for e in enriched),
            "unique_ips": len(enriched),
            "unique_countries": len(countries),
            "c2_count": len(fe),
        }
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(output, f, indent=1, ensure_ascii=False)

    print(f"\n✅ {OUT}")
    print(f"   attacks: {output['stats']['total_attacks']:,}")
    print(f"   countries: {list(countries.keys())[:10]}")
    print(f"\n   مثال:")
    for e in enriched[:3]:
        print(f"   {e['ip']:18} {e['country']:3} {e['count']:>10,}  {e['isp'][:25]}")

main()
