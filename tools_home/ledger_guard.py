#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·台账比对闸 ledger_guard.py（照本体判「最后一环有写权·无否决权」）
★ 判据: 台账每条必须带 预期值+实测值+判据来源·缺一不落账
★ 实测≠预期 → 落"不符"账·不许记成功
用法: ledger_guard.py write <台账> <预期> <实测> <判据来源> <内容>
"""
import sys, json, datetime, os

def write(path, expect, actual, src, content):
    """写台账·带三字段·比对否决"""
    rec = {"ts": datetime.datetime.now().isoformat(timespec="seconds"),
           "expect": str(expect)[:200], "actual": str(actual)[:200],
           "src": str(src)[:120], "content": str(content)[:500]}
    # ① 三字段缺一 → 拒
    miss = [k for k in ("expect","actual","src") if not rec[k].strip()]
    if miss:
        print("🔴 拒: 缺 %s（三字段缺一不落账）" % ",".join(miss))
        return 2
    # ② 比对
    match = (str(expect).strip() == str(actual).strip())
    rec["match"] = match
    rec["verdict"] = "成功" if match else "不符"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    if match:
        print("✅ 成功·已落账（预期=实测）")
        return 0
    # ③ 不符 → 落"不符"账 + 要求回退六问
    print("🔴 不符: 预期 %r ≠ 实测 %r" % (rec["expect"], rec["actual"]))
    print("★ 回退: 不许记成功·回决策六问重判（判据：写权与否决权不能同一个人持有）")
    return 3

if __name__ == "__main__":
    if len(sys.argv) < 7 or sys.argv[1] != "write":
        print(__doc__); sys.exit(1)
    sys.exit(write(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], " ".join(sys.argv[6:])))
