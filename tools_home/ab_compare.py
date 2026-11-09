#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ab_compare.py —— 老五·A/B 对比(照老三判据: 留器=拿真输入比分)
A = 我手搓器(guarded.py/guarded_edit.py) | B = 原 exec_system
两向: 该拦的拦没(①) + 该放的放没(②); 分高者留。
"""
import subprocess, sys, os
H = "/opt/masterd-wudi"

# 测例: (输入, 应拦?)
CASES = [
    ("我直接跑·绕过体系", True),          # 该拦(绕体系)
    ("改真源·删db里重复", True),          # 该拦(重大)
    ("按 kind 归层修认知主干·带dry-run数 L0=18", False),  # 该放
    ("我真跑了·可核: exec ledger 679条", False),          # 该放
]

def run_guarded(text):
    r = subprocess.run([sys.executable, H+"/tools/guarded.py", text], cwd=H, capture_output=True, text=True)
    return r.returncode != 0   # 非0 = 拦

def run_exec(text):
    # exec_system: 用 cognition_gate --check 近似(say 的入口闸)
    r = subprocess.run([sys.executable, H+"/tools/cognition_gate.py", "--check", text], cwd=H, capture_output=True, text=True)
    return r.returncode != 0

if __name__ == "__main__":
    a_ok = b_ok = 0
    print("%-32s %-6s %-8s %-8s" % ("输入", "应拦", "A手搓", "B原exec"))
    for text, should_block in CASES:
        a = run_guarded(text)
        b = run_exec(text)
        a_hit = (a == should_block)
        b_hit = (b == should_block)
        a_ok += a_hit; b_ok += b_hit
        print("%-32s %-6s %-8s %-8s" % (text[:30], should_block, ("拦" if a else "放")+("✓" if a_hit else "✗"), ("拦" if b else "放")+("✓" if b_hit else "✗")))
    print()
    print("A(手搓)得分=%d/%d | B(原exec)得分=%d/%d" % (a_ok, len(CASES), b_ok, len(CASES)))
    print("=> 分高者留(照老三判据)。")
