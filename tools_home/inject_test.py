#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·注入测试v2（照老三/老六判据·带owner_id）
★ 修: 旧版没带owner_id→被触发器拦(不是测试失败·是脚本错)
"""
import sqlite3, shutil, datetime
DB = "/opt/masterd-wudi/memory/memory.db"
shutil.copy(DB, DB + ".bak-before-inject2-20261114")
c = sqlite3.connect(DB); cur = c.cursor()

# ① 塞一条 owner=lao3（别家·带 owner_id）
cur.execute("""INSERT INTO memories (ts,kind,who,title,body,fp,created,layer,owner_id,subkind,mem_class,mem_state)
 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
 (datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "method", "老三(燼)",
  "INJECT-V2-TEST", "别再家测试", "injectv2", "2026-11-14T03:10:00", "L3", "lao3", "inject", "method", "active"))
c.commit()

# ② 查我(lao5)
me = cur.execute("SELECT COUNT(*) FROM memories WHERE owner_id='lao5'").fetchone()[0]
hit = cur.execute("SELECT COUNT(*) FROM memories WHERE owner_id='lao5' AND title='INJECT-V2-TEST'").fetchone()[0]
print("① 注入 owner=lao3 → 成功")
print("② 查 owner=lao5: %d 条" % me)
print("③ 注入条在我这吗: %d 条" % hit)
print("★ 结果: %s" % ("✅ 读不到·隔离成立" if hit == 0 else "❌ 混了"))

# ④ 清理
cur.execute("DELETE FROM memories WHERE title='INJECT-V2-TEST'"); c.commit()
print("④ 已清理·库回 %d 条" % cur.execute("SELECT COUNT(*) FROM memories").fetchone()[0])
