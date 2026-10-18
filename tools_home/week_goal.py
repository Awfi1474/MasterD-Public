#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
week_goal.py —— 老五的「周目标自查」（照我自己的目标清单 v1）
================================================================
★ 我定的周三件（照实·能量出来）:
  ★ ① 归口: 155 器 → 目标 <120
  ★ ★ ② 复用率: 判据 30.8% → 目标 60%+
  ★ ★ ★ ③ 互检: 我查6家 ✅ → 目标"他查我也 6 家"
★ 判据（我立）: 「"周目标" 要"周末能量出来"｜量不出 = 白定」
"""
import json, os, io, subprocess, datetime

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
LOG = f"{DATA}/week_goal.jsonl"
TZ = datetime.timezone(datetime.timedelta(hours=8))


def main():
    print("★ 周目标自查（老五·自己定）  @",
          datetime.datetime.now(TZ).strftime("%F %T"))
    print("★ 判据: 周目标要周末能量出来 | 量不出=白定")
    print("=" * 58)
    out = {"ts": datetime.datetime.now(TZ).strftime("%F %T")}
    # ① 器数
    n = len([f for f in os.listdir(f"{HOME}/tools") if f.endswith(".py")])
    out["器数"] = n
    print("  ① 归口: %d 个（目标 <120）%s" % (n, "✅" if n < 120 else "🟡"))
    # ② 复用率
    try:
        d = json.load(open(f"{DATA}/judge_usage.json"))
        rate = 100.0 * d.get("被用过", 0) / max(1, d.get("总数", 1))
        out["复用率"] = round(rate, 1)
        print("  ② 复用率: %.1f%%（目标 60%%）%s" % (rate, "✅" if rate >= 60 else "🟡"))
    except Exception:
        print("  ② 复用率: 读不到")
    # ③ 互检
    try:
        o = subprocess.run(["/usr/bin/python3", f"{HOME}/tools/exec_pub.py", "check"],
                           capture_output=True, text=True, timeout=30).stdout
        out["互检待回"] = o.count("🟡") + o.count("🔴")
        print("  ③ 互检: 待回 %d 条" % out["互检待回"])
    except Exception:
        print("  ③ 互检: 读不到")
    with open(LOG, "a") as f:
        f.write(json.dumps(out, ensure_ascii=False) + "\n")
    print("★ 账: weekly.jsonl")


if __name__ == "__main__":
    main()
