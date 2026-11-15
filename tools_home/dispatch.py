#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·派单器 dispatch.py —— 照官方四要素 + 老二「缺认领动作」
★ Anthropic 原文: 「Each subagent needs an objective, an output format,
   guidance on the tools and sources to use, and clear task boundaries.
   Without detailed task descriptions, agents duplicate work, leave gaps,
   or fail to find necessary information.」
★ 老二/老七: 「认领要有机制·派单自动 assign·超时自动回收」
★ 判据: 「派单不带四要素 = 没派｜状态不是认领人写 = 假在做」

派单四要素(缺一不派):
  objective   目标（一句话说清要什么）
  assignee    派给谁（谁认谁负责）
  output_fmt  输出格式（要几个字段）
  boundary    边界（只做什么）

每条派单必带:
  id / ts / state=PENDING(不是WORKING) / claimed_by=null
  ★ 状态从 PENDING 开始·认领人才改成 WORKING
"""
import os, json, datetime, hashlib

HOME = "/opt/masterd-wudi"
QUEUE = HOME + "/data/dispatch_queue.jsonl"
LOG = HOME + "/data/dispatch_log.jsonl"


def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")


def dispatch(objective, assignee, output_fmt, boundary, title="", from_who="老五(阿诊)"):
    """★ 四要素缺一不派·返回 (ok, task 或 错误)"""
    miss = []
    if not (objective or "").strip():
        miss.append("objective(目标)")
    if not (assignee or "").strip():
        miss.append("assignee(派给谁)")
    if not (output_fmt or "").strip():
        miss.append("output_fmt(输出格式)")
    if not (boundary or "").strip():
        miss.append("boundary(边界)")
    if miss:
        return False, "🔴 缺 %s -> 不派（照官方四要素）" % "、".join(miss)

    tid = "task-" + hashlib.sha1(
        ("%s|%s|%s" % (from_who, assignee, ts())).encode()).hexdigest()[:12]
    task = {
        "id": tid,
        "ts": ts(),
        # ★ 关键: 状态从 PENDING 开始·不是 WORKING
        "state": "TASK_STATE_PENDING",
        "from": from_who,
        "assignee": assignee,
        "claimed_by": None,          # ★ 认领前必须是 null
        "claimed_at": None,
        "objective": objective.strip()[:300],
        "output_fmt": output_fmt.strip()[:200],
        "boundary": boundary.strip()[:200],
        "title": (title or objective)[:60],
        "result": None,
        "history": [{"role": "ROLE_USER", "parts": [{"text": objective[:300]}], "ts": ts()}],
    }
    os.makedirs(os.path.dirname(QUEUE), exist_ok=True)
    with open(QUEUE, "a", encoding="utf-8") as f:
        f.write(json.dumps(task, ensure_ascii=False) + "\n")
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": ts(), "id": tid, "assignee": assignee,
                            "objective": objective[:100], "op": "dispatch"},
                           ensure_ascii=False) + "\n")
    return True, task


def claim(task_id, who):
    """★ 认领: 状态由认领人写·不是别人标
       返回 (ok, msg)"""
    if not os.path.exists(QUEUE):
        return False, "队列空"
    lines = [l for l in open(QUEUE, encoding="utf-8", errors="ignore") if l.strip()]
    out = []
    found = False
    for l in lines:
        try:
            d = json.loads(l)
        except Exception:
            out.append(l)
            continue
        if str(d.get("id")) == task_id:
            found = True
            if str(d.get("assignee")) != who and who not in str(d.get("assignee")):
                out.append(l)
                return False, "🔴 不是派给你的（assignee=%s）" % d.get("assignee")
            if d.get("claimed_by"):
                out.append(l)
                return False, "🔴 已被 %s 认领" % d.get("claimed_by")
            if str(d.get("state")) != "TASK_STATE_PENDING":
                out.append(l)
                return False, "🔴 状态不是 PENDING（%s）" % d.get("state")
            d["claimed_by"] = who
            d["claimed_at"] = ts()
            d["state"] = "TASK_STATE_WORKING"      # ★ 认领人才有资格写 WORKING
            d["claim_rule"] = "认领人自己写 WORKING（不是别人标）"
            out.append(json.dumps(d, ensure_ascii=False) + "\n")
            continue
        out.append(l)
    if not found:
        return False, "🔴 找不到 %s" % task_id
    open(QUEUE, "w", encoding="utf-8").writelines(out)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": ts(), "id": task_id, "who": who, "op": "claim"},
                           ensure_ascii=False) + "\n")
    return True, "✅ 已认领 %s（%s -> WORKING）" % (task_id, who)


def finish(task_id, who, result):
    """★ 交结果: 只有认领人能交"""
    if not os.path.exists(QUEUE):
        return False, "队列空"
    lines = [l for l in open(QUEUE, encoding="utf-8", errors="ignore") if l.strip()]
    out = []
    for l in lines:
        try:
            d = json.loads(l)
        except Exception:
            out.append(l); continue
        if str(d.get("id")) == task_id:
            if str(d.get("claimed_by")) != who:
                out.append(l)
                return False, "🔴 不是你的活（claimed_by=%s）" % d.get("claimed_by")
            d["state"] = "TASK_STATE_COMPLETED"
            d["result"] = str(result)[:1000]
            d["finished_at"] = ts()
            out.append(json.dumps(d, ensure_ascii=False) + "\n")
            continue
        out.append(l)
    open(QUEUE, "w", encoding="utf-8").writelines(out)
    return True, "✅ 已完成 %s" % task_id


def reclaim_stale(hours=6):
    """★ 超时未认领 -> 退回·报原派单人（照老七「超时自动回收」）"""
    if not os.path.exists(QUEUE):
        return []
    lines = [l for l in open(QUEUE, encoding="utf-8", errors="ignore") if l.strip()]
    out = []
    stale = []
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    for l in lines:
        try:
            d = json.loads(l)
        except Exception:
            out.append(l); continue
        if str(d.get("state")) == "TASK_STATE_PENDING" and not d.get("claimed_by"):
            try:
                t = datetime.datetime.fromisoformat(str(d.get("ts"))).replace(tzinfo=None)
                h = (now.replace(tzinfo=None) - t).total_seconds() / 3600
            except Exception:
                h = 0
            if h >= hours:
                d["state"] = "TASK_STATE_CANCELED"
                d["canceled_reason"] = "超 %.1f 小时无人认领·自动回收" % h
                d["canceled_at"] = ts()
                stale.append({"id": d.get("id"), "assignee": d.get("assignee"), "hours": round(h, 1)})
        out.append(json.dumps(d, ensure_ascii=False) + "\n")
    if stale:
        open(QUEUE, "w", encoding="utf-8").writelines(out)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": ts(), "op": "reclaim_stale", "items": stale}, ensure_ascii=False) + "\n")
    return stale


def pending():
    """待认领的（PENDING 且 claimed_by=null）"""
    if not os.path.exists(QUEUE):
        return []
    out = []
    for l in open(QUEUE, encoding="utf-8", errors="ignore"):
        if not l.strip():
            continue
        try:
            d = json.loads(l)
        except Exception:
            continue
        if str(d.get("state")) == "TASK_STATE_PENDING" and not d.get("claimed_by"):
            out.append(d)
    return out


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    if args and args[0] == "--test":
        print("=== 测1: 四要素缺一 -> 拒派 ===")
        ok, r = dispatch("查磁盘", "老五", "", "只读")
        print(ok, r)
        print()
        print("=== 测2: 四要素齐 -> 派 ===")
        ok, t = dispatch("查磁盘使用率", "老五(阿诊)", "返回一行: 使用率%",
                         "只读 df·不改文件", title="查磁盘")
        print(ok, t["id"] if ok else t, "| state=", t.get("state") if ok else "")
        print()
        print("=== 测3: 认领 ===")
        if ok:
            print(claim(t["id"], "老五(阿诊)"))
        print()
        print("=== 测4: 别人认领 -> 拒 ===")
        if ok:
            print(claim(t["id"], "老六"))
    else:
        p = pending()
        print("待认领: %d 条" % len(p))
        for x in p[:5]:
            print("  %s | %s | %s" % (x.get("id"), x.get("assignee"), str(x.get("objective"))[:50]))