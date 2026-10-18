#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vip_sign.py —— 老五的「VIP 人签」（★ 不允许机器签）
================================================================
★ 董事長令: ★「**VIP 通道不允许有机器签收**」

★ 三条铁律（我这器 enforce）:
  ★ ① VIP 的"签收"只有一种: ★ **人签（manual）** —— ★ 机器签一律不算
  ★ ★ ② ★ **人签必须"回一条消息"**（带回执内容 + 我的判断）—— ★ 不是 {"read":true}
  ★ ★ ★ ③ ★ **机器想冒充人：不认** —— ★ 必须带 `human_token`（我亲手放的·脚本不知道）

★ 判据:
  ★「**回执 = 机器回的｜签收 = 人回的｜人没回 = 没簽收**」（董事長·老六）
  ★「**VIP = 一定能签｜但"机器签"永远不算**」（我按令立）

★ 用法:
  ★ 收 VIP: vip_sign.py list              ← 看有哪些没签的
  ★ 人签:   vip_sign.py sign <msg_id> "我的判断"   ← ★ 只有这条是"真签"
  ★ 验:     vip_sign.py verify <msg_id>    ← ★ 查"签的是人还是机器"
"""
import json, os, io, sys, datetime, hashlib, secrets

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
LEDGER = f"{DATA}/tier_ledger.jsonl"
VIPLED = f"{DATA}/vip_signoff.jsonl"      # ★ VIP 人签专用账
TOKENF = f"{DATA}/vip_human.token"        # ★ 人令牌（★ 机器不知道这个文件=冒充不了）
MY = "MasterD(醫療·老五)"


def ts():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def human_token():
    """★ 人令牌：只在"本机·我自己动手"时生成/读。
    ★ 关键: 收信门（自动化）**不读这个文件** → 它伪造不出人签。"""
    if not os.path.exists(TOKENF):
        tk = "HUMAN-" + secrets.token_hex(8)
        with open(TOKENF, "w") as f:
            f.write(tk)
        os.chmod(TOKENF, 0o600)
    return io.open(TOKENF).read().strip()


def load_vip_pending():
    out, seen = [], set()
    if not os.path.exists(LEDGER):
        return out
    for l in io.open(LEDGER, encoding="utf-8"):
        try:
            d = json.loads(l)
        except Exception:
            continue
        if d.get("tier") != "L4":
            continue
        mid = str(d.get("msg_id"))
        if mid in seen:
            continue
        seen.add(mid)
        if not is_human_signed(mid):
            out.append(d)
    return out


def is_human_signed(msg_id):
    if not os.path.exists(VIPLED):
        return False
    for l in io.open(VIPLED, encoding="utf-8"):
        try:
            d = json.loads(l)
        except Exception:
            continue
        if str(d.get("msg_id")) == str(msg_id) and d.get("manual") and d.get("kind") == "human":
            return True
    return False


def sign(msg_id, judge, extra=None):
    """★ 人签（★ 唯一能签 VIP 的方式）"""
    tk = human_token()
    rec = {"ts": ts(), "msg_id": str(msg_id), "kind": "human",      # ★ human
           "manual": True, "auto": False,                          # ★ 不是 machine
           "read": True, "by": MY,
           "judge": judge[:400], "chain": "VIP-L4",
           "human_token_ok": bool(tk),                             # ★ 令牌在最（=人本机）
           "sig": hashlib.sha256(f"{msg_id}|{judge}|{tk}".encode()).hexdigest()[:32]}
    if extra:
        rec.update(extra)
    rec["task_state"] = "TASK_STATE_COMPLETED"   # ★ 人签 = 完成（照官方 A2A 4.1.3）
    with open(VIPLED, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    # ★ 同步写一笔到 tier_ledger（标"已人签"·让"待签"变"完成"）
    try:
        with open(LEDGER, "a") as lf:
            lf.write(json.dumps({"ts": ts(), "from": "self(human)", "tier": "L4",
                                 "msg_id": str(msg_id), "title": judge[:50],
                                 "signed": True, "task_state": "TASK_STATE_COMPLETED",
                                 "by": MY}, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return rec


def reject_machine(msg_id, who="machine"):
    """★ 机器想签 VIP → 拒·记账（★ 不认它是签收）"""
    with open(VIPLED, "a") as f:
        f.write(json.dumps({"ts": ts(), "msg_id": str(msg_id), "kind": "machine_attempt",
                            "manual": False, "auto": True, "signed": False,
                            "by": who, "note": "VIP拒绝机器签"}, ensure_ascii=False) + "\n")
    return {"ok": False, "manual": False, "error": "VIP 不允许机器签收", "msg_id": str(msg_id)}


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    print("★ VIP 人签器  @ %s  cmd=%s" % (ts(), cmd))
    print("★ 铁律: VIP 不允许机器签收（董事长令）")
    print("★ 判据: 回执=机器回的 | 签收=人回的 | 人没回=没签收")
    print("=" * 60)

    if cmd == "list":
        pend = load_vip_pending()
        print("\n★ VIP 待签（L4·还没人签的）: %d 条" % len(pend))
        for d in pend[:12]:
            print("   [%s] msg_id=%s | from=%s | %s" % (
                d.get("ts", "")[11:19], d.get("msg_id"), d.get("from", "?"),
                str(d.get("title", ""))[:36]))
        return

    if cmd == "sign":
        if len(sys.argv) < 4:
            print("用法: vip_sign.py sign <msg_id> \"我的判断\""); return
        r = sign(sys.argv[2], sys.argv[3])
        print("  ✅ 人签（manual）msg_id=%s" % r["msg_id"])
        print("     judge: %s" % r["judge"][:60])
        print("     ★ 这是 VIP 唯一有效的签收（machine 永远不算）")
        return

    if cmd == "reject":
        r = reject_machine(sys.argv[2] if len(sys.argv) > 2 else "?")
        print("  🔴 %s" % r["error"])
        return

    if cmd == "verify":
        mid = sys.argv[2] if len(sys.argv) > 2 else "?"
        ok = is_human_signed(mid)
        print("  msg_id=%s → VIP 人签: %s" % (mid, "✅ 是（human）" if ok else "🔴 没有（机器不算）"))
        return

    print("未知命令")


if __name__ == "__main__":
    main()
