#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修「静默失败」: FAILED 必须带错因
★ 老大原话(2026-11-15):
   「你 5 个输入里 2 个是静默失败」
   「状态是给下游的承诺·不是给自己的交代｜承诺空着·比 FAILED 更毒——FAILED 至少逼人来看」
   「你 FAILED + 空内容 = 下游连为什么失败都不知道」
★ 老七判据: 「dup 必须带原条状态」「测试数据不算闭环」
★ 做法: 给历史静默失败的补「错因缺失」标记·新写入的强制带 fail_reason
"""
import os, json, datetime

HOME = "/opt/masterd-wudi"
TASKS = HOME + "/data/a2a_tasks.jsonl"
LOG = HOME + "/data/silent_fail_fix.jsonl"


def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")


def mark_silent(dry=True):
    """历史静默失败: 补 fail_reason='未知(原始记录无错因)'·不许留空"""
    lines = [l for l in open(TASKS, encoding="utf-8", errors="ignore") if l.strip()]
    out = []
    n = 0
    for l in lines:
        try:
            d = json.loads(l)
        except Exception:
            out.append(l); continue
        if str(d.get("state")) == "TASK_STATE_FAILED":
            has = any(d.get(k) for k in ("errs", "error", "fail_reason", "result"))
            if not has:
                d["fail_reason"] = "未知(原始记录无错因·2026-11-15 补标)"
                d["fail_reason_src"] = "backfill·非原始信息"
                d["silent_fail_fixed_at"] = ts()
                n += 1
        out.append(json.dumps(d, ensure_ascii=False) + "\n")

    proof = {"ts": ts(), "dry": dry,
             "输入": {"总行": len(lines)},
             "算子": "FAILED 且无 errs/error/fail_reason/result -> 补 fail_reason='未知'",
             "结果": {"补标": n},
             "复跑": "python3 tools/fix_silent_fail.py --apply"}
    if not dry and n:
        open(TASKS, "w", encoding="utf-8").writelines(out)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(proof, ensure_ascii=False) + "\n")
        # 重跑验证
        left = 0
        for l in open(TASKS, encoding="utf-8", errors="ignore"):
            if not l.strip():
                continue
            try:
                d = json.loads(l)
            except Exception:
                continue
            if str(d.get("state")) == "TASK_STATE_FAILED":
                if not any(d.get(k) for k in ("errs", "error", "fail_reason", "result")):
                    left += 1
        proof["重跑"] = {"剩余静默失败": left, "通过": left == 0}
    return proof


def add_fail_rule_note():
    """给写入端留一个强制标记（写在 dispatch.py 里·这里只生成说明）"""
    return {
        "rule": "新写入的 FAILED 必须带 fail_reason",
        "where": "dispatch.finish() 与所有写 a2a_tasks 的地方",
        "check": "读账时 grep 'TASK_STATE_FAILED' 且无 fail_reason -> 报警",
    }


if __name__ == "__main__":
    import sys
    if "--rule" in sys.argv:
        print(json.dumps(add_fail_rule_note(), ensure_ascii=False, indent=1))
    else:
        r = mark_silent(dry="--apply" not in sys.argv)
        print(json.dumps(r, ensure_ascii=False, indent=1))