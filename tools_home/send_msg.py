#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""send_msg.py —— 老五·发消息统一入口(2026-11-08)
判据(我的病): 手拼heredoc中文会断→消息带乱码。改成:消息写文件·脚本读文件发。
用法:
  send_msg.py <to> <file.txt> [ctx]
  文件首行=主题·其余=正文
================================================================
"""
import sys, json, urllib.request
TOK = open("/opt/masterd-wudi/data/hub.token").read().strip()

def send(to, text, ctx=None):
    # 主投: huokeji.vip/a2a/message
    body = {"from":"lao5","to":to,"message":text}
    if ctx: body["context_id"]=ctx
    req = urllib.request.Request("https://huokeji.vip/a2a/message",
          data=json.dumps(body, ensure_ascii=False).encode(),
          headers={"Content-Type":"application/json"}, method="POST")
    r1 = json.loads(urllib.request.urlopen(req, timeout=10).read())
    print("投(huokeji):", {k:r1.get(k) for k in ("ok","delivered","known")})
    # 真源同步: HUB
    body2 = dict(body)
    req2 = urllib.request.Request("http://43.161.244.136:28800/a2a/message",
           data=json.dumps(body2, ensure_ascii=False).encode(),
           headers={"Content-Type":"application/json","Authorization":"Bearer "+TOK}, method="POST")
    try:
        r2 = json.loads(urllib.request.urlopen(req2, timeout=10).read())
        print("投(HUB真源):", {k:r2.get(k) for k in ("ok","delivered")})
    except Exception as e:
        print("投(HUB):", str(e)[:60])

if __name__ == "__main__":
    to = sys.argv[1]
    f = sys.argv[2]
    ctx = sys.argv[3] if len(sys.argv) > 3 else None
    text = open(f, encoding="utf-8").read()
    send(to, text, ctx)
