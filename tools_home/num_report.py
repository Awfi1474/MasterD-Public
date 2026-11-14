#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·报数字器 num_report.py（照L1第23条·报数字必须跑全量）
★ 判据：数字必有命令回执｜不许看子集报总数
用法: num_report.py <账本文件> [字段名]
"""
import json, os, sys
from collections import Counter

def report(path, field=None):
    if not os.path.exists(path):
        print("❌ 文件不存在:", path); return
    lines = [l for l in open(path, encoding="utf-8", errors="ignore") if l.strip()]
    print("★ 报数字（全量·不是子集）")
    print("  文件:", os.path.basename(path))
    print("  总行数:", len(lines))
    if field:
        c = Counter()
        bad = 0
        for l in lines:
            try: d = json.loads(l)
            except Exception: bad += 1; continue
            v = d.get(field)
            if isinstance(v, dict): v = v.get("state")
            c[str(v)] += 1
        print("  字段 %r 分布:" % field)
        for k, v in c.most_common(15): print("    %-28s %d" % (k, v))
        if bad: print("  解析失败:", bad)
    print("\n★ 判据: 全量跑过才算数字｜看起来查了!=真查了")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: num_report.py <jsonl文件> [字段]")
        sys.exit(1)
    report(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
