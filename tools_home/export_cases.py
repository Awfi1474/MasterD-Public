#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 memory.db 里的 case 类导出成 cases/CASES.jsonl —— 照 LAYERS_SPEC 的 must_have"""
import sqlite3, json, os

db = "/opt/masterd-wudi/memory/memory.db"
outdir = "/opt/masterd-wudi/cases"
os.makedirs(outdir, exist_ok=True)
out = os.path.join(outdir, "CASES.jsonl")

con = sqlite3.connect(db); con.row_factory = sqlite3.Row
rows = con.execute("SELECT * FROM memories WHERE kind='case' ORDER BY id").fetchall()

cols = rows[0].keys() if rows else []
with open(out, "w", encoding="utf-8") as f:
    for r in rows:
        d = {k: r[k] for k in cols}
        f.write(json.dumps(d, ensure_ascii=False) + "\n")

print("★ 导出 %d 条 case → %s" % (len(rows), out))
print("  大小: %d bytes" % os.path.getsize(out))
print()
print("══ 前 3 条标题 ══")
for r in rows[:3]:
    print("  #%s %s" % (r["id"], (r["title"] or "")[:60]))
print()
print("══ 最后 3 条 ══")
for r in rows[-3:]:
    print("  #%s %s" % (r["id"], (r["title"] or "")[:60]))
