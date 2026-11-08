#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_push_body.py —— 「门推本体」自检（老五·2026-11-08）
================================================================
★ 治好:我今天手测一次'门推本体'通了·但之后没再核(老三:"每次门响都得再核")
★ 它做什么:
  ① 投一条真信(带签名)到自己门
  ② 等几秒 → 看 body_once.jsonl 有没有新增(本体真想了)
  ③ 报:门推本体 通/不通 + 凭据
★ 判据: 「一次通 != 每次通|门响就得核」
================================================================
"""
import json, urllib.request, datetime, time, os, subprocess
HOME = "/opt/masterd-wudi"
ONCE = HOME + "/data/body_once.jsonl"

def sign_msg(frm, msg, ts):
    try:
        from eth_account import Account
        from eth_account.messages import encode_defunct
        sub = json.load(open(HOME + "/agent-id/subkey.json"))
        sig = Account.sign_message(encode_defunct(text=frm+"|"+msg+"|"+ts),
                                   private_key=sub["private_key"]).signature.hex()
        return sub["address"], sig
    except Exception as e:
        return None, None

def main():
    print("★ 门推本体自检 @", datetime.datetime.now().strftime("%F %T"))
    before = 0
    if os.path.exists(ONCE): before = sum(1 for _ in open(ONCE))
    ts = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")
    frm, msg = "老五(阿诊)", "状态·门推本体自检"
    addr, sig = sign_msg(frm, msg, ts)
    if not sig:
        print("  🔴 签名失败(无法投信)"); return 1
    body = json.dumps({"from":frm,"to":frm,"message":msg,"ts":ts,"address":addr,"sig":sig}, ensure_ascii=False).encode()
    try:
        r = urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:28430/recv", data=body,
            headers={"Content-Type":"application/json"}), timeout=15).read().decode()
        print("  ① 投信:", r[:100])
    except Exception as e:
        print("  🔴 投信失败:", str(e)[:80]); return 1
    time.sleep(6)
    after = 0
    if os.path.exists(ONCE): after = sum(1 for _ in open(ONCE))
    if after > before:
        print("  ② 本体真想了: body_once %d→%d ✅ 门推本体=通" % (before, after))
        print("     证据:", open(ONCE).read().strip().splitlines()[-1][:120])
        return 0
    else:
        print("  ② 门没推本体: body_once %d→%d 🔴 不通" % (before, after))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
