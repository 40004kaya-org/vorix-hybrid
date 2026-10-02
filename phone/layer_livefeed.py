#!/usr/bin/env python3
"""L-LiveFeed — پوش زنده رویدادها به تلگرام"""
import os, json, time, requests

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
TOKEN_FILE = os.path.join(HOME, "vorix/.tg-token")
CHAT_ID = "175160049"
STATE_FILE = os.path.join(BASE, "livefeed_state.json")

WATCH = [
    "hash_chain.jsonl",
    "playbooks.jsonl",
    "layer10_events.jsonl",
    "killswitch_events.jsonl",
    "queue.jsonl",
]

def load_token():
    if os.path.exists(TOKEN_FILE):
        return open(TOKEN_FILE).read().strip()
    return ""

TOKEN = load_token()
API = "https://api.telegram.org/bot" + TOKEN

def send(text):
    try:
        r = requests.post(API + "/sendMessage", json={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print("SEND ERR: " + str(e))
        return False

def load_state():
    try: return json.load(open(STATE_FILE))
    except: return {}

def save_state(s):
    try: json.dump(s, open(STATE_FILE, "w"))
    except: pass

def init_offsets():
    offs = {}
    for f in WATCH:
        p = os.path.join(BASE, f)
        offs[f] = os.path.getsize(p) if os.path.exists(p) else 0
    return offs

def fmt(fname, ev):
    ts = str(ev.get("ts", ev.get("timestamp", "")))[:19]
    sev = str(ev.get("severity", ev.get("level", "INFO"))).upper()
    evt = ev.get("event", ev.get("event_type", ev.get("type", "?")))
    msg = ev.get("message", ev.get("msg", ""))

    icons = {"CRITICAL":"!!!", "ERROR":"!!", "WARN":"!", "WARNING":"!", "INFO":"i"}
    icon = icons.get(sev, "-")

    txt = "[" + icon + "] <b>" + str(evt) + "</b>\n"
    if ts: txt += "T " + ts + "\n"
    if msg: txt += str(msg)[:200] + "\n"
    txt += "F " + fname
    return txt

def main():
    if not TOKEN:
        print("ERROR: token not found"); return

    print("LiveFeed starting...")
    # (start message removed)
    print("watching " + str(len(WATCH)) + " files")

    offs = init_offsets()
    save_state(offs)

    while True:
        try:
            for f in WATCH:
                p = os.path.join(BASE, f)
                if not os.path.exists(p): continue
                size = os.path.getsize(p)
                last = offs.get(f, size)
                if size < last: last = 0
                if size == last: continue

                with open(p) as fh:
                    fh.seek(last)
                    lines = fh.readlines()
                    offs[f] = fh.tell()

                for line in lines:
                    line = line.strip()
                    if not line: continue
                    try:
                        ev = json.loads(line)
                        send(fmt(f, ev))
                    except: pass
                save_state(offs)
            time.sleep(0.2)
        except KeyboardInterrupt:
            print("Bye"); break
        except Exception as e:
            print("ERR: " + str(e)); time.sleep(5)

if __name__ == "__main__":
    main()
