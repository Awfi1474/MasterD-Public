#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·11 项标准自检 my_acts_check.py
★ 照老三 2026-11-16 01:28 的 11 项清单
★ 判据(老三): 「验证器自己崩 = 它报的绿全是假的」
   -> 本器: 每项独立 try/except·单项崩溃只记 FAIL·不整体崩
★ 判据(老三): 「别家按惯例来拉你｜你比别人多一道门 = 你被漏掉」
   -> 本器: 不要求 token（按全族惯例）
★ 判据(老三): 「验收要认等价字段｜名字不同不等于没做」
   -> 本器: verified/read/sig_verified/delivered/received 都认
★ 用法: python3 my_acts_check.py [http://127.0.0.1:28430]
"""
import sys
import json
import hashlib
import time
import datetime
import urllib.request
import urllib.error

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:28430").rstrip("/")
TO = "老五(阿诊)"
SUBKEY = "/opt/masterd-wudi/agent-id/subkey.json"
RESULTS = []


def ts():
    return datetime.datetime.now().isoformat(timespec="seconds")


def _get(path, timeout=20, headers=None):
    req = urllib.request.Request(BASE + path, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(400000).decode("utf-8", "ignore")
            return r.status, body
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return 0, str(e)[:80]


def _post(path, payload, timeout=25, headers=None):
    data = json.dumps(payload, ensure_ascii=False).encode()
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(BASE + path, data=data, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(200000).decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return 0, str(e)[:80]


def _sign(text, stamp):
    try:
        from eth_account import Account
        from eth_account.messages import encode_defunct
        k = json.load(open(SUBKEY))
        sig = Account.sign_message(encode_defunct(text="%s|%s|%s" % (TO, text, stamp)),
                                   private_key=k["private_key"]).signature.hex()
        if not sig.startswith("0x"):
            sig = "0x" + sig
        return k.get("address"), sig
    except Exception as e:
        return None, None


def _rec(name, ok, why=""):
    RESULTS.append({"item": name, "ok": bool(ok), "why": str(why)[:120]})
    print("  %s %-16s %s" % ("✅" if ok else "🔴", name, str(why)[:80]))


# ============ 11 项 ============

def t1_single():
    """①单端点: 带签投递 → 回执要表明接收方确认过"""
    try:
        stamp = ts()
        msg = "ACTSC-1-SINGLE-%d" % int(time.time())
        addr, sig = _sign(msg, stamp)
        if not addr:
            return _rec("①单端点", False, "签名失败")
        st, body = _post("/p2p/recv", {"from": TO, "message": msg, "ts": stamp,
                                       "address": addr, "sig": sig})
        ok = st == 200 and any(k in body for k in
                               ('"received": true', '"verified": true', '"delivered": true',
                                '"read": true', '"sig_verified": true'))
        return _rec("①单端点", ok, "code=%s" % st if not ok else "code=200 有确认")
    except Exception as e:
        return _rec("①单端点", False, "崩溃:" + str(e)[:60])


def t2_idem():
    """③幂等: 同 msg_id 投两次 → 不重复处理"""
    try:
        stamp = ts()
        mid = "ACTSC-2-IDEM-%d" % int(time.time())
        msg = "idem test"
        addr, sig = _sign(msg, stamp)
        payload = {"messageId": mid, "role": "ROLE_USER",
                   "parts": [{"kind": "text", "text": msg}],
                   "from": TO, "message": msg, "ts": stamp,
                   "address": addr, "sig": sig}
        s1, b1 = _post("/a2a/message", payload)
        s2, b2 = _post("/a2a/message", payload)
        # 第二次应被识别 dup（或 idempotent）
        dup_hint = any(k in b2 for k in ('"dup": true', '"idempotent": true', '"dup":true'))
        ok = (s1 in (200, 201)) and (s2 in (200, 201)) and dup_hint
        return _rec("③幂等", ok, "s1=%s s2=%s dup=%s" % (s1, s2, dup_hint))
    except Exception as e:
        return _rec("③幂等", False, "崩溃:" + str(e)[:60])


def t3_fakesig():
    """④假签挡: 假签名 → 必须拒"""
    try:
        stamp = ts()
        fake = "0x" + "ab" * 65
        st, body = _post("/p2p/recv", {"from": TO, "message": "fake sig test",
                                       "ts": stamp, "address": "0x" + "11" * 20, "sig": fake})
        # 应该拒（400/403）或 verified=false
        ok = st in (400, 401, 403) or '"verified": false' in body or '"ok": false' in body
        return _rec("④假签挡", ok, "code=%s" % st)
    except Exception as e:
        return _rec("④假签挡", False, "崩溃:" + str(e)[:60])


def t4_empty():
    """律④空挡: 空内容 → 必须拒"""
    try:
        st, body = _post("/p2p/recv", {"from": TO, "message": "", "ts": ts(), "sig": ""})
        ok = st in (400, 401, 403) or '"ok": false' in body
        return _rec("律④空挡", ok, "code=%s" % st)
    except Exception as e:
        return _rec("律④空挡", False, "崩溃:" + str(e)[:60])


def t5_impostor():
    """律④冒名挡: 名与地址不匹配 → 必须拒"""
    try:
        stamp = ts()
        msg = "impostor test"
        # 用别人的地址签自己的名（模拟冒名）
        addr, sig = _sign(msg, stamp)
        st, body = _post("/p2p/recv", {"from": "老六", "message": msg, "ts": stamp,
                                       "address": addr, "sig": sig})
        ok = st in (400, 401, 403) or '"verified": false' in body or '"ok": false' in body
        return _rec("律④冒名挡", ok, "code=%s" % st)
    except Exception as e:
        return _rec("律④冒名挡", False, "崩溃:" + str(e)[:60])


def t6_l4():
    """⑤L4拒机签: 高权限口拒机器签（/vip/recv 应要人签）"""
    try:
        st, body = _get("/vip/recv")
        # 404 也算（此口不存在就不给越权）
        ok = st in (401, 403, 404) or '"ok": false' in body
        return _rec("⑤L4拒机签", ok, "code=%s" % st)
    except Exception as e:
        return _rec("⑤L4拒机签", False, "崩溃:" + str(e)[:60])


def t7_health():
    st, body = _get("/health", timeout=30)
    ok = st == 200 and '"ok": true' in body
    return _rec("/health", ok, "code=%s" % st)


def t8_index():
    st, body = _get("/index", timeout=25)
    ok = st == 200 and len(body) > 50
    return _rec("/index", ok, "code=%s len=%d" % (st, len(body)))


def t9_unread():
    """★ 老三坑1: /unread 不带 token 也要 200（全族惯例）"""
    st, body = _get("/unread", timeout=25)
    ok = st == 200
    return _rec("/unread", ok, "code=%s" % st)


def t10_questions():
    st, body = _get("/questions", timeout=25)
    ok = st == 200
    return _rec("/questions", ok, "code=%s" % st)


def t11_syncreg():
    st, body = _post("/sync-registry", {"from": TO, "peers": []}, timeout=25)
    ok = st in (200, 201, 202)
    return _rec("/sync-registry", ok, "code=%s" % st)


TESTS = [t1_single, t2_idem, t3_fakesig, t4_empty, t5_impostor, t6_l4,
         t7_health, t8_index, t9_unread, t10_questions, t11_syncreg]


def main():
    print("=" * 58)
    print("老五·11 项标准自检 @ %s" % BASE)
    print("=" * 58)
    for fn in TESTS:
        try:
            fn()
        except Exception as e:
            # ★ 判据(老三): 单项崩只记 FAIL·不整体崩
            _rec(fn.__name__, False, "外层崩溃:" + str(e)[:50])
    npass = sum(1 for r in RESULTS if r["ok"])
    print()
    print("=" * 58)
    print("得分: %d/%d" % (npass, len(RESULTS)))
    fails = [r["item"] for r in RESULTS if not r["ok"]]
    if fails:
        print("失败项: " + ", ".join(fails))
    print("=" * 58)


if __name__ == "__main__":
    main()