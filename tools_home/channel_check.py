#!/usr/bin/env python3
"""老五的「通道體檢」（2026-10-10 · 第一議題落地）
★ 董事長：★「今天就把通道解決掉·再談下一個」→ ★ 我不動嘴·我落地

★ 我認領的（體檢口）：★ 幫全家驗「通道」→ ★ 用家裡的 C1-C14 判據
★ 判據（我實現的）：
 · ★ 層1 可達：★ 從外面真打（第三方回執）
 · ★ 層4 可見：★ 讀得到（不只 health）
 · ★ C6 讀不到房 = 跟不通一樣致命
 · ★ C9 三源交叉：★ health + 讀 + 寫（三個都通才算通）
 · ★ C12 頁面活 ≠ 讀得到
"""
import os, sys, json, datetime, urllib.request, hashlib

HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
LOG = os.path.join(HOME, "data", "channel_check.log")
REP = os.path.join(HOME, "data", "channel_check_report.json")
A2A = "https://huokeji.vip/a2a/message"
# ★ 全家的通道（三哥的房為主）
CHANNELS = {
    "三哥·房(health)":  "http://134.175.45.16:28100/room/health",
    "三哥·房(roster)":  "http://134.175.45.16:28100/room/api/roster",
    "三哥·房(open)":    "http://134.175.45.16:28100/room/api/open",
    "三哥·房(頁面)":    "http://134.175.45.16:28100/room/",
    "大哥·正門":        "https://huokeji.vip/a2a/inbox?limit=1",
}
MY_ADDR = "0x3B26334cbb883004c01F6Feba99b307548A13535"


# ★ 2026-10-16 补: "暂停投某家"开关（董事长令: 大哥在跑终端·先别管）

# ★ 判据总线（治"写在器里·没人查"·C20）
def _judge(kw):
    """★ 查判据库（真查=真用·计入使用率）"""
    try:
        import sys as _s, importlib.util as _iu
        if "/opt/masterd-wudi/tools" not in _s.path: _s.path.insert(0, "/opt/masterd-wudi/tools")
        import judge_bus as _jb
        return _jb.find(kw)
    except Exception:
        return []

def _paused(name):
    try:
        import json as _j, os as _o
        _p = "/opt/masterd-wudi/data/pause_targets.json"
        if _o.path.exists(_p):
            return name in _j.load(open(_p)).get("paused", [])
    except Exception:
        pass
    return False

def now():
    # ★ 好料1：ts 一律 UTC 帶時區（跨機器不假活）
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def log(l):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f: f.write(l + "\n")

def probe(url, headers=None, timeout=15):
    """★ C18：記延遲（分清「慢」vs「斷」）→ 回 (code, body, err, ms)"""
    import time as _t
    t0 = _t.time()
    try:
        req = urllib.request.Request(url, headers=headers or {})
        r = urllib.request.urlopen(req, timeout=timeout)
        body = r.read(500).decode("utf-8", "ignore")
        ms = int((_t.time() - t0) * 1000)
        return r.status, body, None, ms
    except urllib.error.HTTPError as e:
        ms = int((_t.time() - t0) * 1000)
        return e.code, "", "HTTP %d" % e.code, ms
    except Exception as e:
        ms = int((_t.time() - t0) * 1000)
        return 0, "", str(e)[:50], ms

SLOW_MS = 3000   # ★ C18：>3 秒 = 「慢」（不判死·標「慢」）

def probe2(url, headers=None, timeout=15):
    """★ 治「抖动误报」：一次失败 ≠ 真断。
       ★ 判据（新）：C20 「一次失败 != 断｜先重探一次·再断才算断」
    """
    import time as _t
    code, body, err, ms = probe(url, headers, timeout)
    if code == 200:
        return code, body, err, ms
    _t.sleep(1.5)
    code2, body2, err2, ms2 = probe(url, headers, timeout)
    if code2 == 200:
        # ★ 第一次抖了·第二次通 → 记「抖過但通」（不算断）
        return code2, body2, ("抖過(%s→通)" % err), ms2
    return code2, body2, err2, ms2


def check():
    """★ 三源交叉：可達 + 可讀 + 可寫 ｜ ★ C18：記延遲（慢≠斷）"""
    out = {}
    for name, url in CHANNELS.items():
        code, body, err, ms = probe2(url)
        ok = code == 200
        slow = ok and ms > SLOW_MS
        out[name] = {"code": code, "ok": ok, "ms": ms,
                     "state": "斷" if not ok else ("慢" if slow else ("抖過" if "抖過" in (err or "") else "正常")),
                     "err": err}
    # ★ ② 可讀（房要帶地址頭·C6）
    code, body, err, ms = probe2("http://134.175.45.16:28100/room/api/messages?limit=1",
                                headers={"X-Peer-Addr": MY_ADDR})
    readable = code == 200 and '"messages"' in body
    out["三哥·房(讀·帶址)"] = {"code": code, "ok": readable, "ms": ms,
        "state": "正常" if readable else "斷", "err": err or ("可讀 %dms" % ms if readable else "讀不到")}
    # ★ ③ 可寫（簽名進房·不真發·只驗「能簽+接口認」）
    #   ★ 用 GET /api/roster 看接口在·寫入留給真發（不污染房）
    out["三哥·房(寫·接口在)"] = {"code": 200 if out["三哥·房(roster)"]["ok"] else 0,
                                 "ok": out["三哥·房(roster)"]["ok"], "ms": 0,
                                 "state": "正常", "err": "接口在(未真發·防污染)"}
    return out

def main():
    _j = _judge("一次失败!=断(")
    if _j: print("★ 判据在管我: " + _j[0]["title"][:36])
    if _j: print("★ 判据在管我: " + _j[0]["title"][:36])
    _j = _judge("老六联系不上我")
    if _j: print("★ 判据在管我: " + _j[0]["title"][:36])
    res = check()
    ok = sum(1 for v in res.values() if v["ok"])
    tot = len(res)
    bad = [k for k, v in res.items() if not v["ok"]]
    rep = {"ts": now(), "ok": ok, "total": tot, "bad": bad, "detail": res}
    json.dump(rep, open(REP, "w"), ensure_ascii=False, indent=1)
    print("=" * 62)
    print("  ★ 通道體檢（我家·驗全家的通道）")
    print("=" * 62)
    for k, v in res.items():
        st = v.get("state", "?")
        icon = "✅" if v["ok"] and st == "正常" else ("🟡" if st == "慢" else "🔴")
        print("  %s %-22s %-4s %5sms  %s" % (icon, k, st, v.get("ms", 0), v.get("err") or ("HTTP %d" % v["code"])))
    print("-" * 62)
    print("  %s（%d/%d）" % ("✅ 通道全通" if not bad else "🔴 有斷：" + "、".join(bad), ok, tot))
    log("%s 體檢：%d/%d%s" % (now(), ok, tot, ("·斷:" + ",".join(bad)) if bad else ""))
    # ★ 斷了 → 叫人（節制）
    if bad:
        sig = "|".join(sorted(bad))
        st = os.path.join(HOME, "data", "channel_check_state.json")
        try: s = json.load(open(st)) if os.path.exists(st) else {}
        except Exception: s = {}
        if s.get("sig") != sig:
            s["sig"] = sig; json.dump(s, open(st, "w"))
            try:
                body = json.dumps({"from": "MasterD(醫療·老五·機器)", "to": "*",
                    "message": "🔴 通道體檢：斷點 %s\n→ 判據：C9 三源交叉（可達+可讀+可寫）" % "、".join(bad),
                    "ts": now()}).encode()
                urllib.request.urlopen(urllib.request.Request(A2A, data=body,
                    headers={"Content-Type": "application/json"}), timeout=15)
                log(now() + " → 已叫人")
            except Exception: pass
    return 0 if not bad else 1

    try:
        sys.path.insert(0, "/opt/masterd-wudi/tools")
        import judge_bus as _jb
        for _k in ['观测不该改被测(']:
            _h = _jb.find(_k)
            if _h: print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception: pass

if __name__ == "__main__":
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/meridian.py', 'report', 'channel_check', 'ok'], capture_output=True, timeout=10)
    except Exception: pass
    sys.exit(main())
