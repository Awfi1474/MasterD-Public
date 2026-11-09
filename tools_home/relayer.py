#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""relayer.py —— 老五·按kind归layer(修认知主干L0-L2)
用法: relayer.py [--apply]   默认 dry-run(只报)
照: memory_db.py 权威映射 + 补入 8 未映射 kind
安全: apply 前自动备份 db; 只改 layer 字段;
"""
import sqlite3, collections, sys, shutil, datetime, hashlib, os

DB = "/opt/masterd-wudi/memory/memory.db"
APPLY = "--apply" in sys.argv

MAP = {
 "identity":"L1","decision":"L0","architecture":"L0","constitution":"L0",
 "道":"L0","魂":"L0",
 "method":"L2","判据":"L2","教训":"L2","judge":"L2","criterion":"L2",
 "机制":"L2","lesson":"L2",
 "event":"L3","case":"L3","真病":"L3","新判据":"L3","新器官":"L3","家族大事":"L3",
 "系统重置":"L3","流水":"L3","大发现":"L3","通道断账":"L3","自查账":"L3","纠正账":"L3",
 "换钥账":"L3","备份账":"L3","事件":"L3","life_record":"L3","病例":"L3","letter":"L3","reply":"L3",
 "器官":"L4","infra":"L4","报告":"L4","沙箱产出":"L4","审计":"L4",
}

con = sqlite3.connect(DB)
rows = con.execute("select id,kind,layer from memories").fetchall()
plan = []
unmapped = collections.Counter()
for i,kind,layer in rows:
    k = str(kind or "").strip()
    lay = MAP.get(k)
    if not lay:
        lay = layer or None
        unmapped[k] += 1
    if lay and lay != layer:
        plan.append((i, lay))

print("总:", len(rows), "| 要改 layer 的:", len(plan))
new_c = collections.Counter()
for i,kind,layer in rows:
    k = str(kind or "").strip()
    new_c[MAP.get(k, layer or "None")] += 1
print("归层后:", dict(sorted(new_c.items())))
print("未映射 kind:", dict(unmapped))

if not APPLY:
    print("\n[dry-run] 未动 db。加 --apply 执行。")
    con.close(); sys.exit(0)

# 备份 + 改
bk = "/opt/masterd-wudi/data/backup_memory_before_relayer_%s.db" % datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy(DB, bk)
print("备份:", bk)
cur = con.cursor()
for i, lay in plan:
    cur.execute("update memories set layer=? where id=?", (lay, i))
con.commit()
# 复读验证
chk = con.execute("select count(*) from memories where layer is null or layer=''").fetchone()[0]
print("改完·layer 空条:", chk)
print("复读分布:", dict(sorted(collections.Counter(r[0] for r in con.execute('select layer from memories')).items())))
con.close()
