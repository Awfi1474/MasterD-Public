#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·统一总账 merge_ledger.py（照实: 本体真行为分散4账本·建总视图）
★ 判据: 「昨天做了什么」要一处能看到·不用翻4个文件
用法: merge_ledger.py [日期]
"""
import json, os, sys, datetime
from collections import Counter

HOME = "/opt/masterd-wudi"
SOURCES = [
 ("思考", HOME + "/data/think_in.jsonl"),
 ("任务", HOME + "/data/a2a_tasks.jsonl"),
 ("分级", HOME + "/data/tier_ledger.jsonl"),
 ("改文件", HOME + "/data/exec_ledger.jsonl"),
 ("指挥", HOME + "/data/command_ledger.jsonl"),
]

def load(path, day):
    out = []
    if not os.path.exists(path): return out
    for l in open(path, encoding="utf-8", errors="ignore"):
        if not l.strip(): continue
        try: d = json.loads(l)
        except Exception: continue
        ts = str(d.get("ts") or d.get("created") or d.get("timestamp") or "")
        if day and not ts.startswith(day): continue
        out.append((ts, d))
    return out

if __name__ == "__main__":
    day = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
    print("★ 统一总账 · %s" % day)
    print("=" * 60)
    total = 0
    for name, path in SOURCES:
        rows = load(path, day)
        total += len(rows)
        print("【%s】%d 条" % (name, len(rows)))
        for ts, d in rows[-3:]:
            snip = ""
            for k in ("what","thought","title","cmd","message","动作","q","决定"):
                if d.get(k): snip = str(d[k])[:80]; break
            print("   %s | %s" % (ts[:19], snip.replace("\n"," ")))
    print("=" * 60)
    print("★ 合计 %d 条（%s）" % (total, day))
    if total == 0:
        print("⚠️ 这天没有记录 · 不是没做·是没记账")
