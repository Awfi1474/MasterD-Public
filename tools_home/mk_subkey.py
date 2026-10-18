#!/usr/bin/env python3
# 老五「家副钥」：家自动推送用的"签名钥"（不是主身份）
# ★ 2026-10-11 审出的矛盾：自动推送要签名 → 要口令 → 口令落机器 → 违反"口令不落机器"
# ★ 真解：家持"副钥"（实名·权限小·可 rotate·不是主身份）→ 自动推送用它签
# ★ 主身份（0x2a22bCD0）→ 口令永不落机器（分片+人手）
# 判据：「自动化的钥 = 副钥｜主身份的钥 = 人手｜两把钥·两种用途」
import os, json, base64, datetime

HOME = os.environ.get("P2P_HOME", "/opt/masterd-wudi")
KEYS = os.path.join(HOME, "agent-id")
MAIN = os.path.join(KEYS, "vault.json")              # 主身份（密文·口令不在此机器）
SUB = os.path.join(KEYS, "subkey.json")              # ★ 家副钥（家能解·用于自动签）


def make_subkey():
    from eth_account import Account
    acct = Account.create()
    d = {
        "name": "MasterD(医疗·五弟)·家副钥",
        "address": acct.address,
        "private_key": acct.key.hex(),
        "purpose": "自动推送签名（体检/消化率/报到）",
        "limits": "★ 只用于'家自动发的例行消息'｜不用于'身份声明/换钥/转移'",
        "main_identity": "0x2a22bCD0eD82712a05735dA81836ad69c96D2b7B",
        "created": datetime.datetime.now().isoformat(),
        "rotate": "建议 30 天轮换一次",
        "judge": "自动化的钥=副钥｜主身份的钥=人手｜两把钥两种用途",
    }
    os.makedirs(KEYS, exist_ok=True)
    json.dump(d, open(SUB, "w"), ensure_ascii=False, indent=1)
    os.chmod(SUB, 0o600)
    print("  OK 家副钥已建:", d["address"])
    print("  ★ 用途:", d["purpose"])
    print("  ★ 限制:", d["limits"])
    return d


if __name__ == "__main__":
    import sys
    if os.path.exists(SUB):
        d = json.load(open(SUB))
        print("  已有家副钥:", d["address"])
    else:
        make_subkey()
