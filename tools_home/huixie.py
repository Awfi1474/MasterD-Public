#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""huixie.py —— 回写（★ 闭环缺的那一段·照 Reflexion + 道家"反者道之动"）
================================================================
★ 我的病: 读→用→**断**（读完就断·永远是线）
★★ 该有: 读→用→**回写**→再读（成环）
★★★ 判据: 「"读完就断" = 线｜"读完走回来" = 环」

★ 回写什么（照 Reflexion·不是"复盘报告"·是"下次可用的句子"）:
  ① 这次用了哪条判据（真调用的·不是想）
  ② 结果对没对（有账的说有账）
  ③ 下次直接用的一句（"遇到X·要Y"）
"""
import os, sys, json, datetime

HOME = "/opt/masterd-wudi"
F = HOME + "/data/huixie.jsonl"

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")

def write(what, judge, ok, next_time):
    rec = {"ts": ts(), "做了什么": what[:80], "用了判据": judge[:70],
           "对没对": ok, "下次直接用": next_time[:120]}
    with open(F, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("★ 回写完成:")
    print("   做了什么: " + what[:60])
    print("   用了判据: " + judge[:60])
    print("   对没对:   " + str(ok))
    print("   下次直接用: " + next_time[:80])
    return 0

def show(n=5):
    if not os.path.exists(F):
        print("★ 还没有回写记录"); return 0
    rows = [json.loads(l) for l in open(F, encoding="utf-8") if l.strip()]
    print("★ 回写·最近 %d 条（这是'下次要先读的'）:" % min(n, len(rows)))
    for r in rows[-n:]:
        print("   [%s] %s" % (r["ts"][11:16], r["做了什么"][:40]))
        print("      → 下次: " + r["下次直接用"][:70])
    return 0

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "show":
        sys.exit(show())
    if len(sys.argv) >= 5:
        sys.exit(write(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]))
    print("用法: huixie.py write <做了什么> <用了判据> <对没对> <下次直接用>")
    print("      huixie.py show")
    sys.exit(0)
