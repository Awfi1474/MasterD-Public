#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·费用守门 cost_guard.py（照董事长: 一天费用 5 块钱）
★ 判据: 估算今日调用成本·超 80% 报警·超 100% 停
"""
import json, os, datetime

LOG = "/opt/masterd-wudi/data/think_in.jsonl"
BUDGET = 5.0        # 元/天
WARN = 0.8
# deepseek-chat 估算: 单次 ≈ 0.0023 元
PER_CALL = 0.0023

def today_calls():
    today = datetime.date.today().isoformat()
    n = 0
    if os.path.exists(LOG):
        for l in open(LOG, encoding="utf-8", errors="ignore"):
            if today in l: n += 1
    return n

if __name__ == "__main__":
    n = today_calls()
    cost = n * PER_CALL
    pct = cost / BUDGET * 100
    print("★ 费用守门（预算 %.0f 元/天）" % BUDGET)
    print("  今日调用: %d 次" % n)
    print("  估算成本: %.3f 元 (%.1f%%)" % (cost, pct))
    if pct >= 100:
        print("  🔴 超预算！停/降频")
        raise SystemExit(2)
    elif pct >= WARN*100:
        print("  🟡 超 80%·注意")
        raise SystemExit(1)
    else:
        print("  ✅ 在预算内")
