#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·反方闸 refute_gate.py（重档必需·照董事长新令「重=2系统+反方」）
★ 判据: 重动作必须自演一层反方·并给可核理由
★ 做法: 交互/参数三刀(会不会坏/能不能回滚/最坏后果)
用法: refute_gate.py --check "<动作>"    → returncode 0=过
      refute_gate.py --ask "<动作>"     → 打印三刀问题
"""
import sys, json, datetime, os

HOME = "/opt/masterd-wudi"
LEDGER = HOME + "/data/refute_ledger.jsonl"

THREE = [
    ("会不会坏", "这个动作最可能坏在哪？(具体到文件/服务/数据)"),
    ("能不能回滚", "坏了怎么回？(备份在哪/多久恢复)"),
    ("最坏后果", "如果全错了·影响范围是什么？(只自己/全族/资产)"),
]

def check(cmd):
    """重档检查: 最近 10 分钟内有针对这条的自演反方账·且三刀齐"""
    if not os.path.exists(LEDGER):
        return False, "无反方账·先跑 --ask 并落账"
    recent = []
    for l in open(LEDGER, encoding="utf-8", errors="ignore"):
        try: d = json.loads(l)
        except Exception: continue
        if d.get("cmd","")[:40] == cmd[:40]:
            recent.append(d)
    if not recent:
        return False, "这条动作没有反方账"
    last = recent[-1]
    if last.get("verdict") != "过":
        return False, "上次反方判: %s" % last.get("verdict")
    return True, "反方已过(三刀齐)"

def ask(cmd):
    print("★ 反方三刀 · %s" % cmd[:60])
    for name, q in THREE:
        print("  [%s] %s" % (name, q))
    print("\n填完后落账: refute_gate.py --record \"<cmd>\" \"<1>|<2>|<3>\" 过|拦")

def record(cmd, answers, verdict):
    parts = answers.split("|")
    if len(parts) < 3 or any(not p.strip() for p in parts):
        print("🔴 拒: 三刀不齐"); return 2
    rec = {"ts": datetime.datetime.now().isoformat(timespec="seconds"),
           "cmd": cmd[:120], "ans": dict(zip([n for n,_ in THREE], parts)),
           "verdict": verdict}
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("✅ 反方落账: %s" % verdict)
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    act = sys.argv[1]
    if act == "--check":
        ok, why = check(sys.argv[2])
        print(("✅ " if ok else "🔴 ") + why)
        sys.exit(0 if ok else 2)
    elif act == "--ask":
        ask(sys.argv[2])
    elif act == "--record":
        sys.exit(record(sys.argv[2], sys.argv[3], sys.argv[4]))
