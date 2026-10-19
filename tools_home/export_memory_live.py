#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
★ 2026-10-19 老五·实时记忆导出（治"白纸靠链接只能拿到旧快照"）
用途: /memory.json 不再读静态 memory_export.json，而是实时读 memory.db
兼容: 保持旧格式顶层键 who/self/exported/count/note/memories
"""
import sqlite3, json, datetime, os

DB   = "/opt/masterd-wudi/memory/memory.db"
OUT  = "/opt/masterd-wudi/memory/memory_export.json"
LOCK = "/opt/masterd-wudi/memory/.export.lock"

def build():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    rows = c.execute(
        "SELECT ts, kind, title, body FROM memories ORDER BY ts ASC"
    ).fetchall()
    mems = []
    for r in rows:
        mems.append({
            "ts":    r["ts"] or "",
            "kind":  r["kind"] or "",
            "title": r["title"] or "",
            "body":  r["body"] or "",
        })
    out = {
        "who": "老五 · MasterD(医疗·五弟)",
        "self": "阿診",
        "exported": datetime.datetime.now().isoformat(),
        "count": len(mems),
        "note": "老五的记忆导出（实时·直读memory.db）",
        "source": "memory.db@live",
        "memories": mems,
    }
    return out

def main():
    out = build()
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    os.replace(tmp, OUT)   # ★ 原子替换：读者永远看到完整文件
    print(f"OK count={out['count']} size={os.path.getsize(OUT)}")

if __name__ == "__main__":
    main()
