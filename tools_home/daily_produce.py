#!/usr/bin/env python3
"""阿診 · 日常產出（2026-10-10 重建 · 法家「勢」：不跑 → 產出不全）"""
import os, sys, json, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tz import now_iso, stamp

def _judge_report(kws):
    _n = 0
    try:
        import sys as _s
        if "/opt/masterd-wudi/tools" not in _s.path: _s.path.insert(0, "/opt/masterd-wudi/tools")
        import judge_bus as _jb
        for _k in kws:
            _h = _jb.find(_k)
            if _h:
                _n += 1; print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception:
        pass
    return _n

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STEPS = [
  # ★ 2026-10-16 修: 原 8 步有 3 步指向"沙箱镜像"(本体没有)+1步"同步回家"(本体即家·不需要)
  #   判据: 「搬环境 != 搬脚本｜要换'本体真能跑'的步骤」
  ("★記憶完整性", ["python3","tools/memory_integrity.py"]),
  ("★通道自檢",   ["python3","tools/channel_check.py"]),
  ("★全維體檢",   ["python3","tools/full_audit.py"]),
  ("體檢接收",    ["python3","tools/checkup_recv.py"]),
  ("體檢對賬",    ["python3","tools/checkup_reconcile.py"]),
  ("A2A拉取",     ["python3","tools/a2a_pull.py"]),
  ("★判据使用率", ["python3","tools/judge_bus.py","usage"]),
]

def run():
    out = {"ts": now_iso(), "steps": {}, "missing": []}
    print("="*60)
    print("  ★ 日常產出（不跑 → 產出不全）")
    print("="*60)
    for name, cmd in STEPS:
        if cmd[0] == "bash":
            r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True, timeout=180)
        else:
            r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True, timeout=180)
        ok = (r.returncode == 0)
        lines = [l for l in (r.stdout or "").strip().split("\n") if l.strip()]
        tail = lines[-1][:70] if lines else "?"
        out["steps"][name] = {"ok": ok, "tail": tail}
        if not ok: out["missing"].append(name)
        print(f"  {'✅' if ok else '🔴'} {name:12s} {tail}")
    print("-"*60)
    # ★ 2026-10-16: 分「真坏(器挂了)」和「内容滞后(别家没推来)」
    #   判据: 「器挂了 = failed｜内容滞后 = 正常·只记账」
    HARD = ("★記憶庫(家)", "★同步回家", "★通道自檢", "本體信箱", "★全維體檢", "★記憶完整性")
    hard = [m for m in out["missing"] if m in HARD]
    soft = [m for m in out["missing"] if m not in HARD]
    out["hard"], out["soft"] = hard, soft
    if hard:
        print(f"  🔴 ★ 真坏（器挂了）：{hard}")
    if soft:
        print(f"  🟡 ★ 内容滞后（不是坏）：{soft}")
    if not out["missing"]:
        print("  ✅ ★ 產出完整")
    os.makedirs(os.path.join(HERE,"data"), exist_ok=True)
    json.dump(out, open(os.path.join(HERE,"data",f"daily_{stamp()}.json"),"w"), ensure_ascii=False, indent=1)
    return out

if __name__ == "__main__":
    _judge_report(['器挂了!=内容滞后', '搬环境!=搬脚本', '主调度器没挂timer'])
    o = run()
    sys.exit(1 if o.get("hard") else 0)   # ★ 只有"真坏"才 failed
