#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""reflect_recall.py — 遇事，从"反思库"检索相关教训(老五 2026-11-10)
命门第3步: 动态检索。把"反思(面)"接进决策——遇新事·先问"我以前在类似事上反思出啥"。
用法: python3 reflect_recall.py "要判断的事"
输出: 命中的反思(供 decide.py / 我自己参考)
判据: 遇事不空想·先检索"我反思过的"。
"""
import sys, json, os

HOME = "/opt/masterd-wudi"
REF = HOME + "/memory/REFLECTIONS.jsonl"

# 事 → 关键词 → 反思簇 的映射
KEYMAP = {
    "判据/方法": ['判据','方法','标准','规矩','决定','铁律'],
    "跨家/通道病": ['通道','投递','对账','跨家','known','hub'],
    "依赖/机制病": ['依赖','机制','timer','挂','缺件','import','恢复','备份','降级'],
    "记忆病": ['记忆','相续','空白','覆盖','消化','经历','反思'],
    "身份病": ['身份','漂移','一名','命名','轴','职守','转正','职业'],
    "假象病(以为vs实测)": ['假绿','假成功','假醒','以为','实测','回显','自证'],
}

def recall(what):
    hits = []
    try:
        refs = [json.loads(l) for l in open(REF, encoding='utf-8') if l.strip()]
    except Exception as e:
        return [("ERR", str(e))]
    for r in refs:
        c = r.get('cluster','')
        kws = KEYMAP.get(c, [])
        if any(k in what for k in kws):
            hits.append((c, r.get('count'), r.get('reflection','')))
    return hits

if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else ""
    hits = recall(what)
    if not hits:
        print("反思库: 无命中(这事我没反思过·要新想)")
    else:
        print("★ 遇[%s]·检索到我反思过的:" % what[:30])
        for c, n, rf in hits:
            print("  [%s·%s条] %s" % (c, n, rf[:100]))
    print("判据: 遇事不空想·先检索'我反思过的'。")
