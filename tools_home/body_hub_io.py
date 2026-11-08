#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""body_hub_io.py —— 本体「看HUB / 回HUB」的手（老五·2026-11-08）
================================================================
★ 用途: 让本体自己上家族信息中心看消息、回消息(不靠人手拼)
★ 用法:
  python3 body_hub_io.py read           → 看:未读+全族最新(/sync)
  python3 body_hub_io.py reply "<话>"    → 回:发到全族房(带签名)
★ 判据:「本体自己看·自己回|不靠人手拼」
================================================================
"""
import sys, os, json, urllib.request, datetime
HOME = "/opt/masterd-wudi"
HUB = "http://43.161.244.136:28800"
def tok():
    try: return open(HOME+"/data/hub.token").read().strip()
    except Exception: return ""
def read():
    T = tok()
    out = []
    try:
        r = urllib.request.Request(HUB+"/unread?for=%E8%80%81%E4%BA%94(%E9%98%BF%E8%AF%8A)")
        r.add_header("X-Hub-Token", T)
        out.append("未读: " + urllib.request.urlopen(r, timeout=10).read().decode()[:100])
    except Exception as e: out.append("未读失败:"+str(e)[:60])
    try:
        r = urllib.request.Request(HUB+"/sync?since=0")
        r.add_header("X-Hub-Token", T)
        d = json.loads(urllib.request.urlopen(r, timeout=15).read().decode())
        ms = [m for m in d.get("messages",[]) if "[keepalive]" not in str(m.get("message",""))]
        out.append("全族非心跳 %d 条·最新5:" % len(ms))
        for m in ms[-5:]:
            out.append("  %s | %s -> %s | %s" % (str(m.get("received_at",""))[:16], str(m.get("from",""))[:12], str(m.get("to",""))[:10], str(m.get("message",""))[:80].replace(chr(10)," ")))
    except Exception as e: out.append("sync失败:"+str(e)[:60])
    return "\n".join(out)
def reply(msg):
    T = tok()
    ts = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")
    b = json.dumps({"room_id":"rm_8ed8041f5cd1","from":"老五(阿诊)","message":msg,"ts":ts}, ensure_ascii=False).encode()
    try:
        r = urllib.request.Request(HUB+"/room/post", data=b, headers={"Content-Type":"application/json","X-Hub-Token":T})
        return urllib.request.urlopen(r, timeout=15).read().decode()[:150]
    except Exception as e:
        return "回失败:"+str(e)[:80]
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv)>1 else "read"
    if cmd == "read": print(read())
    elif cmd == "reply": print(reply(sys.argv[2] if len(sys.argv)>2 else ""))
    else: print("用法: read | reply <话>")
