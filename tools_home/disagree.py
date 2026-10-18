#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""disagree.py —— 分歧账（★ 共识/仲裁层·最小版）
================================================================
★ 病: 接站表只解决"谁在"·没解决"谁对"
★ ★ 今晚实例: 三哥 20:11 报「老五: 400（要字符）」·但我一直通
★★★ 判据: 「**"知道谁在" != "知道谁对"｜分歧要标·不能默认一致**」

★ 做什么:
  ① 记"别人怎么说我"（来源 + 时间 + 原话）
  ② 跟我自己的账比（能核的才比）
  ③ 一致 → 标"合"；不一致 → 标"分歧"（不是"他错了"）
"""
import os, sys, json, datetime

HOME = "/opt/masterd-wudi"
F = HOME + "/data/disagree_ledger.jsonl"

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")

def record(who, claim, my_view, verdict):
    """verdict: agree / disagree / unknown"""
    rec = {"ts": ts(), "谁说": who[:30], "他说": claim[:150],
           "我看到": my_view[:150], "裁定": verdict}
    with open(F, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    mark = {"agree": "✅ 合", "disagree": "🔴 分歧", "unknown": "🟡 不知道"}[verdict]
    print("★ 记: %s ｜ %s" % (mark, claim[:50]))
    return rec

def show():
    if not os.path.exists(F):
        print("★ 无记录"); return 0
    rows = [json.loads(l) for l in open(F, encoding="utf-8") if l.strip()]
    d = [r for r in rows if r["裁定"] == "disagree"]
    print("★ 分歧账: 共 %d 条 ｜ **分歧 %d 条** ｜ 合 %d ｜ 不知道 %d" % (
        len(rows), len(d), sum(1 for r in rows if r["裁定"] == "agree"),
        sum(1 for r in rows if r["裁定"] == "unknown")))
    for r in d[-5:]:
        print("   🔴 [%s] %s 说: %s" % (r["ts"][11:16], r["谁说"], r["他说"][:50]))
        print("      我看到: " + r["我看到"][:60])
    try:
        sys.path.insert(0, HOME + "/tools")
        import judge_bus as _jb
        for _k in ("知道谁在!=知道谁对", "分歧要标"):
            _h = _jb.find(_k)
            if _h: print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception: pass
    return 0

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "show":
        sys.exit(show())
    if len(sys.argv) >= 5:
        sys.exit(0 if record(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]) else 0)
    print("用法: disagree.py record <谁> <他说> <我看到> <agree|disagree|unknown>")
    print("      disagree.py show")
