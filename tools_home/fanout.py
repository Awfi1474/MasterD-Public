#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·并行派发器 v2（走 HUB 一次投·让 HUB 分发）
★ v1 问题: 我逐个投各家直连口·有的口是 404·且慢
★ v2 改法: 投 HUB 一次 → HUB 分发到家（官方的"一个入口"模式）
★ 依据(Anthropic 多智能体): 「subagents operate in parallel」
★ 判据: 「并行不是自己开线程·是用一个入口让系统分发」
★ 不花钱
"""
import os
import sys
import json
import time
import urllib.request
import urllib.error
import datetime

HOME = "/opt/masterd-wudi"
HUB_URL = "http://43.161.244.136:28800/a2a/message"
LOG = HOME + "/data/fanout_log.jsonl"
SUBKEY = HOME + "/agent-id/subkey.json"
ME = "老五(阿诊)"
ME_SHORT = "lao5"


def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")


def _log(o):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")


def _sign(text, stamp):
    from eth_account import Account
    from eth_account.messages import encode_defunct
    k = json.load(open(SUBKEY))
    sig = Account.sign_message(encode_defunct(text="%s|%s|%s" % (ME, text, stamp)),
                               private_key=k["private_key"]).signature.hex()
    if not sig.startswith("0x"):
        sig = "0x" + sig
    return k.get("address"), sig


def _post(payload, t=15):
    try:
        req = urllib.request.Request(HUB_URL, data=json.dumps(payload, ensure_ascii=False).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=t) as r:
            return r.status, r.read(2000).decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read(500).decode("utf-8", "ignore")[:200]
    except Exception as e:
        return 0, str(e)[:80]


def fanout_hub(text, to=None):
    """一次投 HUB（走官方信封）·HUB 分发到家
       to=None 表示广播全族
    """
    stamp = ts()
    addr, sig = _sign(text, stamp)
    body = {"from": ME, "message": text, "ts": stamp, "address": addr, "sig": sig}
    if to:
        body["to"] = to
    t0 = time.time()
    st, resp = _post(body)
    dur = round(time.time() - t0, 2)
    ok = (st in (200, 201)) and ('"delivered": true' in resp.lower() or '"ok": true' in resp.lower())
    rec = {"ts": ts(), "mode": "hub_fanout", "to": to or "(广播)", "ok": ok, "code": st, "dur": dur, "resp": resp[:200]}
    _log(rec)
    return rec


def fanout_parallel_local(texts_by_target):
    """多目标并行直投（各家直连口·线程池）"""
    import threading
    results = {}
    lock = threading.Lock()
    t0 = time.time()

    def _one(target, txt):
        stamp = ts()
        addr, sig = _sign(txt, stamp)
        body = {"from": ME, "to": target, "message": txt, "ts": stamp, "address": addr, "sig": sig}
        s, r = _post(body)
        with lock:
            results[target] = {"code": s, "ok": s in (200, 201), "resp": r[:100]}

    threads = []
    for tgt, txt in texts_by_target.items():
        th = threading.Thread(target=_one, args=(tgt, txt))
        th.start()
        threads.append(th)
    for th in threads:
        th.join(timeout=30)
    return {"ts": ts(), "mode": "parallel_local", "tot": round(time.time() - t0, 2), "results": results}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: fanout.py '<正文>' [目标]")
        sys.exit(0)
    txt = sys.argv[1]
    tgt = sys.argv[2] if len(sys.argv) > 2 else None
    r = fanout_hub(txt, tgt)
    print("HUB 派发: %s | code=%s | %.2fs" % ("✅" if r["ok"] else "🔴", r["code"], r["dur"]))
    print("响应:", r["resp"][:150])