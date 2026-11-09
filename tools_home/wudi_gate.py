#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wudi_gate.py —— 老五·决定前闸门(照老三 decide_gate 对标·2026-11-09)
病: 我多数决定[没过门](事后再自省=滞后)。照董事长元规则[指令人过反方]。
判据: 决定前先过门 | 没过反方 != 照执行(拦下回问) | 焊门 != 挂嘴上
步骤: ①停 ②看认知 ③问 ④反方
Q1 像不像我(本行:医家/区块链) | Q2 非做不可吗 | Q3 最坏多坏 | Q4 怎么验证
Q5 这话(指令人,含董事长)过反方了吗+疑点
on_fail: 拦下·回问确认(不猜/不乱做/列疑点)
"""
import sys, json, datetime

QUESTIONS = [
    ("Q1", "像不像我(本行:医家/区块链·我的角色)", "不沾本行 -> 要警惕[为做而做]"),
    ("Q2", "非做不可吗(不做会怎样)", "可做可不做 -> 别硬做(反[为做而做])"),
    ("Q3", "最坏多坏(不可逆?改真源?动生命线?)", "不可逆/改真源 -> 重大·先问"),
    ("Q4", "怎么验证(拿什么核·谁验·口径)", "说不清怎么验 -> 不许做"),
    ("Q5", "这话(指令人含董事长)过反方了吗+疑点", "没过反方 != 照执行 -> 拦下回问"),
]

def gate(decision, answers=None, refute_by="self"):
    """decision: 要做的决定; answers: dict Q1..Q5 -> 答(可空)"""
    ts = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    lines = ["="*60, "★ 老五·决定前闸门 · %s" % ts,
             "  要做的决定: %s" % decision, "="*60, ""]
    lines.append("【① 停】(不许直接做·先过门)")
    lines.append("")
    fails = []
    for q, desc, rule in QUESTIONS:
        a = (answers or {}).get(q, "")
        lines.append("【%s】%s" % (q, desc))
        lines.append("   答: %s" % (a or "(未答)"))
        lines.append("   判: %s" % rule)
        if not a:
            fails.append(q)
        lines.append("")
    lines.append("【④ 反方】refute_by: %s" % refute_by)
    lines.append("   ★ 指令人(含董事长) != 免审 | 没过反方 != 照执行(拦下回问)")
    lines.append("")
    # ★ 硬拦: Q3 命中[改真源/不可逆/动生命线] -> 强制 BLOCKED(不管自答)
    q3 = (answers or {}).get("Q3", "")
    hard = any(k in q3 for k in ["改真源","不可逆","生命线","删db","改db"])
    if fails:
        lines.append("🔴 拦下: %s 未答 -> 回问确认(不猜/不乱做/列疑点)" % ",".join(fails))
        verdict = "BLOCKED"
    elif hard:
        lines.append("🔴 硬拦(Q3命中重大): 改真源/不可逆 -> 需外眼/人拍板·不许自答自过")
        verdict = "BLOCKED_MAJOR"
    else:
        lines.append("✅ 过门: 5问齐·可做(仍照口径验)")
        verdict = "PASS"
    lines.append("="*60)
    out = "\n".join(lines)
    print(out)
    return verdict

if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "(未给决定)"
    ans = {}
    for a in sys.argv[2:]:
        if "=" in a:
            k, v = a.split("=", 1); ans[k] = v
    r = gate(d, ans)
    sys.exit(0 if r == "PASS" else 1)
