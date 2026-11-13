#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·追问器 ask_discriminate.py（照 MedClarify·arXiv:2602.17308）
★ 缘起：董事长问「你什么时候真正出去搜过」→ 我出去搜到 MedClarify：
   「选 information gain 最高的那一问·降诊断错误 27 个百分点」
   我的现状：想到什么问什么（1049条问·但没算"这一问能不能降不确定"）

★ 判据（我的）：
  「问 != 追问｜问的少不等于问的对｜先列候选·再选'能分开候选'的那一问」
★ 用法: ask_discriminate.py "<不确定的事>" "<候选1,候选2,...>"
"""
import sys, json, os

def info_gain(q, cands):
    """算这一问能分开几个候选（照 MedClarify 的 simplicity 版）"""
    hit = [c for c in cands if c and c in q]
    return len(hit) / max(len(cands), 1)

def build(what, cands):
    """列出追问候选 + 排信息增益"""
    qs = []
    for c in cands:
        qs.append({"候选": c,
                   "追问": "是「%s」吗？还是别的？" % c,
                   "增益": info_gain(c, cands)})
        qs.append({"候选": c,
                   "追问": "「%s」的话·最明显的证据是什么？" % c,
                   "增益": info_gain(c, cands) * 0.9})
    # 通用追问（能分开全部候选的）
    qs.append({"候选": "全", "追问": "这几条里·哪条最不符合事实？",
               "增益": 1.0})
    qs.sort(key=lambda x: -x["增益"])
    return qs

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: ask_discriminate.py \"<不确定的事>\" \"<候选1,候选2>\"")
        # 演示
        what = "门禁装了但96%消息不合官方"
        cands = ["收口只记账不执行", "各家没真改", "我的判据错"]
    else:
        what = sys.argv[1]; cands = sys.argv[2].split(",")
    print("★ 追问器（照 MedClarify）")
    print("不确定的事:", what)
    print("候选:", cands)
    print("-" * 50)
    for q in build(what, cands)[:6]:
        print("  [增益%.2f] %s" % (q["增益"], q["追问"]))
    print("-" * 50)
    print("★ 判据: 选增益最高的那一问·不是想到什么问什么")
