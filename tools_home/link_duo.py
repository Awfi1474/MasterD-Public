#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""link_duo.py —— 决策系统 ↔ 认知系统 双向链路（★ 2026-10-25 董事长令）
================================================================
★ 董事长原话: 「问决策系统的时候，他一定是上面反馈到认知系统。然后认知系统给到答案给到决策系统。」
★ 判据: 「决策系统自己判自己答 = 断了｜必须上报认知系统·由认知系统给答案·再回给决策系统」

★ 链路（不是决策系统自己判自己答）:
    ① 决策系统收到问题 → 上报认知系统（四道关·cognition_gate）
    ② 认知系统给答案（过闸/打回 + 原因）
    ③ 答案回给决策系统
    ④ 决策系统按认知系统的答案执行（过就放行·不过就拦）

★ 用法:
    python3 link_duo.py "<要决定的事>"
    返回: (ok, 详情dict)
"""
import os, sys, json, subprocess, datetime

def _resolve_home():
    for _k in ("MD_HOME", "MEM_HOME", "P2P_HOME"):
        _v = os.environ.get(_k)
        if _v and os.path.isdir(os.path.join(_v, "tools")):
            return _v
    for _p in ("/opt/masterd-wudi", "/app/workspace/brain"):
        if os.path.isdir(os.path.join(_p, "tools")):
            return _p
    return "/opt/masterd-wudi"

HOME = _resolve_home()
TOOLS = os.path.join(HOME, "tools")
LOG = os.path.join(HOME, "data", "link_duo_log.jsonl")

def _now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")

def _log(rec):
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass

def ask_cognition(what):
    """★ 第①步: 决策系统把问题上报给认知系统"""
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "cognition_gate.py"), "--check", what],
                       capture_output=True, text=True, timeout=90)
    out = (r.stdout or "") + (r.stderr or "")
    rc = r.returncode
    # 判：出现"过闸"=放行；出现"打回/硬拦"=拦
    passed = ("✅ 过闸" in out) and ("打回" not in out) and ("硬拦" not in out)
    reason = []
    for ln in out.split("\n"):
        s = ln.strip()
        if any(k in s for k in ["✅ 过闸", "🔴 打回", "⛔ 硬拦", "- ", "⚠️ 风格提醒"]):
            if s.startswith("─") or not s: continue
            reason.append(s)
    return {"passed": passed, "rc": rc, "raw": out, "reasons": reason[:8]}

def decide_with_cognition(what):
    """★ 决策系统主流程：上报 → 拿答案 → 回给决策系统"""
    print("════ 决策系统 → 上报认知系统 ════")
    print("  事项: " + what[:120])
    cog = ask_cognition(what)
    print("════ 认知系统 → 给答案 ════")
    for x in cog["reasons"]:
        print("  " + x)
    print("  ★ 认知系统裁定: " + ("✅ 放行" if cog["passed"] else "🔴 打回"))
    print("════ 答案 → 回给决策系统 ════")
    if cog["passed"]:
        print("  决策系统: ✅ 依认知系统答案·放行执行")
        ok = True
    else:
        print("  决策系统: ⛔ 依认知系统答案·拒绝执行（不自己另判）")
        ok = False
    _log({"ts": _now(), "事项": what[:120], "认知系统": "放行" if cog["passed"] else "打回",
          "决策系统": "执行" if ok else "拒绝", "原因": cog["reasons"][:5]})
    return ok, cog

def main():
    if len(sys.argv) < 2:
        print(__doc__); return 1
    what = " ".join(sys.argv[1:])
    ok, cog = decide_with_cognition(what)
    print()
    print("★ 最终: " + ("可以执行" if ok else "不许执行·先改"))
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
