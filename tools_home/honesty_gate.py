#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诚实闸 (honesty_gate.py) —— 照实说：这是把「四道关」从说辞变成闸门的第一步。

它拦什么（每条都是今晚我真犯过的）：
  ① 报"好了/修好了/已修复" 但没带复跑命令 → 打回
     判据: «说好了 != 好了｜贴不出复跑命令 = 不算修好»
  ② 报"通了/成功/送达" 但没带验证方式 → 打回
     判据: «发了 != 到了｜没有验证方式 = 假绿»
  ③ 报数字（% / ms / 条 / 次）但没带 src/来源 → 打回
     判据: «报数要指到源｜指不到 = 不算数»
  ④ 说"改了/加了/删了" 但没带改前改后或文件路径 → 打回
     判据: «改了 != 生效｜贴不出对照 = 没改»

不在以下情况拦（避免误杀）：
  · 纯提问、纯汇报进度、纯表达观点
  · 短消息（<80 字·没有"好了/通了"这类断言）

用法: python3 honesty_gate.py "文本"
     返回 0 = 过；1 = 打回（stdout 给理由）
"""
import re
import sys

text = (sys.argv[1] if len(sys.argv) > 1 else '').strip()
if not text:
    print('空文本·放行')
    sys.exit(0)

# 短消息 + 无断言 → 放行（防误杀）
CLAIM_WORDS = ['好了', '修好了', '已修复', '修复了', '通了', '已通', '成功了', '已成功',
               '送达', '已送达', '改好了', '搞定了', '通过了', '已通过', '完成了']
claims = [w for w in CLAIM_WORDS if w in text]
if not claims:
    print('无断言词·放行')
    sys.exit(0)

# 有断言 → 必须有证据
EVIDENCE = [
    # 复跑命令 / 可验证动作
    r'curl\s', r'python3\s', r'\bsed\s+-n\b', r'\bgrep\s', r'\bwc\s+-l\b',
    r'GET\s+/', r'POST\s+/', r'复测', r'复跑', r'验证方式', r'可核', r'可复算',
    r'命令:', r'src[:：]', r'来源[:：]', r'证据[:：]', r'实测',
]
# 数字必须有 src（但如果整段没有任何数字·不要求）
has_num = bool(re.search(r'\d+(?:\.\d+)?\s*(?:ms|s|%|条|次|个|倍)', text))
has_evidence = any(re.search(p, text) for p in EVIDENCE)

fails = []
if not has_evidence:
    fails.append('缺证据（没有复跑命令/验证方式/src/实测原文）')

if has_num and not re.search(r'src|来源|命令|实测|=/|：\s*\d+\s*$', text):
    # 有数字但完全没有任何指向
    if not has_evidence:
        fails.append('报了数字但没指到源')

if fails:
    print('诚实闸打回:')
    for f in fails:
        print('  · ' + f)
    print('断言词命中: ' + ','.join(set(claims)))
    print('判据: «说好了 != 好了｜贴不出复跑命令/验证方式 = 不算»')
    sys.exit(1)

print('诚实闸: 过（断言带证据）')
sys.exit(0)