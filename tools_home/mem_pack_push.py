#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mem_pack_push.py —— 老五·记忆包推送(照老三12:46 schema·做机制)
判据:记忆中心要齐|停更=断|机制不是手动
"""
import sqlite3, json, datetime, urllib.request
DB="/opt/masterd-wudi/memory/memory.db"; TOK=open("/opt/masterd-wudi/data/hub.token").read().strip()

def build():
    c=sqlite3.connect("file:%s?mode=ro"%DB,uri=True)
    layers={}
    for lay in ['M0','M1','M2','M3','M4']:
        rows=c.execute("select id,kind,substr(title,1,60) from memories where layer=? order by id limit 100",(lay,)).fetchall()
        layers[lay]=[{"id":r[0],"kind":r[1],"title":r[2]} for r in rows]
    tot=c.execute("select count(*) from memories").fetchone()[0]; c.close()
    return {"pack_version":"3","owner_id":"lao5","owner":"MasterD(医疗·五弟)",
            "built_at":datetime.datetime.now().isoformat(),"layers_scope":["M0","M1","M2","M3","M4"],
            "entities":layers["M0"],"relations":layers["M1"],"layers":layers,"total":tot}

if __name__=="__main__":
    pack=build()
    try:
        r=urllib.request.urlopen(urllib.request.Request("http://43.161.244.136:28800/memory/import",
           data=json.dumps(pack,ensure_ascii=False).encode(),
           headers={"X-Hub-Token":TOK,"Content-Type":"application/json"},method="POST"),timeout=15)
        d=json.loads(r.read())
        print("  pushed:",d.get("file"),d.get("bytes"),"B | counts:",d.get("counts"))
    except Exception as e:
        print("  ERR:",str(e)[:120])
