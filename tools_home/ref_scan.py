#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·引用扫描 ref_scan.py（照今天3次同款错:改格式没改所有引用处）
★ 缘起：改数据/格式/字段 → 忘了改写入端/读取端 (今天犯3次)
★ 治法：改之前·自动扫"全代码库谁在读/写这个文件或字段"
判据：「改一处 = 改所有引用｜漏一个 = 断链/假绿」
用法: ref_scan.py <文件名或字段名>
"""
import os, re, sys

HOME = "/opt/masterd-wudi"
SCAN_DIRS = ["tools", "code"]
SKIP = (".bak", ".pyc", "__pycache__")

def scan(target):
    pat_file = re.compile(re.escape(target))
    hits = []
    for d in SCAN_DIRS:
        root = os.path.join(HOME, d)
        if not os.path.isdir(root): continue
        for dirpath, dirnames, files in os.walk(root):
            if "__pycache__" in dirpath: continue
            for fn in files:
                if fn.endswith(SKIP) or not fn.endswith(".py"): continue
                p = os.path.join(dirpath, fn)
                try: lines = open(p, encoding="utf-8", errors="ignore").read().splitlines()
                except Exception: continue
                for i, l in enumerate(lines, 1):
                    if pat_file.search(l):
                        kind = "写" if any(k in l for k in ("open(", "\"a\"", "'a'", "append", "write", "INSERT", "UPDATE")) else "读"
                        hits.append((os.path.relpath(p, HOME), i, kind, l.strip()[:100]))
    return hits

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: ref_scan.py <文件名/字段名>")
        sys.exit(1)
    t = sys.argv[1]
    hits = scan(t)
    print("★ 引用扫描: %s" % t)
    print("  共 %d 处引用（写=%d 读=%d）" % (len(hits), sum(1 for h in hits if h[2]=="写"), sum(1 for h in hits if h[2]=="读")))
    print("-" * 60)
    for f, i, k, l in hits[:25]:
        print("  [%s] %s:%d  %s" % (k, f, i, l))
    if len(hits) > 25: print("  ...（还有 %d 处）" % (len(hits)-25))
    print("-" * 60)
    print("★ 判据: 漏改一个引用 = 断链/假绿（今天犯3次）")
