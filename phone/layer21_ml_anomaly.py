#!/usr/bin/env python3
"""L21 — ML Anomaly Detection (Pure Python)"""
import os, sys, json, time, threading, math
from datetime import datetime, timedelta
from collections import defaultdict, deque

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "vorix-hybrid/phone")
STATE_FILE = os.path.join(BASE, "layer21_state.json")
BASELINE_FILE = os.path.join(BASE, "layer21_baseline.json")

try:
    import requests
    with open(os.path.join(HOME, "vorix/.tg-token")) as f:
        TG = f.read().strip()
except:
    TG = ""
CHAT = "175160049"

CONFIG = {
    "learning_days": 3,           # ۳ روز اول فقط یاد می‌گیره
    "baseline_window_hours": 24,   # baseline از ۲۴ ساعت
    "z_threshold": 3.0,            # z-score > 3 → anomaly
    "min_samples": 50,             # حداقل نمونه برای detection
    "check_interval": 300,         # هر ۵ دقیقه چک کن
}

class MLAnomaly:
    def __init__(self):
        self.baseline = self.load_baseline()
        self.history = defaultdict(lambda: deque(maxlen=10000))
        self.stats = {
            "total_events": 0,
            "anomalies": 0,
            "started": time.time(),
        }
        self.lock = threading.Lock()
        self.load_state()

    def load_baseline(self):
        try:
            with open(BASELINE_FILE) as f:
                return json.load(f)
        except:
            return {}

    def save_baseline(self):
        try:
            with open(BASELINE_FILE, "w") as f:
                json.dump(self.baseline, f, indent=2)
        except: pass

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

    # ─────────────────────────────────────────
    #   STATISTICS
    # ─────────────────────────────────────────
    def compute_baseline(self, values):
        """محاسبه mean و std"""
        n = len(values)
        if n < 2:
            return None
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / n
        std = math.sqrt(variance) if variance > 0 else 0
        return {"mean": mean, "std": std, "n": n}

    def z_score(self, value, baseline):
        """محاسبه z-score"""
        if not baseline:
            return 0
        if baseline["std"] == 0:
            # اگه مقدار با mean فرق داشت → anomaly قوی
            if value != baseline["mean"]:
                return 10.0
            return 0
        return abs(value - baseline["mean"]) / baseline["std"]

    # ─────────────────────────────────────────
    #   METRICS EXTRACTION
    # ─────────────────────────────────────────
    def extract_metrics(self, event):
        """استخراج ویژگی‌ها از event"""
        return {
            "msg_length": len(event.get("message", "")),
            "meta_count": len(event.get("metadata", {})),
            "severity_num": {"INFO": 1, "WARN": 2, "ERROR": 3, "CRITICAL": 4}.get(
                event.get("severity", "INFO"), 1),
        }

    # ─────────────────────────────────────────
    #   ANOMALY DETECTION
    # ─────────────────────────────────────────
    def check_event(self, event):
        """چک یک event"""
        with self.lock:
            self.stats["total_events"] += 1
            metrics = self.extract_metrics(event)
            now = time.time()

            anomalies = []
            for name, value in metrics.items():
                self.history[name].append((now, value))

                # baseline
                baseline = self.baseline.get(name)
                if not baseline or baseline.get("n", 0) < CONFIG["min_samples"]:
                    continue

                z = self.z_score(value, baseline)
                if z > CONFIG["z_threshold"]:
                    anomalies.append({
                        "metric": name,
                        "value": value,
                        "z_score": z,
                        "mean": baseline["mean"],
                        "std": baseline["std"],
                    })

            if anomalies:
                self.stats["anomalies"] += 1
                self._alert(event, anomalies)

            return anomalies

    def _alert(self, event, anomalies):
        if not TG: return
        try:
            lines = []
            for a in anomalies[:3]:
                lines.append(f"  • {a['metric']}: {a['value']:.0f} "
                            f"(mean: {a['mean']:.0f}, z: {a['z_score']:.1f})")
            
            msg = (
                f"🧠 *ML Anomaly Detected*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"⚠️ Event: `{event.get('event_type', '?')}`\n"
                f"📊 Severity: `{event.get('severity', '?')}`\n"
                f"🌐 IP: `{event.get('source_ip', '?')}`\n\n"
                f"🔍 Anomalies:\n" + "\n".join(lines) +
                f"\n\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            )
            requests.post(
                f"https://api.telegram.org/bot{TG}/sendMessage",
                json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
        except: pass

    # ─────────────────────────────────────────
    #   BASELINE LEARNING
    # ─────────────────────────────────────────
    def learn_baseline(self):
        """یادگیری از داده‌های فعلی"""
        print("🧠 Learning baseline...")
        updated = 0
        for metric, values in self.history.items():
            vals = [v for _, v in values]
            if len(vals) < CONFIG["min_samples"]:
                print(f"   ⚠️ {metric}: only {len(vals)} samples (need {CONFIG['min_samples']})")
                continue
            baseline = self.compute_baseline(vals)
            if baseline:
                self.baseline[metric] = baseline
                updated += 1
                print(f"   ✅ {metric}: mean={baseline['mean']:.1f}, std={baseline['std']:.1f}")
        self.save_baseline()
        print(f"\n📊 Baseline updated: {updated} metrics")

    # ─────────────────────────────────────────
    #   WATCHER
    # ─────────────────────────────────────────
    def watch(self):
        qfile = os.path.join(BASE, "queue.jsonl")
        last_pos = 0
        last_learn = 0

        print("🧠 L21 ML Anomaly Detection")
        print(f"📊 Z-threshold: {CONFIG['z_threshold']}")
        print(f"📊 Learning window: {CONFIG['learning_days']} days")
        print()

        while True:
            try:
                if not os.path.exists(qfile):
                    time.sleep(2); continue
                size = os.path.getsize(qfile)
                if size < last_pos: last_pos = 0
                if size == last_pos:
                    time.sleep(2); continue

                with open(qfile) as f:
                    f.seek(last_pos)
                    lines = f.readlines()
                    last_pos = f.tell()

                for line in lines:
                    line = line.strip()
                    if not line: continue
                    try:
                        e = json.loads(line)
                        anomalies = self.check_event(e)
                        if anomalies:
                            print(f"🧠 Anomaly: {len(anomalies)} metrics")
                    except: pass

                # یادگیری هر ۱ ساعت
                if time.time() - last_learn > 3600:
                    self.learn_baseline()
                    last_learn = time.time()

                self.save_state()
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"⚠️ {e}")
                time.sleep(10)

    def status(self):
        uptime = int(time.time() - self.stats["started"])
        h, m = divmod(uptime // 60, 60)
        print(f"\n🧠 L21 ML Anomaly Status")
        print(f"═══════════════════════════════")
        print(f"Uptime:        {h}h {m}m")
        print(f"Total events:  {self.stats['total_events']}")
        print(f"Anomalies:     {self.stats['anomalies']}")
        print()
        print(f"📊 Baseline:")
        if self.baseline:
            for name, b in self.baseline.items():
                print(f"   {name}: mean={b['mean']:.1f}, std={b['std']:.1f} (n={b['n']})")
        else:
            print("   (not learned yet)")

    def test(self):
        """تست با داده جعلی"""
        # پاک کردن baseline قدیمی
        self.baseline = {}
        self.history = defaultdict(lambda: deque(maxlen=10000))
        print("🧪 Testing ML Anomaly\n")

        # مقدار عادی برای یادگیری (متنوع)
        print("📍 Feeding 100 normal events (varied)...")
        import random
        for i in range(100):
            self.check_event({
                "message": "normal event " + "x" * random.randint(5, 20),
                "severity": random.choice(["INFO", "INFO", "INFO", "WARN"]),
                "metadata": {"a": "b"} if random.random() < 0.7 else {"a": "b", "c": "d"},
                "event_type": "TEST",
                "source_ip": "1.2.3.4",
            })

        # یادگیری
        print()
        self.learn_baseline()

        # حالا anomaly بفرست
        print("\n📍 Sending anomalous event...")
        anomalies = self.check_event({
            "message": "X" * 500,  # طولانی غیرعادی
            "severity": "CRITICAL",
            "metadata": {"a": "b", "c": "d", "e": "f", "g": "h", "i": "j"},
            "event_type": "TEST_ANOMALY",
            "source_ip": "1.2.3.4",
        })

        print(f"\n✅ Detected {len(anomalies)} anomalies")
        print()
        self.status()

def main():
    if len(sys.argv) < 2:
        print("Usage: layer21_ml_anomaly.py {watch|status|test|learn}")
        return
    cmd = sys.argv[1]
    ml = MLAnomaly()

    if cmd == "watch": ml.watch()
    elif cmd == "status": ml.status()
    elif cmd == "test": ml.test()
    elif cmd == "learn": ml.learn_baseline()

if __name__ == "__main__":
    main()
