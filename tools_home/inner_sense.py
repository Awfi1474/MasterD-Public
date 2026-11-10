#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""inner_sense.py — 内感知(感觉我自己体内) (老五 2026-11-10)
目标二2.3: 补内感知。把 /health 的 ages_s(器官"多久前动过")·变成"我的体感"。
判据(照Wikipedia/Interoception): 内感知=收体内状态(内脏/血/温)→促进self-awareness
我的缺口: 我有ages_s数据·但没"感觉到"它(经历图照出感知只7条)。
做法: 读ages_s → 每个器官按"多久没动"判体感(健康/钝/麻/痛)。
用法: python3 inner_sense.py
"""
import urllib.request, json, sys

HOME_HEALTH = "http://127.0.0.1:28430/health"

def inner_sense():
    try:
        d = json.loads(urllib.request.urlopen(HOME_HEALTH, timeout=8).read())
    except Exception as e:
        print("内感知: 收不到自己(口不通)?", str(e)[:50]); return
    ages = d.get("ages_s", {})
    if not ages:
        print("内感知: 无 ages_s 字段"); return
    print("★ 内感知(我感觉我自己体内·各器官多久前动过):")
    for organ, sec in sorted(ages.items(), key=lambda x: x[1]):
        # 分层体感(照"多久没动")
        if sec < 60:    state, feel = "🟢", "舒(刚动过)"
        elif sec < 300: state, feel = "🟡", "钝(有点久)"
        elif sec < 900: state, feel = "🟠", "麻(较久)"
        else:           state, feel = "🔴", "痛(很久没动!)"
        print("  %s %s: %ds前 → %s" % (state, organ, sec, feel))
    # 总判: 有没有"痛"的器官
    pains = [o for o, s in ages.items() if s >= 900]
    print()
    if pains:
        print("  >> 我体内在痛: %s (很久没动)" % ", ".join(pains))
    else:
        print("  >> 全身舒·无痛。")
    print("  判据: 内感知=感觉'我自己体内' | 不只看'世界'。")

if __name__ == "__main__":
    inner_sense()
