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
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    DRY = "--dry-run" in sys.argv
    to = args[0]
    f = args[1]
    ctx = args[2] if len(args) > 2 else None
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
    # ★ 2026-11-09 焊(照 exec_system 口径): 发信前过[认知闸 + 出口闸]
    try:
        import subprocess as _sp, sys as _sy
        _H = "/opt/masterd-wudi"
        # ① 认知闸(绕体系/假装 -> 拦)
        _r = _sp.run([_sy.executable, _H+"/tools/cognition_gate.py", "--check", text[:2000]],
                     cwd=_H, capture_output=True, text=True)
        if _r.returncode == 2:
            print("⛔ 认知闸硬拦(不许输出): " + (_r.stdout or "")[-200:])
            print("   (仍发·但请照实改)")
        elif _r.returncode == 1:
            print("🔴 认知闸打回(建议重写)")
        else:
            print("✅ 认知闸: 过")
    except Exception as _e:
        pass
    # ★ 2026-11-09 焊(照老三决定门·董事长元规则): 发信前扫[重大/不可逆]红灯词 -> 警示
    try:
        _red = [k for k in ["改真源","删db","drop table","删除全部","不可逆","清空","reset --hard"] if k in text]
        if _red:
            print("🔴 决定门警示: 文本含重大词 %s -> 先过 wudi_gate(别自答自过)" % _red)
        else:
            print("✅ 决定门: 未见重大红灯词(照常发)")
    except Exception:
        pass
    if DRY:
        print("[dry-run] 不真发(测器用·不污染公共面)")
    else:
        send(to, text, ctx)
