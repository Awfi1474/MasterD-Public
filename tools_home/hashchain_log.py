#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·哈希链日志 hashchain_log.py（照 arXiv:2512.20985 IEEE ICCA 2025）
★ 缘起：那篇论文说治理层要「immutable auditability」（不可篡改审计）
   我家日志全是普通 jsonl·谁都能改 → 补"哈希链"（不引链·轻量版）

★ 判据（我的）：
  「可改 = 可赖｜改一条必断链｜断链=被篡改」
★ 用法: hashchain_log.py append <文件> <json内容>
       hashchain_log.py verify <文件>
"""
import json, hashlib, os, sys, datetime, fcntl

def _norm(content):
    """★ 统一归一(2026-11-13·照实: 迁移和校验算法不一致导致全坏链)
       判据: 同一份内容必须算出同一个 hash -> 一律 json.dumps(sort_keys=True)"""
    if isinstance(content, (dict, list)):
        return json.dumps(content, ensure_ascii=False, sort_keys=True)
    return str(content)

def _line_hash(prev_hash, content):
    return hashlib.sha256((str(prev_hash) + "|" + _norm(content)).encode("utf-8")).hexdigest()[:32]

def get_prev(path):
    last = None
    if os.path.exists(path):
        for l in open(path, encoding="utf-8", errors="ignore"):
            if l.strip():
                try: last = json.loads(l)
                except Exception: pass
    return (last.get("h") if last else "GENESIS")

def append(path, content):
    # ★ 2026-11-15 加(照实: 并发写导致 row848 prev错位=断链)
    #   判据: 读prev→写·必须原子(加锁)·否则两条同时读到同一prev
    _lk = path + ".lock"
    with open(_lk, "a") as _lf:
        fcntl.flock(_lf.fileno(), fcntl.LOCK_EX)
        try:
            prev = get_prev(path)
            rec = {"ts": datetime.datetime.now().isoformat(timespec="seconds"),
                   "prev": prev, "c": content, "h": _line_hash(prev, content)}
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                os.fsync(f.fileno())
        finally:
            fcntl.flock(_lf.fileno(), fcntl.LOCK_UN)
    return rec

def verify(path):
    if not os.path.exists(path): return (0, 0, "文件不存在")
    prev = "GENESIS"; n = 0; bad = []
    for i, l in enumerate(open(path, encoding="utf-8", errors="ignore"), 1):
        if not l.strip(): continue
        try: d = json.loads(l)
        except Exception: bad.append((i, "非法JSON")); continue
        n += 1
        if d.get("prev") != prev: bad.append((i, "prev不对(断链)"))
        if d.get("h") != _line_hash(d.get("prev"), d.get("c")): bad.append((i, "hash不符(被改)"))
        prev = d.get("h")
    return (n, len(bad), bad[:3])

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: hashchain_log.py append|verify <文件> [内容]")
        sys.exit(1)
    act, path = sys.argv[1], sys.argv[2]
    if act == "append":
        c = sys.argv[3] if len(sys.argv) > 3 else ""
        r = append(path, c); print("✅ 追加 h=%s prev=%s" % (r["h"][:12], str(r["prev"])[:12]))
    else:
        n, badn, sample = verify(path)
        print("★ 校验 %s" % path)
        print("  行数:%d 坏链:%d" % (n, badn))
        if badn: print("  🔴 被篡改/断链:", sample)
        else: print("  ✅ 完整·无篡改")
