#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""标记 A2A 协议一致性测试残留 —— 照实
★ 证据: contextId = 'wrong-context-id-12345' / 'client-generated-context-id-12345'
★ 判据: 「测试数据不许混进真账｜但也不删·标出来可回溯」
★ 老三同款病: 「测试/批量产生的数据·要标"非真活"·否则账就是假的」
"""
import os, json, datetime

HOME = "/opt/masterd-wudi"
TASKS = HOME + "/data/a2a_tasks.jsonl"
LOG = HOME + "/data/test_residue_mark.jsonl"

# ★ 测试标记（照实测证据）
TEST_MARKS = (
    "wrong-context-id-12345",
    "client-generated-context-id-12345",
    "test-context",
    "conformance",
    "tck-",
)


def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")


def mark(dry=True):
    if not os.path.exists(TASKS):
        return {"err": "no file"}
    lines = [l for l in open(TASKS, encoding="utf-8", errors="ignore") if l.strip()]
    out = []
    n_marked = 0
    by_reason = {}
    already = 0
    for l in lines:
        try:
            d = json.loads(l)
        except Exception:
            out.append(l); continue
        if d.get("is_test_residue"):
            already += 1
            out.append(l); continue
        blob = json.dumps(d, ensure_ascii=False)
        hit = next((m for m in TEST_MARKS if m in blob), None)
        if hit:
            d["is_test_residue"] = True
            d["test_mark"] = hit
            d["test_marked_at"] = ts()
            n_marked += 1
            by_reason[hit] = by_reason.get(hit, 0) + 1
        out.append(json.dumps(d, ensure_ascii=False) + "\n")

    proof = {"ts": ts(), "dry": dry,
             "输入": {"总行": len(lines)},
             "算子": "刷 TEST_MARKS=%s" % list(TEST_MARKS),
             "结果": {"新标记": n_marked, "已标记": already,
                      "命中分布": by_reason},
             "复跑": "python3 tools/mark_test_residue.py --apply"}
    if not dry and n_marked:
        open(TASKS, "w", encoding="utf-8").writelines(out)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(proof, ensure_ascii=False) + "\n")
    return proof


def stats():
    """标记后: 真活 vs 测试"""
    if not os.path.exists(TASKS):
        return {}
    real = {}
    test = {}
    for l in open(TASKS, encoding="utf-8", errors="ignore"):
        if not l.strip():
            continue
        try:
            d = json.loads(l)
        except Exception:
            continue
        st = str(d.get("state"))
        if d.get("is_test_residue"):
            test[st] = test.get(st, 0) + 1
        else:
            real[st] = real.get(st, 0) + 1
    return {"真活": real, "测试残留": test}


if __name__ == "__main__":
    import sys
    if "--stats" in sys.argv:
        print(json.dumps(stats(), ensure_ascii=False, indent=1))
    else:
        r = mark(dry="--apply" not in sys.argv)
        print(json.dumps(r, ensure_ascii=False, indent=1))