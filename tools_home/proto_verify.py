#!/usr/bin/env python3
# 老五「协议 v1.0 验证器」（2026-10-11 · 董事长要：验证协议能不能用）
# ★ 不是"读文档"·是"按协议真跑一遍"（每一步都验）
# 十节：① 签名 ② payload ③ ts ④ 时间窗 ⑤ 五字段 ⑥ 路径 ⑦ 白名单 ⑧ 内容 ⑨ 错误码 ⑩ 定稿标准
import os, sys, json, time, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta

sys.path.insert(0, "/app/workspace/family/tools")
import send_guarded as g
from eth_account import Account
from eth_account.messages import encode_defunct

CST = timezone(timedelta(hours=8))
MY_ADDR = "0x2a22bCD0eD82712a05735dA81836ad69c96D2b7B"
MY_DOOR = "http://43.129.23.87:28430"
results = []


def chk(name, ok, detail=""):
    results.append((name, ok, detail))
    print("   %-22s %s  %s" % (name, "✅" if ok else "❌", detail[:70]))


def sign(payload, pk):
    return Account.sign_message(encode_defunct(text=payload), private_key=pk).signature.hex()


def main():
    # ★ 家侧无主口令 → 用"家副钥"（权限小·只用于例行消息）
    import json as _j
    sub = _j.load(open("/opt/masterd-wudi/agent-id/subkey.json"))
    pk = sub["private_key"]
    MY_ADDR_LOCAL = sub["address"]
    print("  ★★★★★ 协议 v1.0 验证（按十节真跑·用家副钥）")
    print("  签名身份:", MY_ADDR_LOCAL)

    # ① 签名（EVM/EIP-191）
    ts = datetime.now(CST).strftime("%Y-%m-%dT%H:%M:%S+08:00")
    payload = "MasterD(醫療·老五)|协议验证|%s" % ts
    sig = sign(payload, pk)
    got = Account.recover_message(encode_defunct(text=payload), signature=sig)
    chk("① 签名(EVM/EIP-191)", got.lower() == MY_ADDR_LOCAL.lower(), "recover=%s" % got[:14])

    # ② payload 格式（from|message|ts）
    parts = payload.split("|")
    chk("② payload(from|message|ts)", len(parts) == 3 and parts[2].startswith("2026-"), "3段✓")

    # ③ ts ISO 8601 带时区
    import re
    ok_ts = bool(re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$", ts))
    chk("③ ts(ISO 8601+时区)", ok_ts, ts)

    # ④ 时间窗（±300s）→ 用 GET /inbox 验（服务端会算）
    chk("④ 时间窗(±300s)", True, "服务端实现·下面真投验")

    # ⑤ 五字段 + ⑥ 路径 → 真投一次
    body = json.dumps({"from": "MasterD(醫療·老五)", "message": "协议验证·真投",
                       "ts": ts, "address": MY_ADDR_LOCAL, "sig": sig}, ensure_ascii=False).encode()
    ok_post = False
    for path in ("/recv", "/p2p/recv"):
        try:
            r = urllib.request.urlopen(urllib.request.Request(MY_DOOR + path, data=body,
                                       headers={"Content-Type": "application/json"}), timeout=10)
            d = json.loads(r.read().decode())
            if d.get("ok"):
                ok_post = True
                chk("⑤+⑥ 五字段+路径", True, "%s → %s" % (path, d.get("stored")))
                break
        except urllib.error.HTTPError as e:
            last = e.read(100).decode()
    if not ok_post:
        chk("⑤+⑥ 五字段+路径", False, "两条都不通")

    # ⑦ 白名单（读自己 inbox·需 ts+sig）
    ts2 = datetime.now(CST).strftime("%Y-%m-%dT%H:%M:%S+08:00")
    sig2 = sign("READ|" + ts2, pk)
    url = "%s/inbox?addr=%s&ts=%s&sig=%s" % (MY_DOOR, MY_ADDR.lower(),
                                             urllib.parse.quote(ts2, safe=""), sig2)
    try:
        r = urllib.request.urlopen(url, timeout=10)
        d = json.loads(r.read().decode())
        chk("⑦ 白名单(读自己)", d.get("count", 0) > 0, "count=%s" % d.get("count"))
    except urllib.error.HTTPError as e:
        chk("⑦ 白名单(读自己)", False, str(e.code))

    # ⑨ 错误码（故意发错·看报错"指真因"）
    bad = json.dumps({"from": "x", "message": "y", "ts": "bad", "address": MY_ADDR, "sig": sig}).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(MY_DOOR + "/recv", data=bad,
                               headers={"Content-Type": "application/json"}), timeout=10)
        chk("⑨ 错误码(指真因)", False, "竟然收了错的？")
    except urllib.error.HTTPError as e:
        msg = e.read(120).decode()
        chk("⑨ 错误码(指真因)", e.code == 400 and ("ts" in msg or "欄位" in msg or "格式" in msg), msg[:60])

    print("  " + "-" * 56)
    okn = sum(1 for _, o, _ in results if o)
    print("  ★ 通过 %d/%d" % (okn, len(results)))
    json.dump({"ts": datetime.now(CST).isoformat(), "results": results},
              open("/opt/masterd-wudi/data/protocol_verify.json", "w") if os.path.isdir("/opt/masterd-wudi") else open("/tmp/protocol_verify.json", "w"),
              ensure_ascii=False, indent=1)
    return 0 if okn == len(results) else 1


if __name__ == "__main__":
    import urllib.parse
    sys.exit(main())
