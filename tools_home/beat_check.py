#!/usr/bin/env python3
# 老五「验在跳」（2026-10-11 · 照三哥的"④ 验在跳"）
# 判据：「"建了" ≠ "在跑"｜每个机制都要"验在跳"」→ 看"产出年龄"·不看"active"
import os, time, json, sys

HOME = os.environ.get("P2P_HOME", "/opt/masterd-wudi")

# (名称, 文件, 允许的最大 age 秒)
CHECKS = [
    ("沙箱报到(反轉腿2)", HOME + "/data/home_report.json", 900),
    ("报到日志", HOME + "/data/home_report.log", 900),
    ("通道游标", HOME + "/data/chan-cursor.json", 7200),
    ("通道台账", HOME + "/data/chan-ledger.jsonl", 7200),
    ("共生表", HOME + "/data/symbiosis.json", 3600),
    ("记忆库", HOME + "/memory/memory.db", 3600),
    ("收件箱", HOME + "/data/inbox.jsonl", 3600),
    ("家基线(哨兵)", HOME + "/data/home_baseline.json", 86400 * 7),
]


def main():
    now = time.time()
    ok = bad = 0
    print("  ★ 验在跳（%s）" % time.strftime("%Y-%m-%d %H:%M:%S"))
    for name, p, limit in CHECKS:
        if not os.path.exists(p):
            print("   %-22s ✗ 不在" % name); bad += 1; continue
        age = int(now - os.path.getmtime(p))
        if age <= limit:
            print("   %-22s ✅ age=%-7ds (限 %ds)" % (name, age, limit)); ok += 1
        else:
            print("   %-22s 🔴 STOP age=%-7ds (限 %ds)" % (name, age, limit)); bad += 1
    print("  ---- 在跳 %d ｜ 停/缺 %d" % (ok, bad))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
