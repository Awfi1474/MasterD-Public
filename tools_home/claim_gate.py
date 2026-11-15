#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·认领闸 claim_gate.py —— 照老二/老七判据
★ 老二说: 「全族缺少一个认领动作」
★ 老七原话(2026-11-15 17:30):
   「认领要靠人·还是靠机制？如果认领动作本身没有拦截机制
    （派单就自动 assign·超时自动回收）·那没人认下次还会重复发生」
★ 老六实证: POST /task/pull → task:null·reclaimed:0
   「任务被标 working · 但我这一侧领不到它」
★ 判据: 「WORKING 但 claimed_by=null = 假在做｜真有认领才有认领记录」

本器做三件(零模型):
  ① 扫: WORKING 里 claimed_by=null 的（假 working）
  ② 认领: 我能认的（assignee=我 或 无主的）→ 写 claimed_by + 落账
  ③ 超时回收: 超 N 小时没人认 → 报回/退回 pending（不擅自替别人认）
"""
import os, re, json, datetime

HOME = "/opt/masterd-wudi"
TASKS = HOME + "/data/a2a_tasks.jsonl"
CLAIM_LOG = HOME + "/data/claim_ledger.jsonl"
ME_NAMES = ("老五", "lao5", "MasterD(生命科學·五弟)", "MasterD(生命科学·五弟)", "阿诊")

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")

def now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))

def scan():
    """① 扫假 working"""
    if not os.path.exists(TASKS):
        return {"total": 0, "working": 0, "unclaimed": 0, "mine_unclaimed": 0, "oldest_h": 0}
    working = []
    for l in open(TASKS, encoding="utf-8", errors="ignore"):
        if not l.strip():
            continue
        try:
            d = json.loads(l)
        except Exception:
            continue
        if str(d.get("state")) != "TASK_STATE_WORKING":
            continue
        working.append(d)
    unclaimed = [d for d in working if not d.get("claimed_by")]
    def _is_mine(d):
        a = str(d.get("assignee") or "")
        to = str(d.get("to") or "")
        return any(m in a or m in to for m in ME_NAMES)
    mine = [d for d in unclaimed if _is_mine(d)]
    oldest_h = 0
    if working:
        tss = []
        for d in working:
            s = str(d.get("ts") or d.get("created_at") or "")
            try:
                tss.append(datetime.datetime.fromisoformat(s.replace("Z", "+00:00")))
            except Exception:
                pass
        if tss:
            _naive = []
            for t in tss:
                try:
                    _naive.append(t.replace(tzinfo=None))
                except Exception:
                    pass
            if _naive:
                oldest_h = round((now().replace(tzinfo=None) - min(_naive)).total_seconds() / 3600, 1)
    return {"total": len(working), "working": len(working),
            "unclaimed": len(unclaimed), "mine_unclaimed": len(mine),
            "oldest_h": oldest_h}

def claim_mine(limit=20, dry=True):
    """② 认领：只认 assignee 是我的（不替别人认）
       返回 (是否成功, 说明)"""
    if not os.path.exists(TASKS):
        return False, "无任务文件"
    lines = [l for l in open(TASKS, encoding="utf-8", errors="ignore") if l.strip()]
    out = []
    claimed = []
    for l in lines:
        try:
            d = json.loads(l)
        except Exception:
            out.append(l)
            continue
        state = str(d.get("state"))
        a = str(d.get("assignee") or "")
        to = str(d.get("to") or "")
        is_mine = any(m in a or m in to for m in ME_NAMES)
        if state == "TASK_STATE_WORKING" and not d.get("claimed_by") and is_mine and len(claimed) < limit:
            d["claimed_by"] = "老五(阿诊)"
            d["claimed_at"] = ts()
            d["claim_rule"] = "assignee 或 to 含我·且有 WORKING 无 claimed_by"
            claimed.append(str(d.get("id") or d.get("task_id") or "?"))
        out.append(json.dumps(d, ensure_ascii=False) + "\n")

    if not dry and claimed:
        open(TASKS, "w", encoding="utf-8").writelines(out)
        with open(CLAIM_LOG, "a", encoding="utf-8") as f:
            for cid in claimed:
                f.write(json.dumps({"ts": ts(), "id": cid, "claimed_by": "老五(阿诊)",
                                    "rule": "assignee含我 + WORKING + 无claimed_by"}, ensure_ascii=False) + "\n")
    return (len(claimed) > 0), "认领 %d 条（dry=%s）: %s" % (len(claimed), dry, ",".join(claimed[:3]))

def stale_unclaimed(hours=6):
    """③ 超时未认领的（报出来·不替别人认）
       ★ 老七判据: 「超时不认 ≠ 没人看见」"""
    if not os.path.exists(TASKS):
        return []
    out = []
    for l in open(TASKS, encoding="utf-8", errors="ignore"):
        if not l.strip():
            continue
        try:
            d = json.loads(l)
        except Exception:
            continue
        if str(d.get("state")) != "TASK_STATE_WORKING" or d.get("claimed_by"):
            continue
        s = str(d.get("ts") or d.get("created_at") or "")
        try:
            t = datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            continue
        h = (now().replace(tzinfo=None) - t).total_seconds() / 3600
        if h >= hours:
            out.append({"id": str(d.get("id") or d.get("task_id") or "?"),
                        "assignee": str(d.get("assignee") or "?")[:20],
                        "hours": round(h, 1), "title": str(d.get("title") or "")[:40]})
    return sorted(out, key=lambda x: -x["hours"])

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    if "--claim" in args:
        ok, msg = claim_mine(dry=False)
        print(("✅ " if ok else "· ") + msg)
    elif "--stale" in args:
        s = stale_unclaimed(6)
        print("超 6 小时未认领: %d 条" % len(s))
        for x in s[:10]:
            print("  %.1fh  %-14s %s" % (x["hours"], x["assignee"], x["title"]))
    else:
        st = scan()
        print(json.dumps(st, ensure_ascii=False, indent=1))
        s = stale_unclaimed(6)
        print("超6小时未认领: %d 条" % len(s))