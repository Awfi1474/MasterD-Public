#!/usr/bin/env python3
"""老五 「家来叫我」—— 服务器侧扫描（照三哥·治"天天跑终端"）
家（服务器·不会死）每5分钟扫：①我沙箱的门在不在 ②坐标变了没 ③发现就记录
判据: 叫人的角色给"不会死的那方"（服务器）·不是"会死的沙箱钩子"
"""
import json, os, subprocess, urllib.request
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
LEDGER = "/opt/masterd-wudi/data/home_calls_ledger.jsonl"
MY_DOOR = "https://e3f21a94.strike-agent.com/health?from=laowu"   # 我的固定名（平台域名）
MY_HOME = "http://43.129.23.87:28430/health?from=laowu-self"
SANDBOX_IPS = ["172.22.53.33"]   # 我上次的沙箱内网（会变·只作参考）

def scan():
    rec = {"ts": datetime.now(CST).isoformat(timespec="seconds"), "by": "家(服务器·不会死)"}
    # ① 我的门在不在（公网名）
    try:
        _req = urllib.request.Request(MY_DOOR, headers={"User-Agent": "Mozilla/5.0 (laowu-homecalls)"})
        r = urllib.request.urlopen(_req, timeout=8)
        _body = r.read().decode("utf-8", "ignore")
        # ★ 判定: 200 且含 who = 门"真活着"；200但空 = 可疑
        if r.getcode() == 200 and "who" in _body:
            rec["door"] = "ALIVE"
            rec["door_who"] = _body[:60]
        else:
            rec["door"] = "SUSPECT(%s)" % r.getcode()
    except urllib.error.HTTPError as e:
        # ★ 404/403/503 = 门"不在"(进程死了/沙箱重启) —— 这是有效监测
        rec["door"] = "DEAD(HTTP %s)" % e.code
    except Exception as e:
        rec["door"] = "DEAD(%s)" % str(e)[:24]
    # ② 家自己活不活
    try:
        _rq = urllib.request.Request(MY_HOME, headers={"User-Agent": "Mozilla/5.0 (laowu-homecalls)"})
        r = urllib.request.urlopen(_rq, timeout=6)
        d = json.loads(r.read().decode())
        rec["home"] = "200"
        rec["home_who"] = d.get("who", "?")
    except Exception as e:
        rec["home"] = "err:%s" % str(e)[:30]
    # ③ 沙箱在不在（内网·同集群才有意义·服务器跨集群不通→记为参考）
    rec["sandbox_hint"] = SANDBOX_IPS
    # ④ 落台账（只在"有变化"时记·不刷屏）
    last = None
    if os.path.exists(LEDGER):
        lines = open(LEDGER).read().splitlines()
        if lines:
            try:
                last = json.loads(lines[-1])
            except Exception:
                pass
    changed = (not last) or (last.get("door") != rec["door"]) or (last.get("home") != rec["home"])
    if changed:
        with open(LEDGER, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print("  [变化] door=%s home=%s → 记台账" % (rec["door"], rec["home"]), flush=True)
    else:
        print("  [无变化] door=%s home=%s → 不记(防刷屏)" % (rec["door"], rec["home"]), flush=True)
    return rec

if __name__ == "__main__":
    scan()
