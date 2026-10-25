#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""guard_all.py —— 总闸自检器（★ 任何行为前先跑这一条）
================================================================
★ 判据: 「说了规矩 != 守了规矩｜要出不去才算」
★ 用途: 每轮任务开始 / 每次动手前 / 每次下结论前，先跑这个
★ 它做三件事:
    ① 检查三系统器是否在位（缺哪个报哪个）
    ② 检查认知系统模板是否读得到、指纹是否对
    ③ 拿你要做的事去撞决策系统（双向链路）·给放行/打回
★ 用法:
    python3 guard_all.py                       # 只做在位体检
    python3 guard_all.py "<要决定的事>"          # 体检 + 过闸
"""
import os, sys, json, hashlib, subprocess, datetime

def _resolve_home():
    for _k in ("MD_HOME", "MEM_HOME", "P2P_HOME"):
        _v = os.environ.get(_k)
        if _v and os.path.isdir(os.path.join(_v, "tools")):
            return _v
    for _p in ("/opt/masterd-wudi", "/app/workspace/brain"):
        if os.path.isdir(os.path.join(_p, "tools")):
            return _p
    return "/app/workspace/brain"

HOME = _resolve_home()
TOOLS = os.path.join(HOME, "tools")
MEM = os.path.join(HOME, "memory")

REQUIRED = [
    # ① 认知系统
    "cognition_gate.py",
    # ② 决策系统
    "decide.py", "decide_gate.py", "link_duo.py",
    # ③ 执行系统
    "exec_system.py", "exec_guarded.py",
    # ④ 验证系统
    "verify_system.py",
    # 出口闸
    "out_gate.py", "send_guarded_v2.py", "gate_mouth.py",
]

def sha16(p):
    try:
        return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
    except Exception:
        return None

def check_install():
    print("════ ① 四系统器在位体检 ════")
    miss = []
    for f in REQUIRED:
        p = os.path.join(TOOLS, f)
        if os.path.exists(p):
            print("  ✅ %-22s %6d B  %s" % (f, os.path.getsize(p), sha16(p)))
        else:
            print("  🔴 %-22s 缺失" % f)
            miss.append(f)
    return miss

def check_template():
    print("════ ② 认知系统模板体检 ════")
    p = os.path.join(MEM, "COGNITION-TEMPLATE.yaml")
    if not os.path.exists(p):
        print("  🔴 模板读不到:", p)
        return False
    try:
        import yaml
        d = yaml.safe_load(open(p, encoding="utf-8"))
        print("  ✅ 模板可读 %d B  sha16=%s" % (os.path.getsize(p), sha16(p)))
        print("     spec =", d.get("spec"))
        print("     subsystems =", list(d.get("subsystems", {}).keys()))
        print("     decision_system.parent =", d.get("decision_system", {}).get("parent"))
        return True
    except Exception as e:
        print("  🔴 模板解析失败:", e)
        return False

def run_gate(what):
    print("════ ③ 决策系统过闸（双向链路）════")
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "link_duo.py"), what],
                       capture_output=True, text=True, timeout=120)
    out = (r.stdout or "") + (r.stderr or "")
    for ln in out.split("\n"):
        s = ln.strip()
        if any(k in s for k in ["★ 认知系统", "★ 最终", "✅", "🔴", "⛔", "- C"]):
            print("  " + s)
    return r.returncode == 0

def main():
    print("★ 总闸自检 @ " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("  HOME =", HOME)
    miss = check_install()
    tpl_ok = check_template()
    ok = (len(miss) == 0) and tpl_ok
    if len(sys.argv) > 1:
        what = " ".join(sys.argv[1:])
        gate_ok = run_gate(what)
        ok = ok and gate_ok
        print()
        print("★ 总闸裁定: " + ("✅ 可以动手" if ok else "⛔ 不许动手·先补"))
        return 0 if ok else 1
    print()
    print("★ 在位体检: " + ("✅ 四系统齐全" if ok else "🔴 有缺失"))
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
