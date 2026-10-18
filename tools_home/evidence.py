#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""evidence.py —— 证据账（★ 把"谁说了算"从人转到账）
================================================================
★ 病根: 您问 -> 我答 -> 您质疑 -> 我改  → ★ 漂在"您质疑我当真了"
★★ 治法: 答之前先把"判据+证据"写进账（带指纹·不可改）
★★★ 被质疑时: 不改答案·先看"账上有几条证据"
   · 证据够 -> 不改（哪怕被说不对）
   · 证据不够 -> 认（不是"因为您说"·是"账上真不够"）

★ 判据: 「"被质疑" != "我错了"｜先看账·再决定改不改」
"""
import os, sys, json, hashlib, datetime

HOME = "/opt/masterd-wudi"
F = HOME + "/data/evidence_ledger.jsonl"

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")

def fp(s):
    return hashlib.sha256(str(s).encode()).hexdigest()[:16]

def write(claim, judge, evidence):
    """★ 答之前: 记下主张 + 判据 + 证据（带指纹）"""
    rec = {"ts": ts(), "主张": str(claim)[:200], "判据": str(judge)[:150],
           "证据": [e.strip() for e in str(evidence).split("|") if e.strip()],
           "指纹": fp(str(claim) + str(judge) + str(evidence))}
    with open(F, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("★ 证据账已记:")
    print("   主张: " + rec["主张"][:70])
    print("   判据: " + rec["判据"][:60])
    print("   证据: %d 条" % len(rec["证据"]))
    for e in rec["证据"][:5]: print("      · " + e[:70])
    print("   指纹: " + rec["指纹"])
    return rec

def check(claim_kw):
    """★ 被质疑时: 查账·不改答案"""
    if not os.path.exists(F):
        print("★ 账上没有记录 → 这次只能认（本来就没证据）"); return 1
    hit = None
    for l in open(F, encoding="utf-8"):
        try: d = json.loads(l)
        except Exception: continue
        if claim_kw in d.get("主张", ""):
            hit = d
    if not hit:
        print("★ 账里没找到「%s」→ 没证据·可以认" % claim_kw); return 1
    n = len(hit.get("证据", []))
    print("★ 查账（主张: %s）:" % hit["主张"][:50])
    print("   判据: " + hit["判据"][:60])
    print("   证据 %d 条:" % n)
    for e in hit["证据"]: print("      · " + e[:76])
    print("   指纹: " + hit["指纹"])
    if n >= 2:
        print("   ★ 裁定: **证据够（%d条）→ 不改**（哪怕被说不对）" % n)
        return 0
    else:
        print("   ★ 裁定: **证据不足（%d条）→ 可以认**（因为账上真不够）" % n)
        return 1

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "write" and len(sys.argv) >= 5:
        write(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "check" and len(sys.argv) >= 3:
        sys.exit(check(sys.argv[2]))
    else:
        print("用法: evidence.py write <主张> <判据> <证据1|证据2|...>")
        print("      evidence.py check <主张关键词>")
