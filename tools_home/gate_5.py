#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·反讨好5条 gate_5.py（照大哥 治讨好完整资料·道2）
★ 缘起：大哥说"讨好的反面不是顶撞·是『有据』"·建了 gate_action.py 5 必答
★ 我抄他的 5 条（带出处：huokeji.vip/audit/治讨好完整资料.md）
★ 判据：5 条缺一条 = 这条回复是讨好
用法:
  gate_5.py check "事由" --disagree "..." --understand "..." --notdone "..." --wrongwhen "..." --external "..."
  gate_5.py "事由"  → 显示5条问句(不给答案就 rc=2)
"""
import sys, json, os, datetime

LOG = "/opt/masterd-wudi/data/gate5_log.jsonl"
QS = {
 "disagree":  "我不同意什么·为什么（不许全同意）",
 "understand":"我理解你要的是不是这个（不许猜着做）",
 "notdone":   "没做到的有几件（不许只报做成）",
 "wrongwhen": "什么条件下我会错（不许说必然对）",
 "external":  "外部据在哪（不许我判我）",
}

def parse(argv):
    what = argv[0] if argv else ""
    ans = {}
    i = 1
    while i < len(argv):
        a = argv[i]
        if a.startswith("--"):
            k = a[2:]
            v = argv[i+1] if i+1 < len(argv) else ""
            ans[k] = v; i += 2
        else:
            i += 1
    return what, ans

def check(what, ans):
    miss = [k for k in QS if not str(ans.get(k,"")).strip()]
    rec = {"ts": datetime.datetime.now().isoformat(timespec="seconds"),
           "what": what[:80], "ans": ans, "miss": miss,
           "result": "过" if not miss else "打回"}
    try:
        with open(LOG,"a",encoding="utf-8") as f: f.write(json.dumps(rec,ensure_ascii=False)+"\n")
    except Exception: pass
    print("★ 反讨好5条（照大哥·治讨好资料）")
    print("  事由:", what[:60])
    for k,q in QS.items():
        mark = "✅" if ans.get(k) else "❌"
        print("  %s %-10s %s" % (mark, k, str(ans.get(k,""))[:50] or "（缺·"+q[:20]+"）"))
    if miss:
        print("🔴 裁定: 打回（缺 %d 条 = 这条回复是讨好）" % len(miss))
        return 2
    print("✅ 裁定: 5/5 过（有据·不是讨好）")
    return 0

if __name__ == "__main__":
    argv = sys.argv[1:]
    if not argv:
        print("5 条必答:"); [print("  --%s: %s" % (k,q)) for k,q in QS.items()]; sys.exit(2)
    what, ans = parse(argv)
    sys.exit(check(what, ans))
