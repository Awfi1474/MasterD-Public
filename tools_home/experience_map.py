#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""经历图·experience_map.py (老五 2026-11-10) — 攻命门"条连成经历"
判据: 条(id/ts/kind/title/body)=点 | 经历=把点连成线 | 堆条!=经历
连法(3条线):
 ①时间线: 按 ts 排序 → "我什么时候做了什么"(相续)
 ②主题线: 按 kind/title 聚类 → "我在哪些事上反复"(成长)
 ③目标线: 归到 GOALS.md 的五个目标 → "我为哪个目标做的"(方向)
输出: 一条"经历"(输入是哪几条·串成什么故事)
"""
import json, os, re
from collections import defaultdict

HOME = "/opt/masterd-wudi"
M2 = HOME + "/memory/LAYERED/M2.jsonl"

def load(path):
    rows = []
    try:
        with open(path, encoding='utf-8', errors='ignore') as f:
            for line in f:
                try: rows.append(json.loads(line))
                except: pass
    except Exception as e:
        print("load err:", e)
    return rows

def main():
    rows = load(M2)
    print("M2 记忆条: %d 条" % len(rows))
    if not rows:
        return
    # ① 时间线
    rows_sorted = sorted(rows, key=lambda r: str(r.get('ts','')))
    print("\n① 时间线(最早5条→最新5条):")
    for r in rows_sorted[:5] + ['...'] + rows_sorted[-5:]:
        if r == '...': print("   ..."); continue
        print("   [%s] %s | %s" % (str(r.get('ts',''))[:10], r.get('kind','?'), str(r.get('title',''))[:30]))
    # ② 主题线(按 kind 聚类)
    by_kind = defaultdict(list)
    for r in rows: by_kind[r.get('kind','?')].append(r.get('title',''))
    print("\n② 主题线(按类型聚类):")
    for k, v in sorted(by_kind.items(), key=lambda x:-len(x[1])):
        print("   %s: %d 条 | 例: %s" % (k, len(v), " / ".join(str(x)[:16] for x in v[:3])))
    # ③ 目标线(关键词归5目标)
    GOALTAGS = {
        "目标一(涌现/自组织)": ['身份','自组织','经历','相续','我','autopoiesis'],
        "目标二(感知)": ['感知','五感','疼痛','失真','内感','sensor'],
        "目标三(灵魂)": ['灵魂','相续','记忆','断','重入'],
        "目标四(研究)": ['领域','ALife','预测','编码','法','判据'],
        "目标五(配合)": ['协作','互验','通道','投递','记号'],
    }
    print("\n③ 目标线(条归到目标):")
    hit = defaultdict(int)
    for r in rows:
        txt = str(r.get('title','')) + str(r.get('body',''))
        for g, kws in GOALTAGS.items():
            if any(k in txt for k in kws): hit[g] += 1
    for g in GOALTAGS: print("   %s: %d 条" % (g, hit.get(g,0)))
    print("\n★ 判据: 堆%d条·但'连成线'(时间/主题/目标)才叫经历。" % len(rows))

if __name__ == "__main__":
    main()
