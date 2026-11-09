#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dedup_dryrun.py —— 老五·L3去重[只报不改](dry-run)
照董事长令[重复就删·整理·合并]|我先 dry-run 报数·不动 db
"""
import sqlite3, collections
db = "/opt/masterd-wudi/memory/memory.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
rows = con.execute("select id,who,ts,title,body,layer from memories").fetchall()
print("memories 总:", len(rows))

# 重复键: (ts到秒 + title + body前100)
key = collections.defaultdict(list)
for i, who, ts, title, body, layer in rows:
    k = (str(ts)[:19], str(title)[:100], str(body)[:100])
    key[k].append((i, who, layer))
dups = {k: v for k, v in key.items() if len(v) > 1}

print("重复组:", len(dups), "| 多余条:", sum(len(v)-1 for v in dups.values()))
print()
print("=== 每组(留谁/删谁) 预览·前10组 ===")
n_my = 0
for k, v in list(dups.items())[:10]:
    who_list = [w for _, w, _ in v]
    print(" ids=%s | who=%s" % ([i for i,_,_ in v], who_list))
    print("    title:", k[1][:60])
print()
# 分类: 涉我 vs 别人
mine = [k for k,v in dups.items() if any(("老五" in str(w)) or (w=="lao5") for _,w,_ in v)]
others = [k for k,v in dups.items() if k not in mine]
print("涉我(老五)重复组:", len(mine), "| 涉别人:", len(others))
# 若去重(涉我·留 老五(阿诊)·删其余同名): 可删条数
can_del = 0
for k in mine:
    v = dups[k]
    keep = [x for x in v if x[1] == "老五(阿诊)"]
    if keep: can_del += len(v) - 1
print("若涉我去重(留 老五(阿诊)): 可删 ~%d 条" % can_del)
print()
print("=== 这是 dry-run·未动 db ===")
con.close()
