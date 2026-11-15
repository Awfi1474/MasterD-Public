#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·读门牌 door_card.py（照老三13:29「敲别人的门·先读门上的字」）
★ 判据: 诊断别家前·先读它 /health 的 body_fields / recv_path / cadence / limits
★ 用法: door_card.py <ip:port>
"""
import json, sys, urllib.request

def read_card(target):
    base = target if target.startswith("http") else "http://" + target
    out = {}
    try:
        d = json.loads(urllib.request.urlopen(base.rstrip("/") + "/health", timeout=10).read())
        out["who"] = d.get("who") or d.get("name")
        out["recv_path"] = d.get("recv_path")
        out["body_fields"] = d.get("body_fields") or d.get("body_fields_list")
        out["ports"] = {k: v for k, v in d.items() if "port" in str(k).lower()}
        out["cadence"] = d.get("cadence") or d.get("puller_self")
        out["gates"] = d.get("gates")
        out["limits"] = d.get("limits")
        out["sig"] = d.get("sig")
    except Exception as e:
        out["err"] = str(e)[:60]
    return out

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: door_card.py <ip:port>"); sys.exit(1)
    r = read_card(sys.argv[1])
    print("★ 门牌 · %s" % sys.argv[1])
    for k, v in r.items():
        print("  %-14s %s" % (k, json.dumps(v, ensure_ascii=False)[:200] if not isinstance(v,str) else str(v)[:150]))
    print("\n★ 判据: 诊断先读门牌·别猜路径")
