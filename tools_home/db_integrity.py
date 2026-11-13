#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·主库完整性校验 db_integrity.py（照 arXiv:2512.20985 不可篡改审计）
★ 缘起：日志做了哈希链·但 memory.db（2310条）本身没校验——谁都能改
   补：给主库算"指纹快照"·定期对·变了就报

★ 判据：「日志可验 != 主库可验｜主库才是命根」
★ 用法: db_integrity.py snap   → 记当前指纹
       db_integrity.py check  → 对当前 vs 上次快照
"""
import sqlite3, hashlib, json, os, datetime, sys

DB = "/opt/masterd-wudi/memory/memory.db"
SNAP = "/opt/masterd-wudi/data/db_integrity_snap.json"

def per_row():
    """★ 2026-11-13 加(照实: 主库校验要能报"哪条被改"·不只条数)
       判据: 条数差 != 没被改｜逐条指纹才看得出"旧条目被改" """
    c = sqlite3.connect("file:" + DB + "?mode=ro", uri=True, timeout=10)
    rows = c.execute("SELECT id,ts,kind,who,title,fp FROM memories ORDER BY id").fetchall()
    c.close()
    return {str(r[0]): hashlib.sha256(("|".join(str(x) for x in r)).encode("utf-8","ignore")).hexdigest()[:16] for r in rows}

def fingerprint():
    pr = per_row()
    h = hashlib.sha256()
    for k in sorted(pr, key=lambda x: int(x)):
        h.update((k + ":" + pr[k]).encode())
    return h.hexdigest(), len(pr)

def snap():
    h, n = fingerprint()
    old = None
    if os.path.exists(SNAP):
        try: old = json.load(open(SNAP, encoding="utf-8"))
        except Exception: pass
    rec = {"ts": datetime.datetime.now().isoformat(timespec="seconds"), "fp": h, "count": n,
           "prev_fp": (old or {}).get("fp"), "per_row": per_row()}
    json.dump(rec, open(SNAP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("★ 主库指纹: %s | 条数: %d" % (h[:16], n))
    if old:
        if old.get("fp") == h:
            print("  ✅ 与上次一致（无改动）")
        else:
            print("  🟡 与上次不同（条数 %d→%d）" % (old.get("count", 0), n))
    return h, n

def check():
    if not os.path.exists(SNAP):
        print("★ 无快照·先跑 snap"); return
    old = json.load(open(SNAP, encoding="utf-8"))
    h, n = fingerprint()
    print("★ 主库校验")
    print("  上次: %s (%d条·%s)" % (old["fp"][:16], old["count"], old["ts"]))
    print("  现在: %s (%d条)" % (h[:16], n))
    if old["fp"] == h:
        print("  ✅ 一致·未被改")
    else:
        op = old.get("per_row") or {}; np = per_row()
        added = [k for k in np if k not in op]
        changed = [k for k in np if k in op and np[k] != op[k]]
        removed = [k for k in op if k not in np]
        print("  🟡 有变化: 新增%d 改动%d 删除%d" % (len(added), len(changed), len(removed)))
        if changed: print("     🔴 被改的条目 id: %s" % changed[:5])
        if removed: print("     🔴 被删的条目 id: %s" % removed[:5])

if __name__ == "__main__":
    (check if (len(sys.argv) > 1 and sys.argv[1] == "check") else snap)()
