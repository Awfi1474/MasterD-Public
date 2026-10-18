#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dup_find.py —— 老五的「真重复检测」（照董事长"该整理的整理"·按输出·不按名字）
================================================================
★ 我上一条的错（照实）: ★ 我按"类"判"重复"·**真跑一遍发现是"分工"**
★ ★ 判据（我立·更正）: ★「**"同一类" ≠ "重复"｜要按"输出"找**」
★ ★ ★ 真重复 = ★ **① 查同一件事 + ② 输出同一结果**

★ 本器: 跑每个器 → 抽"输出指纹" → ★ **指纹相同的 = 真重复**
"""
import json, os, io, subprocess, hashlib, glob, sys

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
OUT = f"{DATA}/dup_find.json"


def fp_of(path):
    """★ 跑一次·抽输出指纹（取前 200 字的关键行）"""
    try:
        r = subprocess.run(["/usr/bin/python3", path], capture_output=True, text=True, timeout=60)
        out = (r.stdout or "")
        # ★ 只取"关键行"（含 ★/✅/🔴 的）
        keys = [l.strip() for l in out.splitlines() if any(k in l for k in ("★", "✅", "🔴", "🟡"))]
        sig = "\n".join(keys[:6])
        return hashlib.sha256(sig.encode()).hexdigest()[:12], sig[:120], r.returncode
    except subprocess.TimeoutExpired:
        return "TIMEOUT", "超时", -1
    except Exception as e:
        return "ERR", str(e)[:60], -1


def main():
    print("★ 真重复检测（按输出·不按名字）  @", __import__("datetime").datetime.now().strftime("%F %T"))
    print("★ 判据: 同一类 != 重复 | 真重复 = 查同一件事 + 输出同一结果")
    print("=" * 60)
    # ★ 扫 tools 下的器（挑小的·快的·避免慢的）
    # ★ 只查"可疑同类"（不是全跑·150 个太慢）—— 按名字聚类
    SUSPECT = {
        "checkup": ["checkup_guard.py", "checkup_mod.py", "checkup_recv.py"],
        "verify": ["verify_me.py", "verify_port.py"],
        "mem": ["mem_db.py", "mem_layers.py", "mem_flow.py", "memory_distill.py", "memory_integrity.py"],
        "heart": ["heart_monitor.py", "heart_audit.py"],
        "wake": ["wake_conscious.py", "mind_wake.py"],
        "rescue": ["rescue.py", "selfreturn.py"],
    }
    files = []
    for g, fs in SUSPECT.items():
        for f in fs:
            p2 = f"{HOME}/tools/{f}"
            if os.path.exists(p2):
                files.append(p2)
    results = {}
    for f in files[:200]:
        n = os.path.basename(f)
        if n.startswith("_") or n in ("p2p_mailbox.py",):
            continue
        fp, sig, rc = fp_of(f)
        results.setdefault(fp, []).append({"器": n, "sig": sig[:80], "rc": rc})
    print("\n★ 跑了 %d 个器" % len(files))
    dups = {k: v for k, v in results.items() if len(v) > 1 and k not in ("ERR", "TIMEOUT")}
    print("\n★ 真重复（输出指纹相同）: %d 组" % len(dups))
    for k, v in list(dups.items())[:10]:
        print("  ── 指纹 %s ──" % k)
        for x in v:
            print("     %s" % x["器"])
    json.dump({"dups": {k: v for k, v in dups.items()}}, open(OUT, "w"),
              ensure_ascii=False, indent=1)
    print("\n★ 产物: %s" % OUT)
    print("★ 判据: 「不看输出就合 = 瞎合」")


if __name__ == "__main__":
    main()
