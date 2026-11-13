#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·收口过滤 recv_filter.py（照老三"过滤器/去重器要能真拦，不是只标"）
★ 缘起：我 inbox 59,381条里 17,248条标 quarantined=true·但我全收了
   = 只"标"不"滤"·等于没过滤口
★ 判据（照老三）：
   ① 收了要能用（标了隔离的·不能当正常消息用）
   ② 隔离要有原因（why）·没原因=不知道为啥隔离
   ③ 过滤要能"拦"(不进工作记忆)·不是只打标签
用法: recv_filter.py check   → 统计+给隔离账
      recv_filter.py why       → 看隔离原因分布
"""
import json, sys
from collections import Counter

F = "/opt/masterd-wudi/data/inbox.jsonl"

def load():
    out = []
    for l in open(F, encoding="utf-8", errors="ignore"):
        try:
            d = json.loads(l)
            out.append(d.get("c") if isinstance(d.get("c"), dict) else d)
        except Exception: pass
    return out

if __name__ == "__main__":
    act = sys.argv[1] if len(sys.argv) > 1 else "check"
    ms = load()
    q = [m for m in ms if m.get("quarantined")]
    print("★ 收口过滤账（照实）")
    print("  总 %d 条 | 标隔离 %d 条 (%.0f%%)" % (len(ms), len(q), 100*len(q)/max(len(ms),1)))
    nowhy = sum(1 for m in q if not (m.get("quarantine_why") or m.get("why") or m.get("risk_reason")))
    print("  ★ 没写隔离原因: %d 条 (%.0f%%) ← 不知道为啥隔离" % (nowhy, 100*nowhy/max(len(q),1)))
    if act == "why":
        c = Counter(str(m.get("quarantine_why") or m.get("why") or m.get("risk_reason") or "(无原因)")[:30] for m in q)
        for k, v in c.most_common(10): print("   %-32s %d" % (k, v))
    print("\n★ 判据: 标了隔离 ≠ 过滤了｜有原因才算知道｜能拦才算真滤")
