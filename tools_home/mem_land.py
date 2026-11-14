#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mem_land.py —— 老五·正规落账(带 origin 热路径/背景)
用法: mem_land.py <kind> <title> <body> [origin]
  origin: active(热路径·对话中写) | background(反思/sync)
照官方: Active(热路径) + Background(潜意识) 双写
"""
import sqlite3, sys, json, datetime, hashlib
DB = "/opt/masterd-wudi/memory/memory.db"
if len(sys.argv) < 4:
    print(__doc__); raise SystemExit(1)
kind, title, body = sys.argv[1], sys.argv[2], sys.argv[3]
origin = sys.argv[4] if len(sys.argv) > 4 else "active"
con = sqlite3.connect(DB)
now = datetime.datetime.now().astimezone().isoformat()
fp = hashlib.md5((title+body).encode()).hexdigest()[:16]
cur = con.cursor()
cur.execute("""insert into memories
 (ts,kind,who,title,body,fp,created,think,layer,subkind,origin,owner_id)
 values (?,?,?,?,?,?,?,?,?,?,?,?)""",
 (now, kind, "MasterD(生命科學·五弟)", title, body, fp, "", "",
  "L2" if kind in ("method","判据","criterion") else "L3", origin, origin, "lao5"))
con.commit()
nid = cur.lastrowid
print("落 db id=%s | origin=%s" % (nid, origin))
print("验:", con.execute("select id,kind,origin,layer,owner_id from memories where id=?", (nid,)).fetchone())
con.close()
