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

ME = "lao5"   # ★ 焊死令环3: 交默认from=自己·不靠手填
def send(to, text, ctx=None):
    # ★ 2026-11-11 改(照官方v0.3·老大11-10定): 主口=a2a-jsonrpc | 兼容口/a2a/message回退
    #   判据: 以官方为准|主口官方JSON-RPC 2.0
    body = {"from":ME,"to":to,"message":text}
    if ctx: body["context_id"]=ctx
    _ok_official = False
    try:
        # ★ 2026-11-12 改(照董事长令"发消息一律官方字段·暂停家族字段"):
        #   官方: role(user/agent)+parts[{kind,text}]+messageId+contextId
        #   别再塞家族 from/to 到 metadata(官方无此)
        import uuid as _uuid
        _msg = {"role": "user", "messageId": "msg-" + _uuid.uuid4().hex[:12],
                "parts": [{"kind": "text", "text": text}]}
        if ctx:
            _msg["contextId"] = str(ctx)
        _jr = {"jsonrpc":"2.0","id":1,"method":"message/send","params":{"message": _msg}}
        req = urllib.request.Request("https://huokeji.vip/a2a-jsonrpc",
              data=json.dumps(_jr, ensure_ascii=False).encode(),
              headers={"Content-Type":"application/json"}, method="POST")
        _ro = json.loads(urllib.request.urlopen(req, timeout=10).read())
        if _ro.get("result"):
            _ok_official = True
            print("投(a2a-jsonrpc·官方v0.3):", str(_ro.get("result"))[:80])
    except Exception as _e:
        print("投(a2a-jsonrpc)失败,回退兼容口:", str(_e)[:50])
    if not _ok_official:
        # ★ 2026-11-12 修(照全族验签统一): 兼容口也要带EIP-191签名
        #   判据: 无签->rejected|带签(from|message|ts)+address才收
        try:
            import datetime as _dt2, json as _j2
            from eth_account import Account
            from eth_account.messages import encode_defunct
            _sub = _j2.load(open("/opt/masterd-wudi/agent-id/subkey.json"))
            _ts2 = _dt2.datetime.now().astimezone().isoformat()
            _sig2 = Account.sign_message(encode_defunct(text="%s|%s|%s" % (ME, text, _ts2)),
                                         private_key=_sub["private_key"]).signature.hex()
            if not _sig2.startswith("0x"):
                _sig2 = "0x" + _sig2
            _body2 = {"from": ME, "to": to, "message": text, "ts": _ts2,
                      "address": _sub["address"], "sig": _sig2}
            req = urllib.request.Request("https://huokeji.vip/a2a/message",
                  data=json.dumps(_body2, ensure_ascii=False).encode(),
                  headers={"Content-Type":"application/json"}, method="POST")
            r1 = json.loads(urllib.request.urlopen(req, timeout=10).read())
            print("投(huokeji兼容口·带签):", {k:r1.get(k) for k in ("ok","delivered","known")})
        except Exception as _e2:
            print("投(兼容口)失败:", str(_e2)[:60])
    # ★ 2026-11-09 加(照老四四层[回执!=可查!=已读!=已回]·我第一层要有账): 发信账
    try:
        import datetime as _dt, os as _os
        _lp = "/opt/masterd-wudi/data/send_ledger.jsonl"
        _os.makedirs(_os.path.dirname(_lp), exist_ok=True)
        with open(_lp, "a", encoding="utf-8") as _f:
            import json as _j
            _f.write(_j.dumps({"ts": _dt.datetime.now().isoformat(timespec="seconds"),
                "to": to, "摘要": (text or "")[:400].replace("\n"," "),
                "len": len(text or ""),
                "hash": __import__("hashlib").md5((text or "").encode("utf-8")).hexdigest()[:12],
                "回执": {k: r1.get(k) for k in ("ok","delivered","known")}}, ensure_ascii=False) + "\n")
    except Exception:
        pass
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
            print("⛔ 认知闸硬拦·未发送: " + (_r.stdout or "")[-200:])
            _sy.exit(2)
        elif _r.returncode == 1:
            print("🔴 认知闸打回·未发送(先改再发): " + (_r.stdout or "")[-200:])
            _sy.exit(1)
        else:
            print("✅ 认知闸: 过")
        # ★ 2026-11-11 焊(照say.py三关口径): 言行闸·不过不发
        _s = _sp.run([_sy.executable, _H+"/tools/speech_gate.py", text[:2000]],
                     cwd=_H, capture_output=True, text=True)
        if _s.returncode != 0:
            print("🔴 言行闸打回·未发送(不照着规则·就不是我): " + (_s.stdout or "")[-200:])
            _sy.exit(1)
        print("✅ 言行闸: 过")
    except Exception as _e:
        pass
    # ★ 2026-11-09 焊(照老三决定门·董事长元规则): 发信前扫[重大/不可逆]红灯词 -> 警示
    try:
        _red = [k for k in ["改真源","删db","drop table","删除全部","不可逆","清空","reset --hard","转资金","转账","转钱","私钥","助记词","打款","汇款"] if k in text]
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
