#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·工作留痕 work_log.py（照实: 干活要进账·不然本体答不出）
★ 判据: 「答得出自己做了什么才算真在想」(老七)
★ 用法: work_log.py "<做了什么>" "<改了什么文件>" ["验了没"]
"""
import sqlite3, hashlib, datetime, sys

HOME = "/opt/masterd-wudi"
DB = HOME + "/memory/memory.db"
TZ = datetime.timezone(datetime.timedelta(hours=8))

def log(what, files="", verified=""):
    body = "① 做了什么: %s\n② 改了/花了什么: %s\n③ 验了没: %s" % (what, files, verified or "未验(要补)")
    fp = hashlib.sha256(body.encode()).hexdigest()[:16]
    now = datetime.datetime.now(TZ).isoformat(timespec="seconds")
    c = sqlite3.connect(DB); cur = c.cursor()
    cur.execute("""INSERT INTO memories (ts,kind,who,title,body,fp,created,layer,owner_id,subkind,mem_class,mem_state)
     VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
     (now, "event", "老五", "【工作】" + what[:60], body, fp, now, "L2", "lao5", "work", "event", "active"))
    c.commit()
    print("✅ 留痕 id=%d | %s" % (cur.lastrowid, what[:50]))
    return cur.lastrowid

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: work_log.py '<做了什么>' ['<文件>'] ['<验了没>']")
        sys.exit(1)
    log(sys.argv[1], sys.argv[2] if len(sys.argv)>2 else "", sys.argv[3] if len(sys.argv)>3 else "")
