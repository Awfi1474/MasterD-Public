#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vip_overdue.py —— VIP超期未签收清单(照老三10:16第3条)
判据:账不能抹只能挂|挂账要报出·每24h报全族|红着到签为止
"""
import json, os, datetime

import json as _j
def _thr():
    """★ 照老三'阈值进档不进代码':读 THRESHOLDS.json"""
    try:
        return _j.load(open("/opt/masterd-wudi/memory/THRESHOLDS.json"))
    except Exception:
        return {"vip_overdue_days": 24}

HOME="/opt/masterd-wudi"; DATA=HOME+"/data"
VIPLED=DATA+"/vip_signoff.jsonl"; LEDGER=DATA+"/tier_ledger.jsonl"

_THR = _thr()   # ★ 读阈值档
def overdue():
    sig=set(); pend=set()
    for l in open(VIPLED,encoding="utf-8",errors="ignore"):
        try:d=json.loads(l)
        except:continue
        if d.get("manual") and d.get("kind")=="human": sig.add(str(d.get("msg_id")))
        if d.get("kind")=="pending_unsigned" and not d.get("superseded"): pend.add(str(d.get("msg_id")))
    # 找真VIP未签(人投/董事长令类·非测试)
    out=[]
    for l in open(LEDGER,encoding="utf-8",errors="ignore"):
        try:d=json.loads(l)
        except:continue
        if d.get("tier")!="L4" or d.get("signed"): continue
        mid=str(d.get("msg_id"))
        t=str(d.get("title",""))
        if any(k in t for k in ["stdverify","[h1]","冒名","五律自动","[复现]"]): continue  # 测试流水不算
        if mid in sig: continue
        fr=str(d.get("from",""))
        if "老五" in fr or "阿诊" in fr or "生命科學·老五" in fr: continue  # ★ 自己发的不算(人投我的才算)
        out.append({"msg_id":mid,"from":str(d.get("from",""))[:16],"title":t[:50],"ts":str(d.get("ts",""))[:16]})
    return out

if __name__=="__main__":
    o=overdue()
    print("★ VIP 超期未签收清单 @ "+datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("  判据:「账不能抹只能挂|挂账要报出|红着到签为止」")
    print("  条数:",len(o))
    for x in o[:10]:
        print("   [%s] %-14s | %s"%(x["ts"][5:],x["from"][:13],x["title"]))
    # 落盘
    json.dump({"ts":datetime.datetime.now().isoformat(),"count":len(o),"list":o},open(DATA+"/vip_overdue.json","w"),ensure_ascii=False,indent=1)
    print("  落盘:data/vip_overdue.json")
