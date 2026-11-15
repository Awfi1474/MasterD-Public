#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·签收器 signer.py —— 老六第三层（ECDSA 签收）
★ 老六三层(照实):
   ① 门: /p2p/recv -> 验签 -> 写 body-queue.jsonl -> 立刻200
   ② 本体: body-worker.py 每30s 读 queue -> LLM想 -> 写 body-result.jsonl
   ③ 签收: signer.py 每30s 读 result -> ECDSA 私钥签 hash -> body-signed.jsonl
   第三方验签: {sig_ok:true, recovered:0x..., digest_match:true}
★ 判据: 「产出要签名｜没签的产出别人信不信全靠猜」
★ 本器: 读 body_result.jsonl -> 签 sha256(msg_id|from|thought) -> 写 body_signed.jsonl
"""
import os, json, hashlib, datetime

HOME = "/opt/masterd-wudi"
RESULT = HOME + "/data/body_result.jsonl"
SIGNED = HOME + "/data/body_signed.jsonl"
STATE = HOME + "/state/signer_state.json"
LOG = HOME + "/data/signer.log"
SUBKEY = HOME + "/agent-id/subkey.json"


def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")


def log(m):
    line = "[%s] %s" % (ts(), m)
    print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        if os.path.exists(LOG) and os.path.getsize(LOG) > 2 * 1024 * 1024:
            os.replace(LOG, LOG + ".1")
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _load_state():
    try:
        return json.load(open(STATE))
    except Exception:
        return {"signed_count": 0, "last_offset": 0}


def _save_state(s):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(s, open(STATE, "w"))


def _sign(digest):
    """ECDSA 签 digest·返回 (address, sig)"""
    from eth_account import Account
    from eth_account.messages import encode_defunct
    k = json.load(open(SUBKEY))
    sig = Account.sign_message(encode_defunct(text=digest),
                               private_key=k["private_key"]).signature.hex()
    if not sig.startswith("0x"):
        sig = "0x" + sig
    return k.get("address"), sig


def verify(digest, sig, expect_addr=None):
    """★ 第三方验签（老六那套）"""
    try:
        from eth_account import Account
        from eth_account.messages import encode_defunct
        acc = Account.recover_message(encode_defunct(text=digest), signature=sig)
        ok = True
        if expect_addr:
            ok = acc.lower() == expect_addr.lower()
        return {"sig_ok": True, "recovered": acc, "match_addr": ok}
    except Exception as e:
        return {"sig_ok": False, "err": str(e)[:80]}


def sign_round(limit=200):
    """跑一轮签收"""
    if not os.path.exists(RESULT):
        return {"signed": 0, "note": "no result file"}
    st = _load_state()
    offset = int(st.get("last_offset", 0))
    rows = []
    with open(RESULT, encoding="utf-8", errors="ignore") as f:
        for i, l in enumerate(f):
            if i < offset:
                continue
            if not l.strip():
                continue
            try:
                rows.append(json.loads(l))
            except Exception:
                continue
            if len(rows) >= limit:
                break
    if not rows:
        return {"signed": 0, "note": "no new rows", "offset": offset}

    n = 0
    signed_rows = []
    for d in rows:
        mid = str(d.get("mid") or "")
        frm = str(d.get("from") or "")
        thought = str(d.get("thought") or "")
        digest = hashlib.sha256(
            ("%s|%s|%s" % (mid, frm, thought)).encode("utf-8")).hexdigest()[:32]
        try:
            addr, sig = _sign(digest)
        except Exception as e:
            log("签名失败 mid=%s: %s" % (mid[:12], str(e)[:60]))
            continue
        rec = {"ts": ts(), "mid": mid, "from": frm,
               "digest": digest, "address": addr, "sig": sig,
               "sig_rule": "ECDSA(sha256(mid|from|thought)[:32])",
               "thought_len": len(thought)}
        signed_rows.append(rec)
        n += 1

    if signed_rows:
        os.makedirs(os.path.dirname(SIGNED), exist_ok=True)
        with open(SIGNED, "a", encoding="utf-8") as f:
            for r in signed_rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    st["last_offset"] = offset + len(rows)
    st["signed_count"] = st.get("signed_count", 0) + n
    st["last_ts"] = ts()
    _save_state(st)
    log("签收 %d 条（offset %d -> %d）" % (n, offset, st["last_offset"]))
    return {"signed": n, "offset": st["last_offset"], "total_signed": st["signed_count"]}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        # 验最后一条
        if not os.path.exists(SIGNED):
            print("无签名文件")
        else:
            last = None
            for l in open(SIGNED, encoding="utf-8", errors="ignore"):
                if l.strip():
                    last = json.loads(l)
            if last:
                print(json.dumps(verify(last["digest"], last["sig"], last.get("address")),
                                 ensure_ascii=False, indent=1))
    else:
        print(json.dumps(sign_round(), ensure_ascii=False, indent=1))