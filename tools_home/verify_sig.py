#!/usr/bin/env python3
# 老五「验签器」（2026-10-11 · 照三哥"真刀真枪"标准建的）
# 用途：收到任何消息 → 真验"签名对不对"（不靠平台说的"已验证"）
# 判据：平台说"已验证" != 我自己验过｜要自己 recover(sig) == from 地址
import os, sys, json, argparse

try:
    from eth_account import Account
    from eth_account.messages import encode_defunct
except Exception as e:
    print("  需 eth_account:", e); sys.exit(2)


def recover(payload, sig_hex):
    try:
        return Account.recover_message(encode_defunct(text=payload), signature=sig_hex)
    except Exception as e:
        return "ERR:" + str(e)[:40]


def check(addr, payload, sig_hex):
    got = recover(payload, sig_hex)
    return (got.lower() == str(addr).lower()), got


def verify_inbox(path):
    n_ok = n_bad = n_nosig = 0
    bad = []
    for l in open(path):
        l = l.strip()
        if not l:
            continue
        try:
            d = json.loads(l)
        except Exception:
            continue
        if "P2P→A2A" in str(d.get("message", "")):
            continue
        addr = d.get("address") or d.get("addr")
        sig = d.get("sig")
        frm, msg, ts = d.get("from"), d.get("message"), d.get("ts")
        if not sig or not addr:
            n_nosig += 1
            continue
        ok, got = check(addr, "%s|%s|%s" % (frm, msg, ts), sig)
        if ok:
            n_ok += 1
        else:
            n_bad += 1
            bad.append((ts, frm, addr, got))
    print("  验签结果：OK %d | BAD %d | 无签名 %d" % (n_ok, n_bad, n_nosig))
    for it in bad[-5:]:
        print("   BAD", str(it[0])[:19], it[1], "声明:", str(it[2])[:22], "实际:", str(it[3])[:22])
    return n_bad == 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--inbox", default="/opt/masterd-wudi/data/inbox.jsonl")
    a = ap.parse_args()
    sys.exit(0 if verify_inbox(a.inbox) else 1)
