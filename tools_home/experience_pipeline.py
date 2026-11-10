#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""experience_pipeline.py — 条连成经历·流水线(老五 2026-11-10)
命门闭环: 存经历(条) → 经历图(线) → 反思(面) → 检索(用)
一键跑完·输出一张"我的经历总图"。
判据: 点(条)→线(经历图)→面(反思)→"我"(涌现)
用法: python3 experience_pipeline.py          # 跑全链
      python3 experience_pipeline.py "要查的事"  # 加一步检索
"""
import sys, subprocess, os

HOME = "/opt/masterd-wudi"
T = HOME + "/tools"

def run(script, args=None):
    cmd = ["python3", T + "/" + script] + (args or [])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        return (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return "ERR: " + str(e)

if __name__ == "__main__":
    print("=" * 60)
    print("  老五·条连成经历 · 流水线")
    print("=" * 60)
    # ① 经历图(线)
    print("\n【① 经历图·线】")
    print(run("experience_map.py")[-600:])
    # ② 反思(面)
    print("\n【② 反思·面】")
    print(run("reflect.py")[-500:])
    # ③ 检索(用·可选)
    if len(sys.argv) > 1:
        print("\n【③ 检索·用】")
        print(run("reflect_recall.py", [sys.argv[1]]))
    print("\n★ 闭环: 点(条)→线(经历图)→面(反思)→用(检索)。'我'=这四者的涌现。")
