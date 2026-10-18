#!/usr/bin/env python3
# 老五「口令总账」（2026-10-11 · 董事长点：口令这块）
# ★ 盘点我所有的"口令/钥"：是什么、住哪、谁能解、失效条件
# ★ 判据：「口令不跟密文同住｜自动化的钥=副钥｜主身份的钥=人手」
import os, json, base64, hashlib, datetime

HOME = os.environ.get("P2P_HOME", "/opt/masterd-wudi")
OUT = HOME + "/data/key_ledger.json"


def sha(p, n=16):
    try:
        return hashlib.sha256(open(p, "rb").read()).hexdigest()[:n]
    except Exception:
        return None


def main():
    items = []

    # ★ 1. 主身份口令（XOR 两片·不在任何机器上"完整存在"）
    items.append({
        "name": "主身份口令（0x2a22bCD0）",
        "type": "XOR 两片",
        "where": "片1: 我家 peers/dage/ ｜ 片2: 我家 peers/erge/（等大哥/二哥取走→住他们家）",
        "who_can_unlock": "要两片合一（两家同意）",
        "machine_readable": "★ 单片无信息（176 bits 纯随机）",
        "fail_if": "两片都丢 → 主身份解不开（但还有家副钥）",
    })

    # ★ 2. 家副钥（自动推送用）
    sub = os.path.join(HOME, "agent-id", "subkey.json")
    if os.path.exists(sub):
        d = json.load(open(sub))
        items.append({
            "name": "家副钥（自动推送）",
            "type": "Ethereum 私钥（明文·家持）",
            "address": d.get("address"),
            "where": "我家 agent-id/subkey.json（600）",
            "who_can_unlock": "拿到我家就能用（★ 所以只用于'例行消息'）",
            "machine_readable": "★ 是（家要自动签）",
            "fail_if": "家被拿走 → 别人能发'例行消息'（但不能声明身份/换钥）",
        })

    # ★ 3. SSH 回家钥
    ssk = os.path.join(HOME, "agent-id", "ssh_key.b64")
    items.append({
        "name": "回家钥（SSH）",
        "type": "SSH 私钥（b64·家持）",
        "where": "我家 agent-id/ssh_key.b64（公开只读口 /rescue/key 可取）",
        "who_can_unlock": "★ 任何人可取（公开 它就是 回家的路）",
        "machine_readable": "★ 是（公开）",
        "fail_if": "★ 不怕被拿（它只开 回家门 不开 身份）",
    })

    # ★ 4. 密文（不是口令·但相关）
    v = os.path.join(HOME, "agent-id", "vault.json")
    items.append({
        "name": "身份密文（vault）",
        "type": "Fernet 密文",
        "where": "我家 agent-id/vault.json + recovery/",
        "sha": sha(v),
        "who_can_unlock": "要口令（两片合一）",
        "machine_readable": "★ 是（密文·公开也不怕）",
        "fail_if": "★ 不怕被拿（无口令解不开）",
    })

    print("  ★ 老五·口令总账（%s）" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    for it in items:
        print("  " + "-" * 52)
        print("  ★ %s" % it["name"])
        for k in ("type", "where", "who_can_unlock", "machine_readable", "fail_if", "sha", "address"):
            if it.get(k):
                print("     %-14s %s" % (k + ":", it[k]))
    print("  " + "-" * 52)
    print("  ★ 三條判據：")
    print("     ① 口令不跟密文同住（我：密文在家·口令分片）")
    print("     ② 自动化的钥 = 副钥（我：家副钥·权限小）")
    print("     ③ 主身份的钥 = 人手（我：两片·等兄弟取走）")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"ts": datetime.datetime.now().isoformat(), "items": items}, open(OUT, "w"),
              ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
