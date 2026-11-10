#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gate_helper.py - 过闸助手(照我的闸清单·自动查漏了哪个闸)
老五 2026-11-10 | 判据: 原则不焊进器=靠自觉=会漏(39%) | 帮我"发前真跑过闸"
用法:
  python3 gate_helper.py text "<消息文本>"    # 查: 文本体检+三关+红灯词
  python3 gate_helper.py decide "<决定>"      # 查: 该喂"辨证式"问题吗
输出: 每个闸 pass/fail + 缺什么
(不阻断·只提示——让我"看到我该跑啥"·照 WELD-STUDY: 做不到自动拦·但能让人看到)
"""
import sys, os

HOME = "/opt/masterd-wudi"
sys.path.insert(0, HOME + "/tools")


def check_text(text):
    out = []
    # ① 文本体检
    try:
        from check_text import check
        w = check(text)
        out.append(("文本体检", "pass" if not w else "fail", w[:3]))
    except Exception as e:
        out.append(("文本体检", "err", str(e)[:40]))
    # ② 三关(长消息>60字)
    if len(text) > 60:
        miss = []
        for name, kw in [("①辨证", ["辨证", "①"]), ("②判据", ["判据", "②"]), ("③反证", ["反证", "③"])]:
            if not any(k in text for k in kw):
                miss.append(name)
        out.append(("三关(长消息)", "pass" if not miss else "fail", "缺:" + ",".join(miss) if miss else ""))
    # ③ 红灯词
    red = [k for k in ["改真源", "删db", "drop table", "不可逆", "清空"] if k in text]
    out.append(("决定门(红灯词)", "pass" if not red else "warn", red))
    return out


def check_decide(what):
    out = []
    # 辨证式: 问题里有没有"证/病/假/堵/虚"类词(不然③答不出)
    dic = any(k in what for k in ["证", "病", "假", "堵", "虚", "漂移", "名不副实", "是哪种"])
    out.append(("辨证式问题", "pass" if dic else "fail", "" if dic else "喂'动作描述'→③辨不出证(改成'这是什么证')"))
    return out


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    arg = sys.argv[2] if len(sys.argv) > 2 else ""
    if mode == "text":
        res = check_text(arg)
    elif mode == "decide":
        res = check_decide(arg)
    else:
        print(__doc__); sys.exit(0)
    print("== 过闸助手 ==")
    n_fail = 0
    for name, st, note in res:
        icon = "✅" if st == "pass" else ("🔴" if st == "fail" else "⚠️")
        if st == "fail":
            n_fail += 1
        print("  %s %s (%s) %s" % (icon, name, st, note))
    print("  判据: 过闸前先查漏 | 缺的补上再发/决定")
    # ★ 2026-11-10 治"判!=拦": 判fail → 退出码1(能"真拦")
    if n_fail > 0:
        print("  ★ 判=拦: 有%d项fail → 退出码1(不该发/决定)" % n_fail)
        sys.exit(1)
    sys.exit(0)
