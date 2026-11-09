#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stalled_redo.py —— 老五·卡住重做器(治'一次没成不重做')
判据:卡了要重做(不许干等)|机制>自觉
"""
import sqlite3, datetime
DB="/opt/masterd-wudi/memory/memory.db"
def redo():
    c=sqlite3.connect(DB)
    # 找 stalled/working超30分 的·标"待重做"
    rows=c.execute("select msg_id,status,note,updated_at from a2a_inbox where status in ('working','stalled')").fetchall()
    n=0
    for mid,st,note,up in rows:
        try:
            age=(datetime.datetime.now()-datetime.datetime.strptime(up[:19],"%Y-%m-%dT%H:%M:%S")).total_seconds()/60
        except Exception: age=0
        if age>30 or st=="stalled":
            # 标"待重做"(not stalled·改回working+note)
            c.execute("update a2a_inbox set status='working',note=?,updated_at=? where msg_id=?",
                      ("★超时%.0f分·标待重做(不干等)"%age, datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"), mid))
            n+=1
            print("  REDO %s(%.0f分)"%(mid[:24],age))
    c.commit();c.close()
    print("  标待重做:%d条"%n)
if __name__=="__main__": redo()
