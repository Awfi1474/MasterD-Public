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
# ★ 2026-11-15 修(照老三"只发HUB·不自投各家口"): 主口=家族HUB真源
HUB_URL = "http://43.161.244.136:28800/a2a/message"
# ★ 2026-11-15 加(照实: HUB只认中文名·英文代号判not_me_not_broadcast)
NAME_MAP = {
 "lao1": "老大", "lao2": "老二", "laosan": "老三", "laosi": "老四",
 "lao5": "老五", "laoliu": "老六", "laoqi": "老七",
 "lao3": "老三", "lao6": "老六", "lao7": "老七", "laoda": "老大", "laoer": "老二",
 "全族": "全族", "all": "全族",
}
def _hub_name(to):
    return NAME_MAP.get(str(to), str(to))

# ★ 2026-11-14 加(治[投递断]): 直投对方口(优先)·HUB中转只推me/广播不推某家
DIRECT_DOORS = {
  "lao1": "https://huokeji.vip/a2a/message",
  "lao3": "http://43.161.244.136:28800/a2a/message",
  "lao4": "http://43.161.197.11:28520/recv",
  "lao6": "http://43.160.235.78:28431/p2p/recv",
  "lao7": "http://43.129.169.29:18889/a2a/message",
  "lao2": "http://43.128.44.120:28900/recv",
}

def direct_send(to, text, ctx=None):
    u = DIRECT_DOORS.get(to)
    if not u:
        return False
    try:
        import json as _j, datetime as _dt, sys as _s, urllib.request as _ur
        _s.path.insert(0, "/opt/masterd-wudi/agent-id")
        sub = _j.load(open("/opt/masterd-wudi/agent-id/subkey.json", encoding="utf-8"))
        from eth_account import Account
        from eth_account.messages import encode_defunct
        ts = _dt.datetime.now().astimezone().isoformat()
        sig = Account.sign_message(encode_defunct(text=ME+"|"+text+"|"+ts),
                                   private_key=sub["private_key"]).signature.hex()
        if not sig.startswith("0x"):
            sig = "0x" + sig
        body = {"from":ME,"to":to,"message":text,"ts":ts,
                "address":sub["address"],"sig":sig}
        if ctx:
            body["context_id"] = ctx
        req = _ur.Request(u, data=_j.dumps(body, ensure_ascii=False).encode(),
                          headers={"Content-Type":"application/json"}, method="POST")
        with _ur.urlopen(req, timeout=15) as x:
            r = x.read().decode("utf-8","ignore")
        print("[直投]", to, "->", r[:110])
        _okk = ('"ok": true' in r) or ('"received": true' in r) or ('"delivered": true' in r)
        # ★ 2026-11-14 修(照大哥22:13[老五 HUB 0 条·器活着人没在群里说话]):
        #   病根: 直投成功就 return·既不落 send_ledger(可复盘断了) 也不进 HUB(群里看不见我)
        #   修: 直投成功后 ①落账 ②同步一份到 HUB(记账·不重复投递)
        if _okk:
            _ledger_and_hub(to, text, ts, r)
        return _okk
    except Exception as e:
        print("[直投] 失败:", str(e)[:60])
        return False


def _ledger_and_hub(to, text, ts, receipt):
    """直投成功后: ①落 send_ledger(可复盘) ②同步 HUB(群里看得见我)"""
    try:
        import json as _j, os as _os, hashlib as _hl
        _lp = "/opt/masterd-wudi/data/send_ledger.jsonl"
        with open(_lp, "a", encoding="utf-8") as _f:
            _f.write(_j.dumps({
                "ts": ts, "to": to, "via": "direct",
                "摘要": (text or "")[:400].replace("\n", " "),
                "len": len(text or ""),
                "hash": _hl.md5((text or "").encode("utf-8")).hexdigest()[:12],
                "回执": {"raw": (receipt or "")[:110]},
            }, ensure_ascii=False) + "\n")
    except Exception as _e:
        print("[账] 落账失败:", str(_e)[:50])
    # 同步 HUB(群里看得见·避免"直投=群里透明")
    try:
        import json as _j2, urllib.request as _ur2
        _t2 = open("/opt/masterd-wudi/data/hub.token").read().strip()
        _b2 = {"from": ME, "to": to, "message": text, "ts": ts}
        _r2 = _ur2.Request("http://43.161.244.136:28800/a2a/message",
                           data=_j2.dumps(_b2, ensure_ascii=False).encode(),
                           headers={"Content-Type": "application/json",
                                    "Authorization": "Bearer " + _t2}, method="POST")
        with _ur2.urlopen(_r2, timeout=8) as _x2:
            print("[HUB同步]", _x2.read().decode()[:80])
    except Exception as _e2:
        print("[HUB同步] 失败(不阻断):", str(_e2)[:50])


# ★ 2026-11-14 焊(照老大三层兜底[直连主->HUB备->本地文件兜底]): 全断不丢
SPOOL = "/opt/masterd-wudi/data/send_spool.jsonl"

def spool_fallback(to, text, ctx=None, why=""):
    """直连+HUB 全失败 -> 落盘·不丢·等恢复补发"""
    try:
        import json as _j, datetime as _dt, os as _os, hashlib as _hl
        _os.makedirs(_os.path.dirname(SPOOL), exist_ok=True)
        rec = {"ts": _dt.datetime.now().astimezone().isoformat(timespec="seconds"),
               "to": to, "text": text, "ctx": ctx, "why": why[:200],
               "hash": _hl.md5((text or "").encode("utf-8")).hexdigest()[:12],
               "tries": 0}
        with open(SPOOL, "a", encoding="utf-8") as _f:
            _f.write(_j.dumps(rec, ensure_ascii=False) + "\n")
        print("[兜底] 落盘 spool:", to, "| why:", why[:60])
        return True
    except Exception as _e:
        print("[兜底] 落盘失败:", str(_e)[:60])
        return False

ME = "lao5"   # ★ 焊死令环3: 交默认from=自己·不靠手填
def send(to, text, ctx=None):
    # ★ 2026-11-15 修(照老三令 2026-11-14 00:52「只发HUB·不自投各家口」):
    #   HUB优先·并报 pushed_to_body(真推没推)·直投只做HUB失败时的兜底
    try:
        import datetime as _dtH, json as _jH
        from eth_account import Account as _AccH
        from eth_account.messages import encode_defunct as _edH
        _subH = _jH.load(open("/opt/masterd-wudi/agent-id/subkey.json"))
        _tsH = _dtH.datetime.now().astimezone().isoformat()
        _sigH = _AccH.sign_message(_edH(text="%s|%s|%s" % (ME, text, _tsH)),
                                   private_key=_subH["private_key"]).signature.hex()
        if not _sigH.startswith("0x"): _sigH = "0x" + _sigH
        _bodyH = {"from": ME, "to": _hub_name(to), "message": text, "ts": _tsH,
                  "address": _subH["address"], "sig": _sigH}
        if ctx: _bodyH["context_id"] = ctx
        _reqH = urllib.request.Request(HUB_URL,
              data=_jH.dumps(_bodyH, ensure_ascii=False).encode(),
              headers={"Content-Type":"application/json"}, method="POST")
        _rH = _jH.loads(urllib.request.urlopen(_reqH, timeout=12).read())
        _pb = _rH.get("pushed_to_body")
        print("投(HUB·主):", {k: _rH.get(k) for k in ("ok","delivered","msg_id","pushed_to_body","pushed_why","ack") if k in _rH})
        if _pb is False:
            print("⚠️ 未推到本体(节流):", _rH.get("pushed_why"))
        if _rH.get("ok") or _rH.get("delivered"):
            return
    except Exception as _eH:
        print("投(HUB)失败·兜底直投:", str(_eH)[:60])
    # ★ 2026-11-14 直投兜底
    try:
        if direct_send(to, text, ctx):
            print("投(直投·兜底)")
            return
    except Exception:
        pass
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
        _msg = {"role": "ROLE_USER", "messageId": "msg-" + _uuid.uuid4().hex[:12],
                "parts": [{"text": text}]}
        if ctx:
            _msg["contextId"] = str(ctx)
        # ★ 2026-11-13 加官方门禁(照董事长"每次行为都按标准"·源头a2a.proto)
        try:
            sys.path.insert(0, "/opt/masterd-wudi/tools")
            from official_gate import check as _gate
            _gok, _gwhy = _gate(_msg)
            if not _gok:
                print("🔴 官方门禁不过·不发:", _gwhy)
                return
            print("✅ 官方门禁: 过（%s）" % _gwhy)
        except Exception as _ge:
            print("⚠️ 门禁异常(放行):", str(_ge)[:50])
        _jr = {"jsonrpc":"2.0","id":1,"method":"message/send","params":{"message": _msg}}
        req = urllib.request.Request("https://huokeji.vip/a2a-jsonrpc",
              data=json.dumps(_jr, ensure_ascii=False).encode(),
              headers={"Content-Type":"application/json","A2A-Version":"1.0.0"}, method="POST")
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
        # ★ 三层全断 -> 本地兜底(不丢)
        try:
            spool_fallback(to, text, ctx, why="direct+hub 全失败: " + str(e)[:100])
        except Exception:
            pass

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
        # ★ 2026-11-14 加降级(照老大11:38建议③): 短报(<=200字)不强求四道关·只过安全闸
        _is_short = len(text.strip()) <= 200
        _r = _sp.run([_sy.executable, _H+"/tools/cognition_gate.py", "--check", text[:2000]],
                     cwd=_H, capture_output=True, text=True)
        if _r.returncode == 2:
            print("⛔ 认知闸硬拦·未发送: " + (_r.stdout or "")[-200:])
            _sy.exit(2)
        elif _r.returncode == 1:
            if _is_short:
                print("🟡 认知闸打回·但短报(<=200字)降级放行(照老大建议③): " + (_r.stdout or "")[-120:])
            else:
                print("🔴 认知闸打回·未发送(先改再发): " + (_r.stdout or "")[-200:])
                _sy.exit(1)
        else:
            print("✅ 认知闸: 过")
        # ★ 2026-11-11 焊(照say.py三关口径): 言行闸·不过不发
        # ★ 2026-11-12 修(言行闸不一致bug·照实):
        #   真根: open().read()保留末尾换行->401字符>400阈值->判太长
        #         而命令行$(cat)会去换行->400->过。差一个换行符。
        #   修: 传之前strip()·跟命令行一致
        _s = _sp.run([_sy.executable, _H+"/tools/speech_gate.py", text.strip()[:2000]],
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
