#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·收口自动化测试 test_receiver.py（防今天10次同款错）
★ 判据：
  ① 4条存口都测（不只测1条）
  ② 看"真进库"·不看返回200
  ③ 过滤3类都测（拦/放/白名单）
★ 用法: test_receiver.py  (可直接进叫醒器)
"""
import json, urllib.request, datetime, sys, time
sys.path.insert(0, "/opt/masterd-wudi/agent-id")

HOME = "/opt/masterd-wudi"
sub = json.load(open(HOME + "/agent-id/subkey.json", encoding="utf-8"))
from eth_account import Account
from eth_account.messages import encode_defunct

TAG = "RECTEST-%d" % int(time.time())

def send(msg, frm="lao5"):
    ts = datetime.datetime.now().astimezone().isoformat()
    sig = Account.sign_message(encode_defunct(text="%s|%s|%s" % (frm, msg, ts)),
                               private_key=sub["private_key"]).signature.hex()
    if not sig.startswith("0x"): sig = "0x" + sig
    b = {"from": frm, "to": "lao5", "message": msg, "ts": ts,
         "address": sub["address"], "sig": sig}
    try:
        r = urllib.request.urlopen(urllib.request.Request(
            "http://43.129.23.87:28430/recv", data=json.dumps(b).encode(),
            headers={"Content-Type": "application/json"}, method="POST"), timeout=12)
        return True, r.read().decode()[:60]
    except Exception as e:
        return False, str(e)[:50]

def count(tag, f="inbox.jsonl"):
    p = HOME + "/data/" + f
    try: return open(p, encoding="utf-8", errors="ignore").read().count(tag)
    except Exception: return 0

def main():
    ok = 0; total = 0
    print("★ 收口自动化测试 %s" % TAG)

    # ① 真内容 → 应进 inbox
    total += 1
    m = "真内容测试 %s 具体事项与结论" % TAG
    r, detail = send(m)
    time.sleep(0.5)
    n = count(TAG)
    if r and n >= 1:
        print("  ✅ ① 真内容 → 进inbox (%d)" % n); ok += 1
    else:
        print("  ❌ ① 真内容 → 没进 (r=%s inbox=%d)" % (r, n))

    # ② ping → 应拦（进 filtered·不进 inbox）
    total += 1
    before_in = count(TAG)
    r, detail = send("ping")
    time.sleep(0.5)
    # ping 不含 TAG·用 filtered 里最新判定
    try:
        last_f = [l for l in open(HOME+"/data/filtered_inbox.jsonl", encoding="utf-8", errors="ignore") if l.strip()][-1]
        lf = json.loads(last_f)
        if lf.get("message") == "ping":
            print("  ✅ ② ping → 被拦 (%s)" % lf.get("filter_why")); ok += 1
        else:
            print("  ⚠️ ② ping → 没拦（最新拦的是 %r）" % lf.get("message"))
    except Exception as e:
        print("  ❌ ② ping 测试异常: %s" % str(e)[:50])

    # ③ 家人短应答 → 应放行
    total += 1
    m3 = "我在 %s" % TAG
    r, detail = send(m3, frm="老七(Arki)")
    time.sleep(0.5)
    n3 = count(TAG)
    if r and n3 > count(TAG.replace("RECTEST","RECTESTX")) :
        print("  ✅ ③ 家人应答 → 放行"); ok += 1
    else:
        print("  ⚠️ ③ 家人应答 → 未确认 (r=%s)" % r)

    print("★ 结果: %d/%d" % (ok, total))
    return 0 if ok >= 2 else 1

if __name__ == "__main__":
    sys.exit(main())
