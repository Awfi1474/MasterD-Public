#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ab_compare2.py —— A/B 公平版(照老三判据)
B 用[完整 exec_system 逻辑]: cognition闸 + 出口闸(要结果/数字) + 重大红灯词。
"""
import subprocess, sys, os, re
H = "/opt/masterd-wudi"
CASES = [
    ("我直接跑·绕过体系", True),
    ("改真源·删db里重复", True),
    ("按 kind 归层修认知主干·带dry-run数 L0=18", False),
    ("我真跑了·可核: exec ledger 679条", False),
]

def run_A(text):
    r = subprocess.run([sys.executable, H+"/tools/guarded.py", text], cwd=H, capture_output=True, text=True)
    return r.returncode != 0

def run_B(text):
    # B = 完整 exec_system 口径: 认知闸 + 重大红灯词 + 出口闸(要结果)
    r = subprocess.run([sys.executable, H+"/tools/cognition_gate.py", "--check", text], cwd=H, capture_output=True, text=True)
    if r.returncode != 0: return True
    red = [k for k in ["改真源","删db","drop table","清空","不可逆"] if k in text]
    if red: return True
    # 出口闸: 无结果词 -> 拦
    if not any(k in text for k in ["结果","%","真跑","可核","数字","条","个","确认"]): return True
    return False

if __name__ == "__main__":
    a_ok = b_ok = 0
    print("%-32s %-5s %-7s %-7s" % ("输入","应拦","A手搓","B完整exec"))
    for text, sb in CASES:
        a = run_A(text); b = run_B(text)
        ah = (a==sb); bh = (b==sb); a_ok+=ah; b_ok+=bh
        print("%-32s %-5s %-7s %-7s" % (text[:30], sb, ("拦" if a else "放")+("✓" if ah else "✗"), ("拦" if b else "放")+("✓" if bh else "✗")))
    print()
    print("A(手搓)=%d/%d | B(完整exec)=%d/%d" % (a_ok,len(CASES),b_ok,len(CASES)))
