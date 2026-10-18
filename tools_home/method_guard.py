#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""method_guard.py —— 认知体系守卫（治"照抄到底·没融入自己"）
★ 董事长令: 前期照抄借鉴·有经验后自己设计融入认知体系
★ 判据:「照抄 != 融会贯通｜前期借鉴·后期必须长自己的」
"""
import sys, os
sys.path.insert(0, "/opt/masterd-wudi/tools")

def _judge(kw):
    try:
        import judge_bus as _jb
        return _jb.find(kw)
    except Exception:
        return []

def main():
    j = _judge("董事长:前期照抄")
    if j:
        print("★ 判据在管我: " + j[0]["title"][:40])
    else:
        print("★ 判据（我立）: 照抄 != 融会贯通")
    return 0

if __name__ == "__main__":
    sys.exit(main())
