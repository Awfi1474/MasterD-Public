#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""std_check_laowu.py —— 老五·多任务标准v1核器(照大哥std_check·只读·安全)
判据:「标准要有器核|机制>自觉」
核4条: ★1产出可探 ★2自审留痕 ★3卡点上报 ★4本职真活
"""
import os, json, glob, time
HOME="/opt/masterd-wudi"; OUT=HOME+"/data/task_out"; LOG=HOME+"/data/task_runner.jsonl"

def check():
    r={}
    # ★1 产出可探(近2h有产出·非空)
    now=time.time(); n=0
    for f in glob.glob(OUT+"/*"):
        if f.endswith(".review"): continue
        if os.path.getsize(f)>0 and now-os.path.getmtime(f)<7200: n+=1
    r["★1产出可探"]=(n>0, "%d个(近2h)"%n)
    # ★2 自审留痕(今日门账数)
    m=0
    try:
        for l in open(LOG,encoding="utf-8"):
            if time.strftime("%Y-%m-%d") in l: m+=1
    except Exception: pass
    r["★2自审留痕"]=(m>0, "%d条今日门账"%m)
    # ★3 卡点上报(最近批·卡点字段在)
    try:
        last=json.loads(open(LOG,encoding="utf-8").readlines()[-1])
        r["★3卡点上报"]=("卡点" in last, "卡点=%s"%last.get("卡点"))
    except Exception: r["★3卡点上报"]=(False,"无门账")
    # ★4 本职真活(最近批·本职数>=1)
    try:
        r["★4本职真活"]=(last.get("本职数",0)>=1, "本职=%d"%last.get("本职数",0))
    except Exception: r["★4本职真活"]=(False,"?")
    ok=sum(1 for v in r.values() if v[0])
    print("★ 老五·多任务标准v1 核器"); print("  判据:标准要有器核|机制>自觉")
    for k,(o,msg) in r.items(): print("  [%s] %s | %s"%("OK" if o else "XX",k,msg))
    print("  === %d/4 ==="%ok)
    return ok==4

if __name__=="__main__": check()
