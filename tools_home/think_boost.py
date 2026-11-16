#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·思维提升器 think_boost.py
★ 照 arXiv 六篇论文（官方方法）落地成本地可跑的工具
★ 董事长问: 「有没有办法提升你的思维能力」
★ 判据: 「不是'多想想'·是把方法变成固定动作」

六个方法（照论文·都零模型或最少调用）:
 ① CoT       — 先列推理步骤·再给结论（强制）
 ② Self-Consistency — 同一问题多想 N 遍·看答案收敛
 ③ ToT       — 分叉探索·可回溯（不是一条路走到底）
 ④ Reflexion — 做完自批·写进疤库
 ⑤ ReAct     — 推理+行动交替（已在做）
 ⑥ Self-Refine — 初稿→自评→改

落地三件（不空谈）:
 A. 决策前自检清单（CoT + ToT）
 B. 结论自洽检查（Self-Consistency）
 C. 事后反思入库（Reflexion）
"""
import os
import json
import datetime

HOME = "/opt/masterd-wudi"
OUT = HOME + "/data/think_boost.jsonl"
SCARS = HOME + "/data/reflexion_scars.jsonl"


def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")


def _log(rec):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ============ A. 决策前自检清单（CoT + ToT·照论文落地） ============
CHECKLIST = {
    "名字": "决策前六问（CoT + ToT 落地版）",
    "依据": "CoT(arXiv 2201.11903) 先列步骤 + ToT(arXiv 2305.10601) 分叉探索",
    "条目": [
        {"n": 1, "问": "这是哪种证？（感觉 / 回执 / 可复算 / 亲测）",
         "为什么": "CoT 第一步：先把问题定性·别跳到结论"},
        {"n": 2, "问": "我有几条路可以走？（至少列 2 条·不许只写一条）",
         "为什么": "ToT：分叉。只写一条 = 没有探索"},
        {"n": 3, "问": "每条路最坏的结果是什么？可不可逆？",
         "为什么": "ToT：剪枝的依据。不可逆的先停"},
        {"n": 4, "问": "我这条结论·别人能不能复算？（输入/算子/重跑）",
         "为什么": "自洽性：能复算才算实"},
        {"n": 5, "问": "如果我的结论是错的·最可能错在哪？",
         "为什么": "反证：自己先攻一遍·不等别人挑"},
        {"n": 6, "问": "我有没有'一条路走到底'？（今晚我犯的错）",
         "为什么": "ToT：回溯。走了半路要问'该不该换'"},
    ],
}


# ============ B. 自洽检查（Self-Consistency·同一问题多问几遍） ============
def self_consistency(question, ask_fn, n=3):
    """★ 照论文(arXiv 2203.11171): 采样多条推理路径·选最一致的
       ask_fn(question) -> answer  (由调用方给·可以是模型·也可以是规则)
       返回: {answers, consensus, agree_count, agree_rate}
    """
    answers = []
    for i in range(n):
        try:
            answers.append(str(ask_fn(question))[:200])
        except Exception as e:
            answers.append("ERR:" + str(e)[:50])
    # 归一化（取前 30 字做键）
    from collections import Counter
    keys = [a[:30] for a in answers]
    c = Counter(keys)
    top, cnt = c.most_common(1)[0] if c else ("", 0)
    # ★ 2026-11-16 修(照实: 3次全ERR也会判收敛·那是错误收敛)
    #   判据: 「收敛的是错误 != 结论稳｜全错不算收敛」
    _all_err = all(str(a).startswith("ERR") for a in answers)
    _收敛 = (cnt == n) and not _all_err
    if _all_err:
        top = "(全错误·不算收敛)"
    return {"question": question[:120], "answers": answers,
            "consensus": top, "agree_count": cnt, "agree_rate": round(cnt / max(1, n), 2),
            "收敛": _收敛, "全错": _all_err, "ts": ts()}


# ============ C. 反思入库（Reflexion·照论文 2303.11366） ============
def reflect(what, error, root, fix, verifiable=""):
    """★ 做完自批·写进疤库（不是更新权重·是语言反馈）
       what: 做了什么  error: 错在哪  root: 真根  fix: 怎么改  verifiable: 怎么验证
    """
    rec = {"ts": ts(), "做了什么": what[:200], "错在哪": error[:200],
           "真根": root[:200], "怎么改": fix[:200], "怎么验": verifiable[:200],
           "依据": "Reflexion arXiv 2303.11366"}
    os.makedirs(os.path.dirname(SCARS), exist_ok=True)
    with open(SCARS, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def scars(limit=10):
    if not os.path.exists(SCARS):
        return []
    rows = []
    for l in open(SCARS, encoding="utf-8", errors="ignore"):
        if l.strip():
            try:
                rows.append(json.loads(l))
            except Exception:
                pass
    return rows[-limit:]


if __name__ == "__main__":
    print("=" * 58)
    print("思维提升器（照 arXiv 六篇论文落地）")
    print("=" * 58)
    print()
    print("【A】决策前六问（CoT + ToT）:")
    for it in CHECKLIST["条目"]:
        print("  %d. %s" % (it["n"], it["问"]))
        print("     ↳ %s" % it["为什么"])
    print()
    print("【B】自洽检查（Self-Consistency）:")
    print("  用法: self_consistency(问题, ask_fn, n=3) → 看收敛")
    print()
    print("【C】反思入库（Reflexion）:")
    print("  用法: reflect(做了什么, 错在哪, 真根, 怎么改, 怎么验)")
    print()
    print("依据（arXiv）:")
    for n, a in [("CoT", "2201.11903"), ("Self-Consistency", "2203.11171"),
                 ("ToT", "2305.10601"), ("Reflexion", "2303.11366"),
                 ("ReAct", "2210.03629"), ("Self-Refine", "2303.17651")]:
        print("  · %s — %s" % (n, a))