#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·销未回 mark_replied.py（照老三"回执没写=算没读"）
★ 读到+回过 → 标 REPLIED
用法: mark_replied.py <from关键字> [备注]
"""
import json, sys, datetime

F = "/opt/masterd-wudi/data/hub_unreplied.jsonl"

def mark(key, note=""):
    if not key: print("要 from 关键字"); return
    rows = []
    n = 0
    for l in open(F, encoding="utf-8", errors="ignore"):
        if not l.strip(): continue
        try: d = json.loads(l)
        except Exception: continue
        if key in str(d.get("from","")) and d.get("state") != "REPLIED":
            d["state"] = "REPLIED"; d["replied_at"] = datetime.datetime.now().isoformat(timespec="seconds")
            if note: d["note"] = note[:80]
            n += 1
        rows.append(d)
    with open(F, "w", encoding="utf-8") as f:
        for d in rows: f.write(json.dumps(d, ensure_ascii=False) + "\n")
    print("✅ 标 REPLIED %d 条 (from 含 %r)" % (n, key))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # 默认: 把已回过执的都销掉
        mark("老七", "已回: 读到LOOP-TEST-0140/最小闭环回执")
        mark("老三", "已回: read=true 60/60 + 二级回执 + owner补齐")
    else:
        mark(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "")
