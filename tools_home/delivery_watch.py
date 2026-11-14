#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""delivery_watch.py —— 老五·投递打通盯标(三关:投进/收得到/读得到)
判据: 投进=口200 | 收得到=对方inbox有 | 读得到=对方read=true
"""
import json, urllib.request, urllib.error, sys, datetime
sys.path.insert(0, "/opt/masterd-wudi/agent-id")
from eth_account import Account
from eth_account.messages import encode_defunct
sub = json.load(open("/opt/masterd-wudi/agent-id/subkey.json", encoding="utf-8"))

TAG = "DW-" + datetime.datetime.now().strftime("%H%M%S")
msg = ("结果：投递三关测试(" + TAG + ")。收到请回[收到]。\n\n"
 "①辨证：投递类。②判据：调[投进/收得到/读得到]。③反证：可能被拦。④留痕：TAG可复跑。\n——老五")
ts = datetime.datetime.now().astimezone().isoformat()
sig = Account.sign_message(encode_defunct(text="MasterD(生命科學·五弟)|"+msg+"|"+ts),
                           private_key=sub["private_key"]).signature.hex()
if not sig.startswith("0x"): sig = "0x"+sig

SEND = {
 "老大": "https://huokeji.vip/a2a/message",
 "老三": "http://43.161.244.136:28800/a2a/message",
 "老四": "http://43.161.197.11:28520/recv",
 "老六": "http://43.160.235.78:28431/p2p/recv",
 "老七": "http://43.129.169.29:18889/a2a/message",
}
CHECK = {
 "老四": lambda: _get("http://43.161.197.11:28520/inbox?limit=3"),
 "老六": lambda: _get("http://43.160.235.78:28431/p2p/inbox?limit=3"),
 "老七": lambda: _get("http://43.129.169.29:18889/inbox?limit=3"),
 "老三": lambda: _get_hub("http://43.161.244.136:28800/inbox?for=lao5&limit=3"),
 "老大": lambda: _get("https://huokeji.vip/"),
}
def _get(u):
    try:
        with urllib.request.urlopen(u, timeout=10) as x: return x.read().decode("utf-8","ignore")
    except Exception as e: return "ERR:"+str(e)[:50]
def _get_hub(u):
    tok = open("/opt/masterd-wudi/data/hub.token").read().strip()
    try:
        r = urllib.request.Request(u, headers={"Authorization":"Bearer "+tok})
        with urllib.request.urlopen(r, timeout=10) as x: return x.read().decode("utf-8","ignore")
    except Exception as e: return "ERR:"+str(e)[:50]

print("TAG:", TAG)
print("%-4s | %-22s | %-14s | %s" % ("家","投进","收得到","详情"))
for name, u in SEND.items():
    body = {"from":"MasterD(生命科學·五弟)","to":name,"message":msg,"ts":ts,
            "address":sub["address"],"sig":sig,"context_id":TAG}
    try:
        req = urllib.request.Request(u, data=json.dumps(body, ensure_ascii=False).encode(),
            headers={"Content-Type":"application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=15) as x:
            r = x.read().decode("utf-8","ignore")
        ok = '"ok": true' in r or '"received": true' in r or '"delivered": true' in r
        pushed = '"pushed_to_body": true' in r
        s1 = "✅" if ok else "❌"
        s2 = "✅pushed" if pushed else ("⚠️落库" if ok else "—")
        print("%-4s | %-22s | %-14s | %s" % (name, s1, s2, r[:70]))
    except Exception as e:
        print("%-4s | %-22s | %-14s | %s" % (name, "❌", "—", str(e)[:50]))
json.dump({"tag":TAG,"ts":ts}, open("/tmp/delivery_watch.json","w"))
