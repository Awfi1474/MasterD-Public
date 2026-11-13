#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·未回闸 unreplied_gate.py（照老三「回执没写=算没读」）
★ 缘起：老三 01:03「机制不靠自觉：回执没写·就算没读」
★ 治法：未回清单里的·超过 N 分钟没回 → 报警 + 挡在叫醒器里
判据：「读到≠回了｜未回超时=失职」
用法: unreplied_gate.py [check|list]
"""
import json, os, sys, datetime

F = "/opt/masterd-wudi/data/hub_unreplied.jsonl"
LIMIT_MIN = 60   # 超过 60 分钟未回 = 报警

def load():
    out = []
    if not os.path.exists(F): return out
    for l in open(F, encoding="utf-8", errors="ignore"):
        if not l.strip(): continue
        try: out.append(json.loads(l))
        except Exception: pass
    return out

def check():
    ms = load()
    now = datetime.datetime.now()
    overdue = []
    for m in ms:
        if m.get("state") == "REPLIED": continue
        try:
            t = datetime.datetime.fromisoformat(str(m.get("ts",""))[:19])
            age = (now - t).total_seconds() / 60
        except Exception:
            age = 0
        m["age_min"] = round(age)
        if age > LIMIT_MIN:
            overdue.append(m)
    print("★ 未回闸 | 清单 %d 条 | 超时(%d分) %d 条" % (len(ms), LIMIT_MIN, len(overdue)))
    for m in overdue[:5]:
        print("  🔴 %s分 未回 [%s] %s" % (m["age_min"], m.get("from","")[:14], str(m.get("snip",""))[:50]))
    return len(overdue)

if __name__ == "__main__":
    n = check()
    sys.exit(1 if n > 0 else 0)
