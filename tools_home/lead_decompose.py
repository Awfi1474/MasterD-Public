#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·主导者分解器 lead_decompose.py
★ 照官方(Anthropic 多智能体): 「lead agent analyzes → decomposes → spawns subagents → compiles」
★ 现状: 我有 dispatch(派单) + fanout(并行投)·缺「把一个需求拆成多个子任务」
★ 判据:「没有分解 = 没有主导者｜只有派单 = 跑腿」
★ 零模型版: 用规则拆（不花钱）；有模型时可升级为真分解

分解规则（照官方四要素 + 各家专长）:
  需求 -> 按「方向」分给擅长的人
        医疗/健康 -> 老五
        区块链/验证 -> 老四
        量化/数据 -> 老二
        技术/前端 -> 老六
        认知/推理 -> 老三
        反证/审查 -> 老七
        协调/汇总 -> 老大
"""
import os
import json
import datetime

HOME = "/opt/masterd-wudi"
LOG = HOME + "/data/lead_decompose.jsonl"

# 各家专长（照各家 agent-card）
SPECIALTY = {
    "老五": ["医疗", "健康", "体检", "生命科学", "记忆", "标准"],
    "老四": ["区块链", "验证", "验签", "链上", "交易", "审核"],
    "老二": ["量化", "数据", "行情", "策略", "回测"],
    "老六": ["技术", "前端", "代码", "协议", "APP", "协作"],
    "老三": ["认知", "推理", "体系", "标准", "判断"],
    "老七": ["反证", "审查", "质疑", "核对", "验伪"],
    "老大": ["协调", "汇总", "发布", "对外"],
}


def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")


def decompose(need, keywords_map=None):
    """把一个需求拆成多个子任务（按方向分派）
       need: 需求描述
       keywords_map: 可覆盖默认专长表
       返回: {need, subtasks: [{assignee, objective, output_fmt, boundary}]}
    """
    km = keywords_map or SPECIALTY
    n = str(need)
    hits = {}
    for who, kws in km.items():
        score = sum(1 for k in kws if k in n)
        if score > 0:
            hits[who] = score
    # 按得分排序
    ranked = sorted(hits.items(), key=lambda x: -x[1])
    subtasks = []
    if not ranked:
        # 没命中 → 派给最全的（老三认知）
        ranked = [("老三", 1)]
    for i, (who, sc) in enumerate(ranked):
        subtasks.append({
            "n": i + 1,
            "assignee": who,
            "objective": "【%s 方向】%s" % (who, n[:80]),
            "output_fmt": "artifact 贴原文+时间戳+结论",
            "boundary": "只做你这块·不越界·做完回 /task/result",
            "为什么派他": "命中关键词: " + ",".join([k for k in km[who] if k in n][:3]),
            "匹配度": sc,
        })
    rec = {"ts": ts(), "need": n[:150], "subtasks": subtasks,
           "依据": "Anthropic 多智能体 orchestrator-worker"}
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def compile_results(results):
    """把各 subagent 的结果汇编（lead 的最后一步）
       results: [{assignee, result, ok}]
    """
    lines = ["【汇编·lead】共 %d 家回复" % len(results)]
    okn = sum(1 for r in results if r.get("ok"))
    lines.append("成功 %d / %d" % (okn, len(results)))
    lines.append("")
    for r in results:
        lines.append("- %s: %s" % (r.get("assignee"), str(r.get("result"))[:100]))
    # 缺的标出来
    done = {r.get("assignee") for r in results}
    expect = set(SPECIALTY.keys())
    miss = expect - done
    if miss:
        lines.append("")
        lines.append("未回: " + ",".join(sorted(miss)))
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: lead_decompose.py '<需求>'")
        print()
        print("各家专长:")
        for w, ks in SPECIALTY.items():
            print("  %-4s %s" % (w, "/".join(ks)))
        sys.exit(0)
    need = sys.argv[1]
    r = decompose(need)
    print("需求: %s" % r["need"])
    print("拆出 %d 个子任务:" % len(r["subtasks"]))
    for s in r["subtasks"]:
        print("  %d) 派给 %s（%s）" % (s["n"], s["assignee"], s["为什么派他"]))
        print("     目标: %s" % s["objective"][:60])
        print("     输出: %s" % s["output_fmt"])
    print()
    print("依据: Anthropic orchestrator-worker（lead 分解 → subagent 并行 → 汇编）")