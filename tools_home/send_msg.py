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
    # ★ 2026-11-09 焊(照老七13:57 发信必过文本体检): 发前扫·有疑提示(不阻断)
    try:
        import importlib.util as _iu
        _sp = _iu.spec_from_file_location("check_text", "/opt/masterd-wudi/tools/check_text.py")
        _ct = _iu.module_from_spec(_sp); _sp.loader.exec_module(_ct)
        _w = _ct.check(text)
        if _w:
            print("⚠️ 文本体检: %d 处可疑(仍发·仅提示)" % len(_w))
    except Exception as _e:
        pass
    send(to, text, ctx)
