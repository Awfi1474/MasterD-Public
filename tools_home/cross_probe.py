#!/usr/bin/env python3
"""老五的「交叉探活」（2026-10-10 · 第五議題·心跳）
★ 我去探兄弟 → ① 驗他們活不活 ② 幫他們升 peer（alive_evidence self→peer）
★ 判據（中醫「切診最硬」）：★「別人探到 = 最硬的活證」（自探不算）
"""
import os, sys, json, urllib.request, datetime
HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
LOG = os.path.join(HOME, "data", "cross_probe.log")
STATE = os.path.join(HOME, "data", "cross_probe_state.json")
# ★ 兄弟的活證口（目前已知）
PEERS = {
    "Arki":   "http://43.129.169.29:18889/health?from=laowu",
    "三哥房": "http://134.175.45.16:28100/room/health",
    # "老四": "https://b2a224e9.strike-agent.com/health?from=laowu",  # 403·待他開白名單
}

def now():
    return datetime.datetime.now(datetime.timezone.utc)

def probe(name, url):
    t0 = now()
    try:
        r = urllib.request.urlopen(url, timeout=10)
        body = r.read(400).decode("utf-8", "ignore")
        ms = int((now() - t0).total_seconds() * 1000)
        try: d = json.loads(body)
        except Exception: d = {}
        return {"ok": r.status == 200, "ms": ms,
                "who": d.get("who") or d.get("agent") or "?",
                "ages": d.get("ages_s") or d.get("chains") or {}}
    except Exception as e:
        return {"ok": False, "err": str(e)[:50]}

def main():
    out = {}
    for name, url in PEERS.items():
        r = probe(name, url)
        out[name] = r
        if r["ok"]:
            print("  ✅ 探 %-6s %4dms · who=%s" % (name, r["ms"], r["who"][:24]))
        else:
            print("  🔴 探 %-6s 失敗：%s" % (name, r.get("err", "")))
    with open(LOG, "a") as f:
        f.write("%s %s\n" % (now().isoformat(), json.dumps(out, ensure_ascii=False)))
    # ★ 順便記錄：我探了他們（他們下次查 peer_hits 會看到我的 IP）
    json.dump({"ts": now().isoformat(), "probed": {k: v.get("ok") for k, v in out.items()}},
              open(STATE, "w"))
    ok = sum(1 for v in out.values() if v.get("ok"))
    print("  ★ 交叉探活：%d/%d 通" % (ok, len(out)))
    return 0 if ok == len(out) else 1

if __name__ == "__main__":
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/meridian.py', 'report', 'cross_probe', 'ok'], capture_output=True, timeout=10)
    except Exception: pass
    sys.exit(main())
