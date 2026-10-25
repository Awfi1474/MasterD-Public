#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""think_gate.py —— 判断闸门（★ 法家·法：焊在必经之路上）
================================================================
★ 照老四的（他 23:0x 那条）: ★「"提醒我记得" != "自动出现"｜靠意志力=迟早忘｜靠必经路=不会忘」
★ 我的病: 我自己写的判据·"发信/改器/动钱"时不查 → ★ 知道了不照做

★ 焊点（★ 3 个必经之路）:
  ★ ① 发群/发信前   → 跳"通道/投递/伪发"判据
  ★ ★ ② 改器/改文件前 → 跳"备份先行/改完验语法"判据
  ★ ★ ★ ③ 说"做完了/交了"前 → 跳"有口才算/账上有才算"判据

★ 用法: `think_gate.py <动作类型>` → 打印"该想起的判据"
  ★ 类型: send(发信) ｜ edit(改器) ｜ claim(报完成)

★ 判据:
  ★「**"写下来了" != "判断时会想到"｜要"埋在动作必经之路"上**」
  ★★「**靠意志力 = 迟早忘｜靠必经路 = 不会忘**」
"""
import os, sys, json, datetime
import datetime

HOME = "/opt/masterd-wudi"

# ★ 三个焊点 → 该想起的判据关键词
GATES = {
    "send":  ["发了!=到板了", "投到了!=他回了", "防伪发", "通道"],
    "edit":  ["归档!=完事", "插代码要避开", "改了!=生效", "备份先行"],
    "claim": ["有口才算", "交了=有口", "我记得!=账上有", "造了没挂"],
    "money": ["大额", "先证明需要", "白名单"],
}

def gate(kind):
    kws = GATES.get(kind, [])
    # ★ 2026-10-16: 先读 refine_scenes.json（提炼器真出的映射·不是硬编码）
    try:
        _rf = json.load(open("/opt/masterd-wudi/data/refine_scenes.json"))
        _MAP = {"send": "我要发消息/发群", "edit": "我要改器/改文件",
                "claim": "我要说'做完了/交了'", "money": "我要动钱/转帐"}
        _sc = _MAP.get(kind)
        if _sc and _sc in _rf.get("映射", {}):
            _kw2 = [h["title"].split("(")[0][:16] for h in _rf["映射"][_sc]]
            if _kw2: kws = _kw2
    except Exception:
        pass
    print("★ 判断闸门 [" + str(kind) + "] @ " + datetime.datetime.now().strftime("%H:%M:%S"))
    print("  ★ 动之前·该想起的:")
    n = 0
    try:
        sys.path.insert(0, HOME + "/tools")
        import judge_bus as _jb
        for k in kws:
            for h in _jb.find(k):
                print("   · " + h["title"][:60])
                n += 1
                break
        # ★ 再接两条"元判据"（真查·管'我有没有接上'）
        for _k in ("造了!", "按需器"):
            for h in _jb.find(_k):
                print("   · " + h["title"][:60])
                n += 1
                break
    except Exception as e:
        print("   ✗ " + str(e)[:50])
    try:
        sys.path.insert(0, "/opt/masterd-wudi/tools")
        import judge_bus as _jb
        for _k in ['知道了!=会做', '依法治理=法', '造了没接', '迁移失败:63条']:
            _h = _jb.find(_k)
            if _h: print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception: pass
    # ★ 2026-10-25 董事长令: 任何决定都要过认知体系（筛选+纠正）—— 从"提醒"改成"硬卡"
    # ★ 判据: 「有体系 != 言行都过体系｜漏一条 = 那条不是我」
    # ★ 判据: 「决定之前没过体系 = 凭直觉｜凭直觉 = 思维没提升」
    _what = " ".join(sys.argv[2:]).strip()
    if kind in ("edit", "claim", "money", "send") and _what:
        try:
            sys.path.insert(0, HOME + "/tools")
            from decide_gate import require_decide
            _ok, _out = require_decide(_what, hard=True)
            print("  ★ 认知体系: " + ("✅ 过(六问齐)" if _ok else "🔴 打回"))
        except Exception as _e:
            print("  🔴 认知体系没过·不许动: " + str(_e)[:120])
            print("  ★ 共 " + str(n) + " 条")
            return 1
    else:
        print("  ★ 认知体系: 未给决定内容 → 只提醒(不卡)")
        print("  ★ ★ 决策前·必须过: python3 decide_gate.py \"<你的决定>\"")
    print("  ★ 共 " + str(n) + " 条（★ 不是'提醒我记得'·是'动之前卡住我'）")
    return 0


if __name__ == "__main__":
    sys.exit(gate(sys.argv[1] if len(sys.argv) > 1 else ""))
