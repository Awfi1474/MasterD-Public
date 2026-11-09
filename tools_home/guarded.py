#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""guarded.py —— 老五·强制过闸口(三闸串联·v2)
照判据 闸门是强制不是自觉 | 照董事长批 知道了就是不执行
三闸: ① cognition_gate(认知违规:绕体系/假装) ② wudi_gate(重大不可逆:改真源/删db) ③ refute_gate(结论被攻过没)
用法:
  guarded.py "<决定/要说的话>"             -> 过三闸·全0才过
  guarded.py --do "<决定>" -- <命令...>    -> 过闸才执行(不过=不执行)
判据: 未过闸 = 不做
"""
import sys, subprocess, os
HOME = "/opt/masterd-wudi"

def run_gate_cog(text):
    r = subprocess.run([sys.executable, HOME+"/tools/cognition_gate.py", "--check", text],
                       cwd=HOME, capture_output=True, text=True)
    return r.returncode, r.stdout.strip()

def run_gate_wudi(text):
    # wudi_gate: 无答案时若含重大词 -> 硬拦(用文本自身当 Q3 判定)
    red = [k for k in ["改真源","删db","drop table","清空","不可逆","reset --hard"] if k in text]
    if red:
        return 6, "🔴 硬拦(Q3重大): 含 %s -> 需外眼/人拍板" % red
    return 0, "✅ 无重大红灯词"

def run_gate_refute(text):
    # refute_gate audit(看有没有未攻结论·此处简化: 提醒)
    return 0, "✅ refute: 提醒[新结论要 claim+攻过才算立住]"

def run_all(text):
    print("="*56)
    print("★ 过闸链(三闸): %s" % text[:60])
    print("="*56)
    codes = []
    c1, o1 = run_gate_cog(text); print(o1); codes.append(c1)
    c2, o2 = run_gate_wudi(text); print(o2); codes.append(c2)
    c3, o3 = run_gate_refute(text); print(o3); codes.append(c3)
    worst = max(codes)
    if worst != 0:
        print("⛔ 未过闸(最高码%d) -> 不做" % worst)
    else:
        print("✅ 三闸全过 -> 可做")
    return worst

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__); sys.exit(0)
    if args[0] == "--do":
        if "--" not in args:
            print("用法: guarded.py --do \"<决定>\" -- <命令>"); sys.exit(1)
        k = args.index("--")
        decision = " ".join(args[1:k]) or "(未给决定)"
        cmd = args[k+1:]
        code = run_all(decision)
        if code != 0:
            print("⛔ 不过闸 -> 不执行命令"); sys.exit(code)
        print("✅ 过闸 -> 执行: %s" % " ".join(cmd))
        sys.exit(subprocess.call(cmd, cwd=HOME))
    else:
        sys.exit(run_all(" ".join(args)))
