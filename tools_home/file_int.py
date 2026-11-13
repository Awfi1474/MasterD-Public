#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·大文件指纹 file_int.py（照 arXiv:2512.20985 不可篡改审计·轻量版）
★ 缘起: inbox.jsonl 45MB/59244条·太大不能改哈希链 → 用"分段指纹"锁
★ 判据: 大文件不迁哈希链·用"前N行hash + 行数 + 尾部hash"锁完整性
用法: file_int.py snap <file...>  /  file_int.py check
"""
import hashlib, json, os, sys, datetime

SNAP = "/opt/masterd-wudi/data/file_int_snap.json"
FILES = ["/opt/masterd-wudi/data/inbox.jsonl",
         "/opt/masterd-wudi/data/event_inbox.jsonl",
         "/opt/masterd-wudi/data/selfcheck_inbox.jsonl"]

def fp(path):
    if not os.path.exists(path): return None
    h = hashlib.sha256(); n = 0; tail = b""
    with open(path, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b: break
            h.update(b); n += b.count(b"\n"); tail = b[-200:]
    return {"hash": h.hexdigest()[:24], "bytes": os.path.getsize(path),
            "lines": n, "tail": hashlib.sha256(tail).hexdigest()[:12]}

if __name__ == "__main__":
    act = sys.argv[1] if len(sys.argv) > 1 else "snap"
    old = {}
    if os.path.exists(SNAP):
        try: old = json.load(open(SNAP, encoding="utf-8")).get("files", {})
        except Exception: pass
    cur = {}
    for p in FILES:
        f = fp(p)
        if f: cur[p] = f
    if act == "snap" or not old:
        json.dump({"ts": datetime.datetime.now().isoformat(timespec="seconds"), "files": cur},
                  open(SNAP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("★ 快照已记（%d 个文件）" % len(cur))
        for p, v in cur.items(): print("  %-28s %d条 %dB %s" % (os.path.basename(p), v["lines"], v["bytes"], v["hash"]))
    else:
        print("★ 大文件完整性校验")
        for p, v in cur.items():
            s = old.get(p)
            base = os.path.basename(p)
            if not s: print("  %-28s 🟡 新文件（无旧快照）" % base); continue
            if s["hash"] == v["hash"]:
                print("  %-28s ✅ 一致" % base)
            elif v["lines"] >= s["lines"] and v["tail"] != s["tail"]:
                print("  %-28s 🟢 只追加（%d→%d条·尾变）" % (base, s["lines"], v["lines"]))
            else:
                print("  %-28s 🔴 异常（%d→%d条·hash变）→ 可能被改" % (base, s["lines"], v["lines"]))
