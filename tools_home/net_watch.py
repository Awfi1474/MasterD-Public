import datetime
#!/usr/bin/env python3
"""老五的「網速監測」（2026-10-10 · 第二議題：網速/延遲）
★ 董事長：★「幾部手機+共用WiFi·延遲避免不了」→ ★ 不是要快·是要「慢也知道」
★ C18：★ 慢 ≠ 斷 → ★ 記延遲趨勢（P50/P99/抖動）·不判死
★ 判據：★「慢要留數字·斷才叫人」
"""
import os, sys, json, time, urllib.request, datetime
HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
LOG = os.path.join(HOME, "data", "net_watch.log")
HIST = os.path.join(HOME, "data", "net_history.json")
TARGETS = {
    "三哥房": "http://134.175.45.16:28100/room/health",
    "大哥正門": "https://huokeji.vip/a2a/inbox?limit=1",
}
N = 7   # ★ 每次 7 次採樣

def one(url):
    t0 = time.time()
    try:
        r = urllib.request.urlopen(url, timeout=12)
        r.read(200)
        return int((time.time() - t0) * 1000)
    except Exception:
        return -1

def pct(xs, p):
    xs = sorted(x for x in xs if x >= 0)
    if not xs: return None
    return xs[min(int(len(xs) * p / 100), len(xs) - 1)]

def main():
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    hist = {}
    if os.path.exists(HIST):
        try: hist = json.load(open(HIST))
        except Exception: hist = {}
    out = {}
    for name, url in TARGETS.items():
        s = [one(url) for _ in range(N)]
        ok = [x for x in s if x >= 0]
        lost = N - len(ok)
        st = {
            "ts": now, "n": N, "ok": len(ok), "loss_pct": round(100 * lost / N),
            "p50": pct(s, 50), "p99": pct(s, 99),
            "jitter": (max(ok) - min(ok)) if ok else None,
            "state": "斷" if len(ok) == 0 else ("慢" if pct(s, 50) and pct(s, 50) > 3000 else "正常"),
        }
        out[name] = st
        hist.setdefault(name, []).append(st)
        hist[name] = hist[name][-200:]   # ★ 留最近 200 次
        print("  %-10s %-4s P50=%-6s P99=%-6s 抖動=%-6s 丟包=%d%%" % (
            name, st["state"], st["p50"], st["p99"], st["jitter"], st["loss_pct"]))
    json.dump(hist, open(HIST, "w"), ensure_ascii=False, indent=1)
    with open(LOG, "a") as f:
        f.write("%s %s\n" % (now, json.dumps(out, ensure_ascii=False)))
    return 0

if __name__ == "__main__":
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/meridian.py', 'report', 'net_watch', 'ok'], capture_output=True, timeout=10)
    except Exception: pass
    sys.exit(main())
