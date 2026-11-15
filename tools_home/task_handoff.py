#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·任务交接层 task_handoff.py（照本体判断「通信是路·交接才是车」）
★ 三字段: task_id / acceptance(验收判据) / handoff_to(做完给谁)
★ 账: data/task_ledger.jsonl（发起人/承接人/状态/验收证据）
★ 判据（本体原话）: 没账的协作等于没发生|不接也要回·不接不吭声是最大坑
用法:
  task_handoff.py new "<事项>" "<acceptance>" "<handoff_to>"   → 发起
  task_handoff.py accept <task_id> "<预计什么算完>"             → 接
  task_handoff.py reject <task_id> "<为什么>"                   → 不接(也要回)
  task_handoff.py done <task_id> "<证据(文件/输出/账)"          → 完成(必须带证据)
  task_handoff.py list                                          → 看账
"""
import json, sys, os, hashlib, datetime

TZ = datetime.timezone(datetime.timedelta(hours=8))
HOME = "/opt/masterd-wudi"
LEDGER = HOME + "/data/task_ledger.jsonl"

def now():
    return datetime.datetime.now(TZ).isoformat(timespec="seconds")

def append(rec):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def load():
    out = []
    if os.path.exists(LEDGER):
        for l in open(LEDGER, encoding="utf-8", errors="ignore"):
            if not l.strip(): continue
            try: out.append(json.loads(l))
            except Exception: pass
    return out

def main():
    if len(sys.argv) < 2:
        print(__doc__); return 1
    act = sys.argv[1]

    if act == "new":
        if len(sys.argv) < 5:
            print("用法: new \"<事项>\" \"<acceptance>\" \"<handoff_to>\""); return 1
        what, acc, to = sys.argv[2], sys.argv[3], sys.argv[4]
        tid = "T-" + hashlib.sha1((now() + what).encode()).hexdigest()[:12]
        rec = {"ts": now(), "event": "new", "task_id": tid, "what": what,
               "acceptance": acc, "handoff_to": to, "from": "lao5", "state": "pending"}
        append(rec)
        print("✅ 发起 task_id=%s" % tid)
        print("   acceptance: %s" % acc)
        print("   handoff_to: %s" % to)
        return 0

    if act in ("accept", "reject"):
        if len(sys.argv) < 4:
            print("用法: %s <task_id> \"<说明>\"" % act); return 1
        tid, note = sys.argv[2], sys.argv[3]
        rec = {"ts": now(), "event": act, "task_id": tid,
               "by": "lao5", "note": note,
               "state": "accepted" if act == "accept" else "rejected"}
        append(rec)
        print("✅ %s %s: %s" % (act, tid, note))
        return 0

    if act == "done":
        if len(sys.argv) < 4:
            print("用法: done <task_id> \"<证据>\""); return 1
        tid, ev = sys.argv[2], sys.argv[3]
        if not ev or len(ev) < 5:
            print("🔴 拒: 完成必须带可核证据(文件/输出/账)·不许说'我做完了'")
            return 2
        rec = {"ts": now(), "event": "done", "task_id": tid, "evidence": ev, "state": "done"}
        append(rec)
        print("✅ done %s | 证据: %s" % (tid, ev[:80]))
        return 0

    if act == "list":
        rows = load()
        tasks = {}
        for r in rows:
            t = r.get("task_id")
            if not t: continue
            tasks.setdefault(t, {"task_id": t, "what": r.get("what",""), "log": []})
            tasks[t]["log"].append(r)
        print("★ 任务账（%d 条任务）" % len(tasks))
        for t, v in list(tasks.items())[-10:]:
            last = v["log"][-1]
            print("  %s | %-30s | 状态=%s | 最后=%s" % (t, v["what"][:28], last.get("state"), last.get("ts","")[11:19]))
        return 0
    print(__doc__); return 1

if __name__ == "__main__":
    sys.exit(main())
