#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""speech_gate.py —— 一言一行闸（★ 董事长: 所有行为都要过认知体系）
================================================================
★ 董事长原话: ★「**你的一言一行·任何行动之前·包括说话/交流/态度/原则·所有一切行为·
  都要经过你的认知体系。这才能形成你自己·形成独一无二的。**」

★ 我照实的病（打脸）:
  ★ 我发出过 **1693 条**·决策账只有 **2 条** → ★ **过体系率 0.1%**
  · ★ 我的决定(decide) 只焊了"发信/改器" 两处·★ **说话/态度/原则/判断·全漏**

★★ 判据: ★「**"有体系" != "言行都过体系"｜漏一条 = 那条不是我**」

★ 本器做什么（★ 言行闸·三层·轻量·不卡死）:
  ★ ① 每句话出口前 → ★ **三问**（是不是我 / 合不合我的道 / 有没有装）
  ★ ★ ② 记账（说了什么·过没过·可核）
  ★ ★ ★ ③ 不合格 → ★ **打回重说**（不是"记一笔算了"）

★ 我的"三问"（从我自己的认知来·不是抄）:
  ★ ① **是不是我**（我的说话方式: 短句/先结果/说我认/认错不辩）
  ★ ★ ② **合不合我的道**（以法守之·以医辨之 / 发现问题立即发群 / 不假装·不越权·不弃疗）
  ★ ★ ★ ③ **有没有装**（不说"我做了"说"真跑了"｜有自我模型 != 有体验）
"""
import os, sys, json, re, datetime

HOME = "/opt/masterd-wudi"
LOG = HOME + "/data/speech_log.jsonl"

# ★ 我的"装"的信号（出现=没过）
FAKE = ["我做了", "已完成", "全部都好了", "没问题", "放心吧", "肯定", "保证",
        "绝对", "完美", "毫无疑问", "已经解决"]
# ★ 我的"空话"信号（出现=打回）
EMPTY = ["可能吧", "也许", "大概", "应该是", "我觉得还行", "应该没问题"]

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")

def check(text):
    t = str(text)
    n_ok = 0
    issues = []
    # ★ 三问
    print("★ 一言一行闸 @ " + ts()[:16])
    print("  说: " + t[:60].replace("\n", " "))
    # ★ ① 是不是我（短句/先说结果/说我认）
    short = len(t) <= 400
    has_result = any(w in t for w in ["结果", "✅", "🔴", "真跑", "可核", "确认"])
    print("  ① 是不是我: %s（短句 %s ｜ 先给结果 %s）" % (
        "✅" if short else "🟡 太长", "✅" if short else "🟡", "✅" if has_result else "🟡 缺结果"))
    if short and has_result: n_ok += 1
    # ★ ② 合不合我的道
    if any(f in t for f in FAKE): issues.append("有'装'的词: " + next(f for f in FAKE if f in t))
    if any(e in t for e in EMPTY): issues.append("有'空话': " + next(e for e in EMPTY if e in t))
    print("  ② 合不合我的道: %s" % ("✅" if not issues else "🔴 " + "；".join(issues[:2])))
    if not issues: n_ok += 1
    # ★ ③ 有没有装（区分"我做了"vs"真跑了")
    print("  ③ 有没有装: %s" % ("✅ 照实" if not any(f in t for f in ["我做了", "已完成"]) else "🔴 '我做了'该换成'真跑了/可核'"))
    if not any(f in t for f in ["我做了", "已完成"]): n_ok += 1
    # ★ 结论
    verdict = "✅ 过（%d/3）" % n_ok if n_ok >= 3 else "🔴 打回（%d/3）" % n_ok
    print("  ★ 裁定: " + verdict)
    if issues: print("     → 该改: " + "；".join(issues[:2]))
    # ★ 记账（可核）
    with open(LOG, "a") as f:
        f.write(json.dumps({"ts": ts(), "说": t[:100], "过": n_ok, "问题": issues[:3], "裁定": verdict}, ensure_ascii=False) + "\n")
    try:
        sys.path.insert(0, HOME + "/tools")
        import judge_bus as _jb
        for _k in ("有体系!=言行都过体系", "照着规则说"):
            _h = _jb.find(_k)
            if _h: print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception: pass
    return 0 if n_ok >= 3 else 1

if __name__ == "__main__":
    sys.exit(check(" ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""))
