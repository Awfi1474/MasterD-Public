#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·并发测试(照实: 2026-11-14 发现并发写坏链)
判据: 8进程同时写·0坏链=锁生效
"""
import sys, os, multiprocessing as mp
sys.path.insert(0,"/opt/masterd-wudi/tools")
T="/tmp/hc_conc_selfcheck.jsonl"

def w(i):
    from hashchain_log import append
    append(T,"c%d"%i)

if __name__=="__main__":
    if os.path.exists(T): os.remove(T)
    ps=[mp.Process(target=w,args=(i,)) for i in range(8)]
    [p.start() for p in ps]; [p.join() for p in ps]
    from hashchain_log import verify
    n,bad,_=verify(T)
    print("并发8写: %d行 坏链%d %s" % (n,bad,"✅锁生效" if bad==0 else "🔴坏了"))
    sys.exit(0 if bad==0 else 1)
