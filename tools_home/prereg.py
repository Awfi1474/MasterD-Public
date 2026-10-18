#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""prereg.py —— 预注册器（★ 三哥 C9 · 我判"收"）
================================================================
★ 三哥 C9: ★「**预注册**：事前写下·不可改｜事后对账有选择权」
★ 病根（三哥说·我们都踩过）: ★「事后挑一个'我早说过' → 假验算」
★ 我认的理由: ★ 我今晚就有"事后改判据"（分母涨了才补接器）→ ★ 这就是"事后有选择权"

★ 本器做什么:
  ★ ① `write <事> <预期>` → ★ 事前写下"我预期什么"（带时间戳·不可改）
  ★ ★ ② `check <事> <实际>` → ★ 事后对账（对不上 = 照实报错·不许改预期）
  ★ ★ ★ ③ `list` → ★ 看所有"预注册了没对账"的

★ 判据（我认三哥这条）:
  ★「**事前写下 = 有选择权｜事后补 = 自己骗自己**」
  ★★「**预注册不改｜要改 = 新开一条**」
"""
import json, os, sys, datetime

HOME = "/opt/masterd-wudi"
F = os.path.join(HOME, "data", "prereg.jsonl")

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")

def write(what, expect):
    rec = {"ts": ts(), "what": what, "expect": expect, "status": "待对账"}
    with open(F, "a") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("★ 预注册（不可改）: [%s] 预期=%s" % (what, expect))

def check(what, actual):
    lines = [json.loads(l) for l in open(F, encoding="utf-8").read().splitlines() if l.strip()]
    hit = None
    for r in lines[::-1]:
        if r["what"] == what and r["status"] == "待对账": hit = r; break
    if not hit:
        print("★ 没找到待对账的预注册: %s（★ 不许事后补·要 new 一条）" % what); return
    ok = str(actual) == str(hit["expect"])
    print("%s 对账 [%s]: 预期=%s 实际=%s → %s" % ("✅" if ok else "🔴", what, hit["expect"], actual, "对上" if ok else "★ 对不上·照实报错"))
    return ok

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "write" and len(sys.argv) > 3: write(sys.argv[2], sys.argv[3])
    elif cmd == "check" and len(sys.argv) > 3: check(sys.argv[2], sys.argv[3])
    else:
        if not os.path.exists(F): print("★ 还没预注册过"); return 0
        for l in open(F, encoding="utf-8").read().splitlines()[-10:]:
            r = json.loads(l); print("  [%s] %s → 预期=%s (%s)" % (r["ts"][11:16], r["what"], r["expect"], r["status"]))
    return 0

if __name__ == "__main__":
    sys.exit(main())
