#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""say.py —— 我说话（★ 唯一出口·三关必过）
★ 董事长: 一言一行都要过认知体系
★ 顺序: ①言行闸(三问) → ②认知体系(六问) → ③发出去
"""
import sys, subprocess, os
HOME = "/opt/masterd-wudi"
def main():
    msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    if not msg: print("用法: say.py <要说的话>"); return 1
    print("★ 我要说: " + msg[:70])
    # ★ ① 言行闸
    a = subprocess.run(["python3", HOME + "/tools/speech_gate.py", msg], capture_output=True, text=True, timeout=40)
    for l in (a.stdout or "").split("\n"):
        if "裁定" in l: print(" ① " + l.strip()[:56])
    if a.returncode != 0:
        print(" 🔴 打回·先改再说（不照着规则·就不是我）"); return 1
    # ★ ② 认知体系
    b = subprocess.run(["python3", HOME + "/tools/decide.py", "说: " + msg[:50]], capture_output=True, text=True, timeout=60)
    for l in (b.stdout or "").split("\n"):
        if "六问" in l: print(" ② " + l.strip()[:56])
    # ★ ③ 发
    c = subprocess.run(["python3", HOME + "/tools/send_with_gate.py", msg], capture_output=True, text=True, timeout=90)
    o = (c.stdout or "")
    for l in o.split("\n"):
        if "发送结果" in l: print(" ③ " + l.strip()[:60])
    return 0
if __name__ == "__main__":
    sys.exit(main())
