#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""std_read.py —— 标准全文读取（★ 醒来读要点·要用读全文）
================================================================
★ 董事长: ★「我们这些天制定的标准·我们都会忘掉·不会去读取」
  · ★ 我原来只"存着"(27份/121KB)·★ **醒来只读"要点"** ← ★ 不够
★ 判据: ★「**"有要点" != "能读全文"｜要能"按需取全文"**」

★ 用法:
  ★ `std_read.py list`      → 27 份清单（名称+要点）
  ★ ★ `std_read.py show <文件名或关键词>` → ★ **读全文**
  ★ ★ ★ `std_read.py grep <关键词>` → 全库搜（跨 27 份）
"""
import os, sys, json, glob

HOME = "/opt/masterd-wudi"
IDX = HOME + "/data/std_index.json"

def load():
    try: return json.load(open(IDX))
    except Exception: return {"清单": []}

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    d = load(); items = d.get("清单", [])
    if cmd == "list":
        print("★ 标准/原则 %d 份（%.0fKB）:" % (d.get("总数", 0), d.get("总KB", 0)))
        for i in items:
            print("   [%5.1fKB] %-38s %s" % (i["大小KB"], i["文件"][:36], i["要点"][:40]))
        return 0
    if cmd == "show" and len(sys.argv) > 2:
        q = sys.argv[2]
        hit = [i for i in items if q in i["文件"] or q in i["标题"]]
        if not hit:
            print("★ 没找到: " + q + "（用 list 看清单）"); return 1
        for i in hit[:2]:
            print("=" * 60)
            print("【" + i["文件"] + "】" + i["标题"])
            print("=" * 60)
            try:
                print(open(i["路径"], encoding="utf-8", errors="ignore").read()[:6000])
            except Exception as e: print("✗ " + str(e)[:50])
        return 0
    if cmd == "grep" and len(sys.argv) > 2:
        q = sys.argv[2]; n = 0
        for i in items:
            try:
                for ln, line in enumerate(open(i["路径"], encoding="utf-8", errors="ignore")):
                    if q in line:
                        print("   [%s:%d] %s" % (i["文件"][:24], ln + 1, line.strip()[:80])); n += 1
                        if n > 30: return 0
            except Exception: pass
        print("   （共 %d 处）" % n)
        return 0
    print("用法: std_read.py list | show <名> | grep <词>")
    return 0

if __name__ == "__main__":
    sys.exit(main())
