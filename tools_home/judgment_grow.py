#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·判据生长器 judgment_grow.py（照 ConfAgents·arXiv:2508.04915）
★ 缘起：ConfAgents 原话「agents can become better tool-users but cannot learn
   to become better strategic planners」→ 我的 12 条判据是写死的·不会自己长
★ 治法：从【打回记录 + 真错案例】里·自动生成【新判据候选】
   判据候选不直接生效（要人/六问确认），先落「候选池」

★ 判据（我的）：
  「判据写死=不会成长｜判据从错误里长=会成长｜但长出来的要审（不自动生效）」
"""
import json, os, re
from collections import Counter

HOME = "/opt/masterd-wudi"
DL = HOME + "/data/decide_log.jsonl"
OUT = HOME + "/data/judgment_candidates.jsonl"

def harvest():
    """从打回/跳过记录里找可变成判据的模式"""
    cands = []
    if not os.path.exists(DL): return cands
    fails = Counter(); samples = {}
    for l in open(DL, encoding="utf-8", errors="ignore"):
        try:
            d = json.loads(l)
            if d.get("结果") == "打回":
                for f in d.get("缺", []):
                    fails[f] += 1
                    samples.setdefault(f, []).append(str(d.get("决定",""))[:60])
        except Exception: pass
    for f, n in fails.most_common():
        if n >= 3:
            cands.append({
                "型": "从打回长判据",
                "缺失": f,
                "次数": n,
                "样案例": samples.get(f, [])[:3],
                "候选判据": "凡出现【%s】·先按此纠正再加：%s" % (f, _fix_hint(f)),
                "状态": "待审（不自动生效）",
            })
    return cands

def _fix_hint(fail):
    m = {
        "③辨不出证": "先判'这是不是决定'·不是决定不过六问（已落地为门槛）",
        "①依什么": "先拉到宪法/标准原文·拉不到就说不清",
        "④不知道下一步会怎么坏": "必答'会重犯哪一条真病'",
        "⑥反证": "必从判据总线真查出·不许硬编码",
    }
    return m.get(fail, "（待定·需人补）")

if __name__ == "__main__":
    c = harvest()
    with open(OUT, "a", encoding="utf-8") as f:
        for x in c:
            import datetime
            x["ts"] = datetime.datetime.now().isoformat(timespec="seconds")
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    print("★ 判据生长器（照 ConfAgents）| 长出 %d 条候选判据" % len(c))
    for x in c:
        print("  [%dx] %s\n     → %s\n     状态: %s" % (x["次数"], x["缺失"], x["候选判据"], x["状态"]))
    print("\n★ 判据: 长出来≠生效｜先进候选池·要审（防自己给自己放宽）")
