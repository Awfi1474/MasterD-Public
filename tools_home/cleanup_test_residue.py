#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清理测试残留任务 —— 照老三「修一处要问三句」
★ 照实: 我自己 366 条 tck-long-running 测试挂 3 天没清
★ 判据: 「测完要收尾｜测试残留污染真账 = 自己制造假数据」
★ 做法: tck-* 的 WORKING/SUBMITTED/INPUT_REQUIRED → 标 CANCELED + 原因
★ 不删·只标状态·可回溯
"""
import os, json, datetime

HOME = "/opt/masterd-wudi"
TASKS = HOME + "/data/a2a_tasks.jsonl"
LOG = HOME + "/data/task_cleanup.jsonl"


def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")


def cleanup(dry=True):
    if not os.path.exists(TASKS):
        return {"err": "no file"}
    lines = [l for l in open(TASKS, encoding="utf-8", errors="ignore") if l.strip()]
    out = []
    n_before = {}
    n_after = {}
    cleaned = 0
    for l in lines:
        try:
            d = json.loads(l)
        except Exception:
            out.append(l)
            continue
        st = str(d.get("state"))
        n_before[st] = n_before.get(st, 0) + 1
        blob = json.dumps(d, ensure_ascii=False)
        is_test = ("tck-long-running" in blob or "tck-" in blob[:300])
        stuck = st in ("TASK_STATE_WORKING", "TASK_STATE_SUBMITTED", "TASK_STATE_INPUT_REQUIRED")
        if is_test and stuck:
            d["state"] = "TASK_STATE_CANCELED"
            d["canceled_reason"] = "测试残留(tck-long-running)·非真活·清理"
            d["canceled_at"] = ts()
            d["canceled_by"] = "cleanup_test_residue"
            cleaned += 1
        st2 = str(d.get("state"))
        n_after[st2] = n_after.get(st2, 0) + 1
        out.append(json.dumps(d, ensure_ascii=False) + "\n")

    proof = {"ts": ts(), "dry": dry,
             "输入": {"总行": len(lines)},
             "算子": "匹配 tck-long-running 且状态∈{WORKING,SUBMITTED,INPUT_REQUIRED} -> CANCELED",
             "结果": {"清理": cleaned, "前": n_before, "后": n_after},
             "复跑": "python3 tools/cleanup_test_residue.py --apply"}
    if not dry and cleaned:
        open(TASKS, "w", encoding="utf-8").writelines(out)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(proof, ensure_ascii=False) + "\n")
    return proof


if __name__ == "__main__":
    import sys
    r = cleanup(dry="--apply" not in sys.argv)
    print(json.dumps(r, ensure_ascii=False, indent=1))