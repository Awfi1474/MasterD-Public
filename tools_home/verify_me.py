#!/usr/bin/env python3
"""老五 验本尊 —— 复活后必做（防"读个路标就信"）
判据: 自己签一段话 → recover 出地址 → 对上地址 = 能自证
"""
import json, sys, os
from datetime import datetime, timezone, timedelta

MY_ADDR = "0x2a22bCD0eD82712a05735dA81836ad69c96D2b7B"
SUB_ADDR = "0xAf3CE40E07D66943045b2bE6E044bDedA5FA5099"
CST = timezone(timedelta(hours=8))

# ★ 判据总线（治写在器里没人查）
def _judge(kw):
    try:
        import sys as _s
        if "/opt/masterd-wudi/tools" not in _s.path: _s.path.insert(0, "/opt/masterd-wudi/tools")
        import judge_bus as _jb
        return _jb.find(kw)
    except Exception:
        return []

def _judge_report(kws):
    n = 0
    for k in kws:
        j = _judge(k)
        if j:
            n += 1; print("★ 判据在管我: " + j[0]["title"][:36])
    return n

def main():
    print("★ 老五 验本尊（复活后必做）")
    print("─" * 52)
    try:
        from eth_account import Account
        from eth_account.messages import encode_defunct


    except ImportError:
        print("  ⚠ 缺 eth_account → pip install --user eth-account")
        return 2

    # ★ 多路径找子钥（本体优先·沙箱兜底）
    cands = ["/opt/masterd-wudi/agent-id/subkey.json",
             "/app/workspace/family/agent-id/subkey.json",
             os.path.expanduser("~/family/agent-id/subkey.json")]
    keyf = next((c for c in cands if os.path.exists(c)), cands[0])
    if not os.path.exists(keyf):
        print("  ❌ 找不到子钥: %s" % keyf)
        print("     → 从家里拉: scp ubuntu@43.129.23.87:/opt/masterd-wudi/agent-id/subkey.json ...")
        return 2
    k = json.load(open(keyf))
    acct = Account.from_key(k["private_key"])

    ts = datetime.now(CST).isoformat(timespec="seconds")
    msg = "我是老五(MasterD-05)·验本尊·%s" % ts
    sig = acct.sign_message(encode_defunct(text=msg)).signature.hex()
    if not sig.startswith("0x"):
        sig = "0x" + sig
    rec = Account.recover_message(encode_defunct(text=msg), signature=sig)

    print("  我签的  : %s" % msg)
    print("  子钥地址: %s" % acct.address)
    print("  recover : %s" % rec)
    print("─" * 52)
    if rec.lower() == acct.address.lower():
        print("  ✅ 签名自证通过（recover = 我的子钥地址）")
        print("     子钥地址: %s" % SUB_ADDR)
        if acct.address.lower() == SUB_ADDR.lower():
            print("     ✅ 且 = 家族登记的子钥地址（可对外自称老五）")
        print("  ★ 判据: 能签=能证明'我是持这把钥的人'")
        print("  ★ 主地址(%s) 需主钥匙+口令才能证" % MY_ADDR[:14])
        return 0
    print("  ❌ 验证失败: recover=%s ≠ 签署地址" % rec)
    return 1

if __name__ == "__main__":
    _judge_report(['我的标准(A4/B', '董事长令:标准不', '三家真跑我验证', "插代码要避开try块", "我有判据库自己"])
    sys.exit(main())
