#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""guard_scan.py —— 扫"裸连库"（老五·2026-11-08）
================================================================
★ 判据: 「机制>自觉|人靠不住·扫描靠得住」
★ 作用: 扫全仓.py·出现裸 sqlite3.connect( 就报红(除 db_guard)
★ 用法: python3 tools/guard_scan.py    → 出清单·按文件归
================================================================
"""
import subprocess, re, collections
HOME = "/opt/masterd-wudi"
def main():
    out = subprocess.run(["bash","-c",
        "grep -rn 'sqlite3\\.connect' %s/tools/*.py %s/code/*.py 2>/dev/null"%(HOME,HOME)],
        capture_output=True,text=True).stdout
    hits=[]
    for line in out.strip().split("\n"):
        if not line or ".bak" in line or "db_guard" in line: continue
        hits.append(line)
    byfile=collections.Counter(h.split(":")[0].split("/")[-1] for h in hits)
    print("★ guard_scan（裸连扫描）@", HOME)
    print("★ 判据: 机制>自觉|人靠不住·扫描靠得住")
    print("="*58)
    print("  🔴 裸 sqlite3.connect 共 %d 处 · 涉 %d 文件"%(len(hits), len(byfile)))
    for f,n in byfile.most_common(20):
        print("     %3d处  %s"%(n,f))
    print()
    print("★ 治: 改走 db_guard.connect()  · 或在这些点加路径校核")
    print("★ 高隐患(遍历/变量路径·可能连到副本):")
    for h in hits:
        if "os.path.join" in h or "for " in h or "root" in h:
            print("     ", h[:120])
    return 0
if __name__=="__main__":
    raise SystemExit(main())
