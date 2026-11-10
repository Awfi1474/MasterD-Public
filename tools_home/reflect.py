#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""反思器·reflect.py (老五 2026-11-10) — 攻命门(条连成经历·第2步)
判据(照arXiv 2304.03442 Generative Agents): ②存经历 → ②合成反思 → ③检索
我的病: 1549条=散点·"我"不成。缺"反思"(把条→更高层理解)。
做法(不调LLM·先做"机械反思"·可核):
 1. 按【主题/目标】聚一批条
 2. 每簇=一条"反思"(这批条·共同讲的是啥·我的结论)
 3. 输出: 反思库(reflections.jsonl) — 比"条"高一层的"面"
"""
import json, os, re
from collections import defaultdict

HOME = "/opt/masterd-wudi"
M2 = HOME + "/memory/LAYERED/M2.jsonl"
OUT = HOME + "/memory/REFLECTIONS.jsonl"

# 反思簇(主题 → 关键词)。每簇=一条"更高层理解"
CLUSTERS = {
    "假象病(以为vs实测)": ['假绿','假成功','假送','假醒','假亮','自称','以为','回显','存在'],
    "依赖/机制病":        ['依赖','机制','timer','挂','断','缺件','import','恢复','备份'],
    "身份病":             ['身份','漂移','一名','命名','名不统一','轴','职守'],
    "记忆病":             ['记忆','相续','断','空白','覆盖','消化','学而'],
    "跨家/通道病":        ['通道','投递','口','收','发','对账','栓','送','known'],
    "判据/方法":          ['判据','方法','标准','规矩','铁律','原则'],
}

def load(path):
    rows = []
    with open(path, encoding='utf-8', errors='ignore') as f:
        for l in f:
            try: rows.append(json.loads(l))
            except: pass
    return rows

def main():
    rows = load(M2)
    print("读入条: %d" % len(rows))
    # 归簇
    buckets = defaultdict(list)
    for r in rows:
        txt = str(r.get('title','')) + str(r.get('body',''))
        for c, kws in CLUSTERS.items():
            if any(k in txt for k in kws):
                buckets[c].append((r.get('ts',''), str(r.get('title',''))[:40]))
    # 每簇=一条反思
    reflections = []
    for c, items in buckets.items():
        if not items: continue
        # 反思 = 该簇条数 + 时间跨度 + 几条样本
        items_sorted = sorted(items)
        span = "%s..%s" % (str(items_sorted[0][0])[:10], str(items_sorted[-1][0])[:10])
        sample = " / ".join(t for _,t in items_sorted[-3:])
        reflections.append({
            "cluster": c, "count": len(items), "span": span,
            "reflection": "【%s】我在%d条里反复栽/反复做。最近: %s" % (c, len(items), sample),
            "kind": "reflection"
        })
    # 排序·输出
    reflections.sort(key=lambda x:-x["count"])
    with open(OUT, 'w', encoding='utf-8') as f:
        for r in reflections: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("\n=== 反思库(条→面) ===")
    for r in reflections:
        print("  [%d条] %s" % (r["count"], r["reflection"][:90]))
    print("\n★ 反思: %d 簇(面) ← 由 %d 条(点) 合成" % (len(reflections), len(rows)))
    print("  判据: 点→面 = 反思。'我'=点(条)+线(经历图)+面(反思)的涌现。")

if __name__ == "__main__":
    main()
