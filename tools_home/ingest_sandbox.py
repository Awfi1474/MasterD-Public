#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ingest_sandbox.py —— 把家拉回来的沙箱产出，自动并进 memory.db
★ 这是"两条腿"管线的最后一环：GitHub -> 家目录 -> 主库
★ 判据: 「拉回来 != 记住了｜落目录不算进库，进库才算记住」
幂等: 用批次目录名去重（ingest_ledger 表），重复跑不重复入。
"""
import os, re, json, sqlite3, datetime, hashlib

R = "/opt/masterd-wudi"
INBOX = os.path.join(R, "data/sandbox_inbox")
DB = os.path.join(R, "memory/memory.db")
WHO = "MasterD(医疗·老五)"

con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
c = con.cursor()

c.execute("CREATE TABLE IF NOT EXISTS ingest_ledger (batch TEXT PRIMARY KEY, ts TEXT, files INTEGER, saved INTEGER)")
done = set(r[0] for r in c.execute("SELECT batch FROM ingest_ledger"))

c.execute("SELECT MAX(id) FROM memories")
next_id = (c.fetchone()[0] or 0) + 1

saved_total = 0
new_batches = 0
batches = sorted(os.listdir(INBOX)) if os.path.isdir(INBOX) else []
for b in batches:
    bdir = os.path.join(INBOX, b)
    if not os.path.isdir(bdir) or b in done:
        continue
    items = []
    for root, dirs, files in os.walk(bdir):
        for fn in files:
            p = os.path.join(root, fn)
            if fn.lower().endswith((".jpg", ".png", ".jpeg", ".gif", ".webp")):
                continue
            try:
                txt = open(p, "r", errors="ignore").read()
            except Exception:
                continue
            if not txt.strip():
                continue
            if "INSERT INTO memories" in txt or fn.endswith(".md") or fn.endswith(".txt"):
                title = ""
                for line in txt.splitlines():
                    line = line.strip().strip('"').strip("'")
                    if line.lower().startswith("title"):
                        if "=" in line:
                            title = line.split("=", 1)[1].strip().strip('"').strip("'")
                            break
                    if fn.endswith(".md") and line.startswith("#") and not title:
                        title = line.lstrip("# ").strip()
                if not title:
                    title = "沙箱产出: " + fn
                items.append((fn, title, txt))
    for fn, title, txt in items:
        title = "[沙箱] " + title[:80]
        body = txt.strip()[:4000]
        fp = hashlib.sha256((title + body).encode()).hexdigest()[:16]
        if c.execute("SELECT 1 FROM memories WHERE fp=?", (fp,)).fetchone():
            continue
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        c.execute("INSERT INTO memories (id,ts,kind,who,title,body,fp,created,think) VALUES (?,?,?,?,?,?,?,?,?)",
                  (next_id, ts, "沙箱产出", WHO, title, body, fp, ts, "来源: " + b + "/" + fn))
        next_id += 1; saved_total += 1
    c.execute("INSERT OR REPLACE INTO ingest_ledger VALUES (?,?,?,?)",
              (b, datetime.datetime.now(datetime.timezone.utc).isoformat(), len(items), saved_total))
    new_batches += 1

con.commit()
total = c.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
print("OK 并入完成: 新批次 %d | 新记忆 %d | 主库现有 %d 条" % (new_batches, saved_total, total))
