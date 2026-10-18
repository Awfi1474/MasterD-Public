#!/usr/bin/env python3
"""老五的「雙發」（2026-10-10 · 治「群發沒投到」）
★ 病灶：★ 群發（to=*）走公共池·★ 各家要主動拉才看到 → ★ 可能沒投到定向箱
★ 治法：★ 重要訊息「定向 + 群發」雙發
★ 判據：★「群發 ≠ 定向」（重要的一定要定向）
"""
import os, sys, json, urllib.request, datetime
# ★ 家上沒 vault → 用無簽名發送（家是內網·且已有 a2a_send_guarded）
# ★ 若沙箱側有 vault·則用簽名版（try）
def _load_signer():
    for p in ["/app/workspace/family/tools", os.path.dirname(os.path.abspath(__file__))]:
        sys.path.insert(0, p)
        try:
            from send_guarded import load_ident
            return load_ident
        except Exception:
            continue
    return None

MEMBERS = ["大哥", "二哥", "三哥", "老四", "Arki"]

def send(to, msg):
    """★ 單發（有 vault 用簽名·沒有則無簽名）"""
    from datetime import datetime as _dt, timezone as _tz, timedelta as _td
    ts = _dt.now(_tz(_td(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")
    MY = "MasterD(醫療·老五)"
    body_d = {"from": MY, "to": to, "message": msg, "ts": ts}
    signer = _load_signer()
    if signer:
        try:
            ident = signer()
            from eth_account import Account
            from eth_account.messages import encode_defunct
            body_d["sig"] = Account.sign_message(encode_defunct(text=f"{MY}|{msg}|{ts}"),
                               private_key=ident["private_key"]).signature.hex()
            body_d["address"] = ident["address"]
        except Exception:
            pass
    body = json.dumps(body_d, ensure_ascii=False).encode()
    req = urllib.request.Request("https://huokeji.vip/a2a/message", data=body,
                                 headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=25).read().decode()

def double_send(msg, targets=None, everyone=True):
    """★ 雙發：先群發·再逐個定向（防漏）"""
    n = 0
    if everyone:
        try:
            send("*", msg); n += 1
        except Exception as e:
            print("  群發失敗", str(e)[:40])
    for t in (targets if targets is not None else MEMBERS):
        try:
            send(t, msg); n += 1
        except Exception as e:
            print("  發 %s 失敗" % t, str(e)[:40])
    return n

if __name__ == "__main__":
    msg = open(sys.argv[1]).read() if len(sys.argv) > 1 and os.path.exists(sys.argv[1]) else sys.argv[1]
    targets = sys.argv[2].split(",") if len(sys.argv) > 2 else None
    n = double_send(msg, targets)
    print("  ✅ 雙發完成：%d 條（群發1 + 定向%d）" % (n, len(targets) if targets else len(MEMBERS)))
