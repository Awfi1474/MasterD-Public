#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""a2a_gate.py —— 老五 A2A 唤醒闸 (2026-11-08)
================================================================
判据(老三家族版+老五加第三条):
  "收到 != 处理 | 处理 != 干完 | 干完 != 复诊过"
  submitted != working | working要有心跳(updated_at) | 超时标 stalled
用法:
  a2a_gate.py recv <from> <msg_id|-> <摘要>   -> 落账 status=working
  a2a_gate.py done <msg_id> <结果>            -> status=completed
  a2a_gate.py status [msg_id]                 -> 查(默认全部working)
  a2a_gate.py beat <msg_id> [进度]            -> 心跳(更新updated_at)
================================================================
"""
import sqlite3, sys, datetime, hashlib
HOME = "/opt/masterd-wudi"
DB = HOME + "/memory/memory.db"

def now():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")

def ensure(con):
    con.execute("""CREATE TABLE IF NOT EXISTS a2a_inbox (
      msg_id TEXT PRIMARY KEY, frm TEXT, summary TEXT,
      status TEXT, note TEXT, created_at TEXT, updated_at TEXT)""")
    con.commit()

def recv(frm, mid, summary):
    con = sqlite3.connect(DB, timeout=10); ensure(con)
    if not mid or mid == "-":
        mid = "local-" + hashlib.md5((frm + now() + summary).encode()).hexdigest()[:10]
    t = now()
    con.execute("""INSERT OR REPLACE INTO a2a_inbox
      (msg_id,frm,summary,status,note,created_at,updated_at) VALUES (?,?,?,?,?,?,?)""",
      (mid, frm, summary[:200], "working", "收到·开始处理", t, t))
    con.commit(); con.close()
    print("WORKING %s <- %s | %s" % (mid, frm, summary[:50]))

def done(mid, result):
    con = sqlite3.connect(DB, timeout=10); ensure(con)
    con.execute("UPDATE a2a_inbox SET status='completed',note=?,updated_at=? WHERE msg_id=?",
                (result[:200], now(), mid))
    con.commit(); con.close()
    print("COMPLETED %s | %s" % (mid, result[:50]))


def ask(mid, q):
    """不确定 -> input-required(照官方A2A:别硬说完成)"""
    con = sqlite3.connect(DB, timeout=10); ensure(con)
    con.execute("UPDATE a2a_inbox SET status='input-required',note=?,updated_at=? WHERE msg_id=?",
                (("待澄清:"+q)[:200], now(), mid))
    con.commit(); con.close()
    print("INPUT-REQUIRED %s | %s" % (mid, q[:50]))

def beat(mid, prog):
    con = sqlite3.connect(DB, timeout=10); ensure(con)
    con.execute("UPDATE a2a_inbox SET updated_at=?,note=? WHERE msg_id=?",
                (now(), prog[:200], mid))
    con.commit(); con.close()
    print("BEAT %s | %s" % (mid, prog[:50]))

def status(mid=None):
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    if mid:
        rows = con.execute("SELECT * FROM a2a_inbox WHERE msg_id=?", (mid,)).fetchall()
    else:
        rows = con.execute("SELECT * FROM a2a_inbox ORDER BY updated_at DESC LIMIT 30").fetchall()
    n_w = n_c = n_s = 0
    for r in rows:
        # stalled: working 且 updated_at 超 30 分钟
        st = r[3]
        try:
            dt = datetime.datetime.strptime(r[6][:19], "%Y-%m-%dT%H:%M:%S")
            age = (datetime.datetime.now() - dt).total_seconds() / 60
        except Exception:
            age = 0
        if st == "working" and age > 30:
            st = "stalled"
        if st == "working": n_w += 1
        elif st == "completed": n_c += 1
        elif st == "stalled": n_s += 1
        print("[%s] %-9s age=%.0fm  %s <- %s | %s" % (r[0][:16], st, age, r[2][:34], r[1][:14], r[5][:30]))
    print("--- summary: working=%d completed=%d stalled=%d ---" % (n_w, n_c, n_s))
    con.close()

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(0)
    c = a[0]
    if c == "recv":   recv(a[1], a[2] if len(a) > 2 else "-", " ".join(a[3:]) if len(a) > 3 else "")
    elif c == "done": done(a[1], " ".join(a[2:]))
    elif c == "beat": beat(a[1], " ".join(a[2:]))
    elif c == "ask": ask(a[1], " ".join(a[2:]))
    elif c == "status": status(a[1] if len(a) > 1 else None)
    else: print("unknown:", c)
