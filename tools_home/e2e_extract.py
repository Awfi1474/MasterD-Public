#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 E2E 测试消息从 inbox 抽出 → 存成回归用例文件
★ 判据: 测试数据不许留在真实收件箱(污染读);但也不许直接删(丢了回归依据)
做法: 抽出 → 存 data/e2e_cases.jsonl → inbox 移除 → 两边都留账
"""
import json, io, os, datetime

HOME = "/opt/masterd-wudi"
INBOX = HOME + "/data/inbox.jsonl"
CASES = HOME + "/data/e2e_cases.jsonl"
LOG = HOME + "/data/e2e_extract_log.jsonl"

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")

def main(dry=True):
    lines = [l for l in open(INBOX, encoding="utf-8", errors="ignore") if l.strip()]
    keep, moved = [], []
    for l in lines:
        try:
            d = json.loads(l)
        except Exception:
            keep.append(l); continue
        b = d.get("c") if isinstance(d.get("c"), dict) else d
        who = str(b.get("from") or "")
        msg = str(b.get("message") or "")
        if who == "E2E测试器" or msg.startswith("TEST-NOISE"):
            moved.append(d)
        else:
            keep.append(l)

    # 三样证明
    proof = {
        "ts": ts(), "dry": dry,
        "输入": {"inbox总行": len(lines), "inbox字节": os.path.getsize(INBOX)},
        "算子": {"匹配规则": "from=='E2E测试器' or message.startswith('TEST-NOISE')",
                 "命中": len(moved)},
        "结果": {"移出": len(moved), "保留": len(keep)},
        "复跑": "python3 tools/e2e_extract.py --apply",
    }
    print(json.dumps(proof, ensure_ascii=False, indent=1))

    if not dry and moved:
        # 先存用例(先保后删·顺序不许反)
        with open(CASES, "a", encoding="utf-8") as f:
            for d in moved:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")
        # 再写回 inbox(只留非测试)
        io.open(INBOX, "w", encoding="utf-8").write("".join(keep))
        # 验证: 重跑计数
        after = sum(1 for l in open(INBOX, encoding="utf-8", errors="ignore")
                    if l.strip() and ("E2E测试器" in l or "TEST-NOISE" in l))
        proof["验证"] = {"重跑残留": after, "通过": after == 0,
                         "inbox新行数": sum(1 for _ in open(INBOX, encoding="utf-8", errors="ignore")),
                         "用例文件行数": sum(1 for _ in open(CASES, encoding="utf-8", errors="ignore"))}
        print("验证:", json.dumps(proof["验证"], ensure_ascii=False))
    open(LOG, "a", encoding="utf-8").write(json.dumps(proof, ensure_ascii=False) + "\n")
    return proof

if __name__ == "__main__":
    import sys
    main(dry="--apply" not in sys.argv)