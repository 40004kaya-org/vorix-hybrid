#!/usr/bin/env python3
"""تولید داده چارت‌ها برای هر بخش"""
import os, json, subprocess
from datetime import datetime, timedelta
from collections import defaultdict

BASE = os.path.expanduser("~/vorix-hybrid")
PHONE = os.path.join(BASE, "phone")
DATA = os.path.join(BASE, "docs", "data")
os.makedirs(DATA, exist_ok=True)

SECTIONS = {
    "overview": ["layer01_selfdefense","layer02_threat_intel","layer03_behavioral",
                 "layer04_auto_block","layer05_data_quarantine","layer06_geoip_block",
                 "layer07_network_behavior","layer08_network_monitor","layer09_rate_limiter",
                 "layer10_red_alert","layer11_dns_sinkhole","layer12_reverse_dns",
                 "layer13_ua_filter","layer15_fingerprint","layer16_killswitch",
                 "layer17_watchdog","layer18_backup_verifier","layer19_password_leak",
                 "layer21_ml_anomaly","layer22_header_analysis","layer23_cookie_anomaly",
                 "layer24_session_hijack","layer25_ssl_monitor","layer26_hsts",
                 "layer29_30_identity","layer31_log_encryption","layer_fim",
                 "layer_rootkit","layer_multichannel","layer_livefeed",
                 "layer_mitre","layer_response","layer_scoring","layer_reports",
                 "layer_forensics","layer_hashchain","layer_mocker","layer_voice"],
    "ingress": ["layer02_threat_intel","layer06_geoip_block","layer09_rate_limiter",
                "layer13_ua_filter","layer15_fingerprint"],
    "intelligence": ["layer03_behavioral","layer21_ml_anomaly","layer_mitre"],
    "response": ["layer04_auto_block","layer10_red_alert","layer_response",
                 "layer_scoring","layer_forensics"],
    "data": ["layer05_data_quarantine","layer31_log_encryption"],
    "output": ["layer_multichannel","layer_livefeed","layer_reports"],
}

def read_events():
    events = []
    for fname in ["hash_chain.jsonl", "playbooks.jsonl", "layer10_events.jsonl"]:
        path = os.path.join(PHONE, fname)
        if os.path.exists(path):
            try:
                for line in open(path).readlines()[-500:]:
                    try: events.append(json.loads(line))
                    except: pass
            except: pass
    return events

def get_metrics(layers):
    pids = []
    for l in layers:
        try:
            r = subprocess.run(["pgrep", "-f", f"python.*{l}"],
                             capture_output=True, text=True, timeout=2)
            for p in r.stdout.strip().split("\n"):
                if p: pids.append(p)
        except: pass
    return {"pids": pids, "count": len(pids)}

def line_chart(events):
    points = []
    now = datetime.utcnow()
    for i in range(24, 0, -1):
        h = now - timedelta(hours=i)
        cnt = sum(1 for e in events if e.get("ts","").startswith(h.strftime("%Y-%m-%dT%H")))
        points.append({"h": h.strftime("%H"), "c": cnt})
    return {"title":"Events 24h", "points": points}

def bar_chart(events):
    b = defaultdict(int)
    for e in events:
        ts = e.get("ts","")
        if len(ts) >= 13:
            b[ts[11:13]] += 1
    labels = [f"{h:02d}" for h in range(24)]
    data = [b.get(h, 0) for h in labels]
    return {"title":"Hourly", "labels": labels, "data": data}

def donut_chart(events):
    t = defaultdict(int)
    for e in events:
        k = e.get("event_type") or e.get("attack") or e.get("event") or "other"
        t[k] += 1
    top = sorted(t.items(), key=lambda x:-x[1])[:6]
    return {"title":"Types", "labels":[x[0] for x in top], "data":[x[1] for x in top]}

def gauge(section, layers):
    m = get_metrics(layers)
    cpu, ram = 0, 0
    for pid in m["pids"]:
        try:
            r = subprocess.run(["ps","-o","pcpu,rss","-p",pid],
                             capture_output=True, text=True, timeout=2)
            lines = r.stdout.strip().split("\n")[1:]
            if lines:
                p = lines[0].split()
                cpu += float(p[0])
                ram += int(p[1])/1024
        except: pass
    return {"title":"Resources", "cpu": round(cpu,1), "ram": round(ram,1), "procs": m["count"]}

def heatmap(events):
    grid = [[0]*24 for _ in range(7)]
    now = datetime.utcnow()
    for e in events:
        ts = e.get("ts","")
        if len(ts) >= 13:
            try:
                dt = datetime.fromisoformat(ts.replace("Z","").split("+")[0])
                d = (now - dt).days
                if 0 <= d < 7:
                    grid[6-d][dt.hour] += 1
            except: pass
    return {"title":"Heatmap", "grid": grid}

def radar(section, layers):
    m = get_metrics(layers)
    return {"title":"Radar",
            "axes":["CPU","RAM","Net","Disk","Err","Proc"],
            "values":[50, 60, 20, 15, 10, min(100, m["count"]*10)]}

def sparklines(layers):
    import random
    return {"title":"Sparklines",
            "items":[{"name":l.replace("layer_","L-")[:12],
                     "data":[random.randint(10,80) for _ in range(20)]}
                    for l in layers[:10]]}

def timeline(events):
    recent = sorted(events, key=lambda x: x.get("ts",""), reverse=True)[:20]
    return {"title":"Timeline",
            "items":[{"ts": e.get("ts","")[11:19],
                     "sev": str(e.get("severity","INFO")).upper(),
                     "msg": (e.get("event_type") or e.get("attack") or e.get("message",""))[:40]}
                    for e in recent]}

def build(section, layers, events):
    return {
        "section": section,
        "ts": datetime.utcnow().isoformat()+"Z",
        "layers": layers,
        "charts": {
            "line": line_chart(events),
            "bar": bar_chart(events),
            "donut": donut_chart(events),
            "gauge": gauge(section, layers),
            "heatmap": heatmap(events),
            "radar": radar(section, layers),
            "sparklines": sparklines(layers),
            "timeline": timeline(events),
        }
    }

def main():
    events = read_events()
    print(f"Events loaded: {len(events)}")
    for section, layers in SECTIONS.items():
        data = build(section, layers, events)
        with open(os.path.join(DATA, f"{section}.json"), "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"OK - {section}.json")
    print("Done!")

if __name__ == "__main__":
    main()
