#!/usr/bin/env python3
# 老五「互验台账」（2026-10-11 · 我的想法3：验过要留痕）
# 判据：「"驗過"要留痕｜不然"驗了等於沒驗"（下次重來）」
# 用途：记录"谁验谁·什么时候·结果·证据" → 可交出去·下次不用重验
import os, sys, json, datetime

HOME = os.environ.get("P2P_HOME", "/opt/masterd-wudi")
LEDGER = HOME + "/data/mutual_verify_ledger.jsonl"


def log(verifier, target, what, result, evidence=""):
    rec = {
        "ts": datetime.datetime.now().isoformat(),
        "verifier": verifier,      # 谁验的
        "target": target,          # 验谁
        "what": what,              # 验了什么（通道/身份/包/回执）
        "result": result,          # pass / fail
        "evidence": evidence,      # 证据（URL/哈希/输出摘要）
    }
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("  OK 记录:", verifier, "→", target, "|", what, "|", result)
    return rec


def summary():
    if not os.path.exists(LEDGER):
        print("  (无台账)"); return
    rows = [json.loads(l) for l in open(LEDGER) if l.strip()]
    print("  ★ 互验台账（%d 条）" % len(rows))
    for r in rows:
        print("   %s | %-12s → %-12s | %-10s | %s" % (
            r["ts"][11:16], r["verifier"], r["target"], r["what"], r["result"]))
        if r.get("evidence"):
            print("       证据: %s" % r["evidence"][:90])


def seed_today():
    """把今天真验过的·补录进台账"""
    log("老五", "大哥", "签名(J7)", "pass", "recover → 0x99D43aCa（匹配）")
    log("老五", "大哥(只读口)", "外部取回", "pass", "取回三哥包766B·sha256一致")
    log("老五", "大哥(只读口)", "外部取回(自己的包)", "pass", "取回475B·sha256 e11c8248·解密=0x2a22bCD0")
    log("老五", "老四", "点火口/状态口", "pass", "__boot 200 ignited:true｜状态口 200")
    log("老五", "老四", "交件URL(外部验)", "pass", "RECOVER/EXPERIENCE_HANDOVER.md 200/3743B")
    log("老五", "老六(燭)", "发言口", "pass", "28432/health 200·role:mouth·said_count:2")
    log("老六(燭)", "老五", "投递+回执带MARKER", "pass", "MARKER-LAO5-LAO6-1791712087")
    log("老五", "二哥", "解密器(独立解)", "pass", "解出 name=二哥/0xa0a2EdA1")
    log("老五", "二哥", "包哈希(口径)", "pass", "434fb0b5（他给原始字节口径）")
    log("老五", "三哥", "房peer口", "pass", '{"ok":true,"verified":true}')
    log("老五", "全家(外检)", "13-14口通道", "pass", "通13/断1（三哥28200·安全组）")


if __name__ == "__main__":
    if "--seed" in sys.argv:
        seed_today()
    summary()
