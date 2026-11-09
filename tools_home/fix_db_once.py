#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix_db_once.py —— 老五·一次修db(补fp + 归层·合并)
照实: 两件都改 memories 表 -> 该[一次备份/一次改/一次验]·别两趟。
用法: fix_db_once.py [--apply]  默认 dry-run
"""
import sqlite3, collections, sys, shutil, datetime, hashlib, os
DB = "/opt/masterd-wudi/memory/memory.db"
APPLY = "--apply" in sys.argv
K2L = {
 "identity":"L1","decision":"L0","architecture":"L0","constitution":"L0","道":"L0","魂":"L0",
 "method":"L2","判据":"L2","教训":"L2","judge":"L2","criterion":"L2","机制":"L2","lesson":"L2",
 "event":"L3","case":"L3","真病":"L3","新判据":"L3","新器官":"L3","家族大事":"L3",
 "系统重置":"L3","流水":"L3","大发现":"L3","事件":"L3","life_record":"L3","病例":"L3",
 "letter":"L3","reply":"L3","器官":"L4","infra":"L4","报告":"L4","沙箱产出":"L4","审计":"L4",
}
con = sqlite3.connect(DB)
rows = con.execute("select id,kind,title,body,fp,layer from memories").fetchall()
n_fp = n_ly = 0
plan_fp = []; plan_ly = []
for i,k,t,b,fp,lay in rows:
    if not fp:
        plan_fp.append((i, hashlib.md5(((t or "")+(b or "")).encode()).hexdigest()[:16]))
    l2 = K2L.get(str(k or "").strip())
    if l2 and l2 != lay:
        plan_ly.append((i, l2))
print("要补fp:", len(plan_fp), "| 要归层:", len(plan_ly))
if not APPLY:
    print("[dry-run] 未动 db。加 --apply 执行。"); sys.exit(0)
bk = "/opt/masterd-wudi/data/backup_before_fix_once_%s.db" % datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy(DB, bk); print("备份:", bk)
cur = con.cursor()
for i, fp in plan_fp: cur.execute("update memories set fp=? where id=?", (fp, i)); n_fp += 1
for i, l2 in plan_ly: cur.execute("update memories set layer=? where id=?", (l2, i)); n_ly += 1
con.commit()
c = collections.Counter(r[0] for r in con.execute("select layer from memories"))
fpdup = len(con.execute("select fp from memories where fp!=\x27\x27 group by fp having count(*)>1").fetchall())
print("改完: 补fp=%d 归层=%d | fp重复组=%d" % (n_fp, n_ly, fpdup))
print("layer分布:", dict(sorted(c.items())))
con.close()
