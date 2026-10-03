#!/usr/bin/env python3
"""VORIX — دیتای واقعی حملات جهانی از APIهای عمومی"""
import json, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

OUT = Path.home() / "vorix-hybrid/docs/data/global_attacks.json"
TIMEOUT = 10

def fetch(url, headers=None):
    try:
        req = urllib.request.Request(url, headers=headers or {"User-Agent": "VORIX/1.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}

# ─── ۱. SANS ISC DShield — Top attack sources ─────────────
def dshield_top():
    data = fetch("https://isc.sans.edu/api/topips/records/100?json")
    if isinstance(data, list):
        return [{
            "ip": d.get("ip"),
            "attacks": int(d.get("count", 0)),
            "firstseen": d.get("firstseen", ""),
            "lastseen": d.get("lastseen", ""),
        } for d in data]
    return []

# ─── ۲. DShield کشور به کشور ─────────────────────────────
def dshield_countries():
    """آمار حملات بر اساس کشور"""
    out = {}
    # Top 20 countries
    for cc in ["CN","RU","US","IR","TR","BR","IN","VN","KR","ID",
               "UA","DE","FR","GB","NL","PL","IT","TH","PK","TW"]:
        d = fetch(f"https://isc.sans.edu/api/sources/{cc}/records/10?json")
        if isinstance(d, list):
            out[cc] = sum(int(x.get("count", 0)) for x in d)
    return out

# ─── ۳. حملات به ایران (targeted) ────────────────────────
def attacks_on_iran():
    """حملاتی که IP مبداشون از DShield می‌دونیم — فیلترهای ایران"""
    # DShield IP رو با info enrichment می‌گیریم
    data = fetch("https://isc.sans.edu/api/topips/records/100?json")
    hits = []
    if isinstance(data, list):
        for d in data[:50]:
            ip = d.get("ip")
            if not ip: continue
            info = fetch(f"https://isc.sans.edu/api/ip/{ip}?json")
            if isinstance(info, dict) and "ip" in info:
                hits.append({
                    "ip": ip,
                    "attacks": int(d.get("count", 0)),
                    "country": info.get("ascountry", "??"),
                    "as": info.get("as", "?"),
                    "asname": info.get("asname", "?"),
                })
    return hits

# ─── ۴. ThreatFox recent IOCs ─────────────────────────────
def threatfox_recent():
    data = fetch("https://threatfox-api.abuse.ch/api/v1/", 
                 headers={"User-Agent": "VORIX/1.0"})
    # POST required — use GET fallback
    try:
        import urllib.request as ur
        body = json.dumps({"query": "get_iocs", "days": 1}).encode()
        req = ur.Request("https://threatfox-api.abuse.ch/api/v1/", 
                        data=body, headers={
                            "Content-Type": "application/json",
                            "User-Agent": "VORIX/1.0"
                        })
        with ur.urlopen(req, timeout=TIMEOUT) as r:
            data = json.loads(r.read().decode())
            if data.get("query_status") == "ok":
                return [{
                    "ioc": x.get("ioc"),
                    "type": x.get("ioc_type"),
                    "malware": x.get("malware_printable", "?"),
                    "threat": x.get("threat_type", "?"),
                    "confidence": x.get("confidence_level", 0),
                } for x in (data.get("data") or [])[:30]]
    except Exception as e:
        return []
    return []

# ─── ۵. URLhaus recent ────────────────────────────────────
def urlhaus_recent():
    try:
        import urllib.request as ur
        body = urllib.parse.urlencode({"limit": 20}).encode()
        req = ur.Request("https://urlhaus-api.abuse.ch/v1/urls/recent/",
                        data=body, headers={"User-Agent": "VORIX/1.0"})
        with ur.urlopen(req, timeout=TIMEOUT) as r:
            data = json.loads(r.read().decode())
            return [{
                "url": x.get("url", "")[:80],
                "threat": x.get("threat", "?"),
                "country": x.get("urlhaus_reference", ""),
            } for x in (data.get("urls") or [])[:20]]
    except Exception:
        return []

# ─── اجرا با thread ───────────────────────────────────────
def main():
    print("🌐 Fetching live data from public APIs...")
    
    results = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {
            ex.submit(dshield_top): "top_ips",
            ex.submit(dshield_countries): "countries",
            ex.submit(threatfox_recent): "threatfox",
            ex.submit(urlhaus_recent): "urlhaus",
        }
        for f in as_completed(futs):
            name = futs[f]
            try:
                results[name] = f.result()
                print(f"  ✅ {name}: {len(results[name]) if isinstance(results[name], (list, dict)) else 0}")
            except Exception as e:
                results[name] = []
                print(f"  ❌ {name}: {e}")
    
    # آمار نهایی
    top_ips = results.get("top_ips") or []
    countries = results.get("countries") or {}
    threatfox = results.get("threatfox") or []
    urlhaus = results.get("urlhaus") or []
    
    output = {
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "DShield + ThreatFox + URLhaus",
        "top_ips": top_ips[:20],
        "countries": countries,
        "threatfox": threatfox,
        "urlhaus": urlhaus,
        "stats": {
            "total_sources": len(top_ips),
            "total_countries": len(countries),
            "total_iocs": len(threatfox),
            "total_urls": len(urlhaus),
            "global_attacks_24h": sum(countries.values()) if countries else 0,
        }
    }
    
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(output, f, indent=1, ensure_ascii=False)
    
    print(f"\n✅ saved: {OUT}")
    print(f"   top_ips: {len(top_ips)}")
    print(f"   countries: {list(countries.keys())}")
    print(f"   threatfox iocs: {len(threatfox)}")
    print(f"   urlhaus: {len(urlhaus)}")

if __name__ == "__main__":
    main()
