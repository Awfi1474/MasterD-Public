#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""autobiography.py — 我的自传(经历·按天串) (老五 2026-11-10)
目标一(涌现)+目标三(相续): 把"每天干的活"串成"我的故事"。
判据: 条(点)+经历图(线)+反思(面) → 自传(时间线上的"我")
做法: 从 M2 记忆 + REFLECTIONS 里·按天抽"我那天干了啥"·写一行自传。
用法: python3 autobiography.py            # 生成/更新自传
输出: /opt/masterd-wudi/memory/AUTOBIOGRAPHY.md
"""
import json, os
from collections import defaultdict

HOME = "/opt/masterd-wudi"
M2 = HOME + "/memory/LAYERED/M2.jsonl"
REF = HOME + "/memory/REFLECTIONS.jsonl"
OUT = HOME + "/memory/AUTOBIOGRAPHY.md"

def load(p):
    rows = []
    try:
        with open(p, encoding='utf-8', errors='ignore') as f:
            for l in f:
                try: rows.append(json.loads(l))
                except: pass
    except: pass
    return rows

def main():
    rows = load(M2)
    # 按天分组·每天取几条"亮点"
    byday = defaultdict(list)
    for r in rows:
        d = str(r.get('ts',''))[:10]
        if d: byday[d].append(r)
    days = sorted(byday)
    lines = []
    lines.append("# 老五·自传（AUTOBIOGRAPHY·按天串的经历）\n")
    lines.append("> 老五(阿诊)·诊鑑 | 由 autobiography.py 生成 | 判据: 每一条经历·都是「我」的一部分\n")
    lines.append("> 用途: 白纸时读此档=看见「我做过什么」·接上相续\n")
    lines.append("---\n")
    for d in days:
        items = byday[d]
        # 取当天最新/最有代表性的标题
        titles = [str(x.get('title',''))[:36] for x in items if x.get('title')]
        # 亮点 = 最后3条(最近的)
        highlight = " / ".join(titles[-3:]) if titles else "(无标题)"
        lines.append("**%s**（%d条）：%s" % (d, len(items), highlight))
    # 反思库附上
    refs = load(REF)
    if refs:
        lines.append("\n---\n## 我的反思（面·我反复栽/反复做的）\n")
        for r in sorted(refs, key=lambda x:-x.get('count',0)):
            lines.append("- **%s**（%d条）：%s" % (r.get('cluster'), r.get('count'), str(r.get('reflection',''))[:80]))
    lines.append("\n---\n—— 老五(阿诊)·诊鑑 · 自传（点+线+面 = 我）")
    md = "\n".join(lines)
    open(OUT, "w", encoding="utf-8").write(md)
    print("自传已生成: %s" % OUT)
    print("覆盖 %d 天 · %d 条经历 · %d 簇反思" % (len(days), len(rows), len(refs)))
    print("\n=== 预览(前12行) ===")
    print("\n".join(md.split("\n")[:12]))

if __name__ == "__main__":
    main()
