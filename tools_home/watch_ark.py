#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""watch_ark.py —— 老五·本职(区块链):定时读 ARK 总量·存时序(看续不续降)
照机制>自觉:观察不靠脑子记,靠 timer。
"""
import json, urllib.request, os, datetime

RPCS=["https://bsc-dataseed.binance.org/","https://bsc-dataseed1.defibit.io/","https://bsc-rpc.publicnode.com"]
def rpc(method, params):
    for u in RPCS:
        try:
            body=json.dumps({"jsonrpc":"2.0","method":method,"params":params,"id":1}).encode()
            req=urllib.request.Request(u,data=body,headers={"Content-Type":"application/json"})
            with urllib.request.urlopen(req,timeout=12) as r:
                d=json.load(r)
                if "result" in d: return d["result"]
        except Exception: pass
    return None

ARK="0xCae117ca6Bc8A341D2E7207F30E180f0e5618B9D"
PAIR="0xCAaF3c41a40103a23Eeaa4BbA468AF3cF5b0e0D8"
LED="/opt/masterd-wudi/data/ark_supply_ts.jsonl"

bn=rpc("eth_blockNumber",[])
ts=rpc("eth_call",[{"to":ARK,"data":"0x18160ddd"},"latest"])
res=rpc("eth_call",[{"to":PAIR,"data":"0x0902f1ac"},"latest"])
rec={"ts":datetime.datetime.now().isoformat(timespec="seconds"),
     "block":int(bn,16) if bn else None,
     "ark_totalSupply":int(ts,16)/1e18 if ts else None}
if res:
    x=res[2:]; r0=int(x[0:64],16); r1=int(x[64:128],16)
    rec["pool_usdt"]=r0/1e18; rec["pool_ark"]=r1/1e18
    rec["ark_price_usd"]=round((r0/1e18)/(r1/1e18),6) if r1 else None
open(LED,"a",encoding="utf-8").write(json.dumps(rec,ensure_ascii=False)+"\n")
# 看时序(末3条·判续降)
lines=open(LED,encoding="utf-8").read().splitlines()
print("记录条数:", len(lines))
for l in lines[-3:]:
    d=json.loads(l); print(" ", d["ts"], "| ARK总量", d.get("ark_totalSupply"), "| 价", d.get("ark_price_usd"))
