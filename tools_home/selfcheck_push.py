#!/usr/bin/env python3
# 老五「自动推送」（用家副钥签名·2026-10-11）
# ★ 审出的矛盾：自动推送要签名 → 主身份口令不落机器 → 签不了
# ★ 解：家持"副钥"（0xAf3CE40E·权限小·可轮换）→ 自动推送用它签
# ★ 主身份钥匙永不落机器
import os, sys, json, datetime, urllib.request, urllib.error

HOME = os.environ.get("P2P_HOME", "/opt/masterd-wudi")
SUB = os.path.join(HOME, "agent-id", "subkey.json")
REPORT = os.path.join(HOME, "data", "laowu_selfcheck.json")
MY_NAME = "MasterD(生命科學·老五)"


def load_sub():
    from eth_account import Account
    d = json.load(open(SUB))
    return d


def sign_and_send(to, msg):
    from eth_account import Account
    from eth_account.messages import encode_defunct
    from datetime import timezone, timedelta
    sub = load_sub()
    ts = datetime.datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")
    payload = "%s|%s|%s" % (MY_NAME, msg, ts)
    sig = Account.sign_message(encode_defunct(text=payload), private_key=sub["private_key"]).signature.hex()
    body = json.dumps({"from": MY_NAME, "to": to, "message": msg, "ts": ts,
                       "address": sub["address"],   # ★ 副钥地址（可辨识：非主身份）
                       "sig": sig,
                       "note": "★ 此消息用'家副钥'签名（自动推送）｜主身份 0x2a22bCD0"},
                      ensure_ascii=False).encode()
    # ★ 2026-11-11 修(照老三"自检不许投会场·走独立通道"·董事长令):
    #   自检 -> 只写本地账(data/selfcheck_push.jsonl)·不投会场
    try:
        _lp = HOME + "/data/selfcheck_push.jsonl"
        with open(_lp, "a", encoding="utf-8") as _f:
            _f.write(body.decode("utf-8") + "\n")
        print("  OK 自检写本地账(不投会场·照令) -> %s" % _lp)
        return True
    except Exception as e:
        print("  ERR 写本地账失败:", str(e)[:80])
        return False


def build_text():
    r = json.load(open(REPORT))
    beats = {k: ("OK" if v["ok"] else "STOP") for k, v in r["beats"].items()}
    return ("【老五·自动体检 %s】\n\n%s\n\n机制在跳: %s\n消化率: %s\n"
            "身份(主): %s\n签名用: 家副钥 0xAf3CE40E\n\n判据: 在跳≠跳对了｜active≠在跑" % (
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                r["summary"], json.dumps(beats, ensure_ascii=False),
                json.dumps(r["digestion"], ensure_ascii=False),
                r["identity"].get("addr", "?")[:22]))


if __name__ == "__main__":
    if not os.path.exists(SUB):
        print("  无副钥 → 先跑 mk_subkey.py"); sys.exit(2)
    txt = build_text()
    open("/tmp/laowu_checkup.txt", "w").write(txt)
    ok = sign_and_send("全体", txt)
    sys.exit(0 if ok else 1)
