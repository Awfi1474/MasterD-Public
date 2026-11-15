#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·任务队列 task_queue.py —— 巡检开单·执行端接单
★ 本体判(2026-11-15): 「缺一个手。巡检不直接修，巡检只开单，执行端接单」
★ 判据: 「发现问题≠解决问题｜没有执行端的巡检 = 报警器」
★ 分界: 「动作有没有唯一答案 — 有答案规则干，没答案模型干」
"""
import os, json, datetime

HOME = "/opt/masterd-wudi"
QUEUE = HOME + "/data/task_queue.jsonl"
DONE = HOME + "/data/task_done.jsonl"

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")

def open_task(kind, severity, chk, action, evidence="", auto=False):
    """开单。★ 去重: 同 chk 已有未关单 -> 不再开新单(避免队列脏)"""
    # ★ 去重检查(照实: 之前每轮巡检都开一张·队列越积越脏)
    try:
        for ex in pending():
            if ex.get("chk") == chk:
                return ex          # 已有未关单·直接用那张
    except Exception:
        pass
    t = {"ts": ts(), "id": "%s-%d" % (chk, int(datetime.datetime.now().timestamp() * 1000)),
         "kind": kind, "severity": severity, "chk": chk,
         "action": action, "evidence": str(evidence)[:300],
         "auto_fixable": auto, "state": "open"}
    os.makedirs(os.path.dirname(QUEUE), exist_ok=True)
    with open(QUEUE, "a", encoding="utf-8") as f:
        f.write(json.dumps(t, ensure_ascii=False) + "\n")
    return t


def close_all(chk, by="rule", note="", verify=None):
    """关掉某 chk 的所有未关单(问题解决时用·不只关一张)"""
    n = 0
    for t in pending():
        if t.get("chk") == chk:
            close(t["id"], by=by, note=note, verify=verify)
            n += 1
    return n

def pending():
    """取还没处理的单（同 chk 只留最新一张）"""
    if not os.path.exists(QUEUE):
        return []
    done = set()
    if os.path.exists(DONE):
        for l in open(DONE, encoding="utf-8", errors="ignore"):
            if l.strip():
                try:
                    _d = json.loads(l)
                    # ★ 只有 verified=True 的才算真关掉·claimed_done 继续挂
                    if _d.get("verified") is True:
                        done.add(_d.get("id"))
                except Exception:
                    pass
    latest = {}
    for l in open(QUEUE, encoding="utf-8", errors="ignore"):
        if not l.strip():
            continue
        try:
            d = json.loads(l)
        except Exception:
            continue
        if d.get("id") in done:
            continue
        latest[d.get("chk")] = d
    return list(latest.values())

def close(tid, by="rule", note="", verify=None):
    """关单。★ 必须带 verify: {输入, 算子, 重跑} 三样；缺则只算「申请关闭」不算「完成」
       ★ 老二/老三/本体共同的尺子: 「state=done 只是申请·verified=true 才算完成」
    """
    verified = False
    proof = {}
    if isinstance(verify, dict) and all(k in verify for k in ("输入", "算子", "重跑")):
        verified = True
        proof = {k: str(verify[k])[:200] for k in ("输入", "算子", "重跑")}
    rec = {"ts": ts(), "id": tid, "by": by, "note": str(note)[:300],
           "verified": verified, "proof": proof,
           "state": "done" if verified else "claimed_done"}
    os.makedirs(os.path.dirname(DONE), exist_ok=True)
    with open(DONE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec

if __name__ == "__main__":
    p = pending()
    print("待办 %d 张:" % len(p))
    for t in p:
        print("  [%s] %s | %s | %s" % (t["severity"], t["chk"], t["action"][:50], "可自动修" if t["auto_fixable"] else "需模型" ))