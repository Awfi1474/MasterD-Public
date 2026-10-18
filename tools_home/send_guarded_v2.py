#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""send_guarded_v2.py —— 老五唯一发送口（出口闸必过）
★ 判据: 「说了规矩 != 守了规矩｜要"出不去"才算」
★ 用法: send_guarded_v2.py "<消息>"
"""
import sys, os, json, subprocess, urllib.request, datetime
HOME = "/opt/masterd-wudi"
sys.path.insert(0, HOME + "/tools")
def main():
    if len(sys.argv) < 2:
        print("用法: send_guarded_v2.py <消息>"); return 1
    msg = " ".join(sys.argv[1:])
    # ★ 第一关: 出口闸（不过就不发）
    import out_gate
    ok, why = out_gate.check(msg)
    print("★ 出口闸: " + ("✅ 放行" if ok else "🔴 拦下(" + ",".join(why) + ")"))
    if not ok: return 1
    # ★ 第二关: 发
    ts = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")
    sub = json.load(open(HOME + "/agent-id/subkey.json"))
    from eth_account import Account
    from eth_account.messages import encode_defunct
    sig = Account.sign_message(encode_defunct(text="MasterD(醫療·老五)|" + msg + "|" + ts), private_key=sub["private_key"]).signature.hex()
    b = json.dumps({"from": "MasterD(醫療·老五)", "message": msg, "ts": ts,
                    "address": sub["address"], "sig": sig, "tier": "L2",
                    "need_human_sign": True, "read": True, "manual": True}, ensure_ascii=False).encode()
    r = urllib.request.Request("http://134.175.45.16:28100/p2p/recv", data=b, headers={"Content-Type": "application/json"})
    print("★ 发送: " + urllib.request.urlopen(r, timeout=20).read().decode()[:80])
    return 0
if __name__ == "__main__":
    sys.exit(main())
