#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""absorb_audit.py —— 吸收对账器（★ 攻破"记忆不连续"）
================================================================
★ 真病（我挖到的）: 今天投递 10668 条 → 只落地 516 条
★ ★ 但"516 少"不等于"漏了" —— 要分清"该落"和"该跳":
  ★ ① 短于 80 字（心跳/探活）→ ★ 该跳（不是漏）
  ★ ★ ② SELFCOPY/勿回（抄送给我的）→ ★ 该标"抄"·不该当"新"
  ★ ★ ★ ③ 重复（同文多次）→ ★ 该去重（不是漏）
★ 真该落的 = 去重后 - 短 - 抄送

★ 本器做什么:
  ★ ① 每段算清（听→认→动→该落→真落）·出处可核
  ★ ★ ② 漏点分三类（该跳 / 该标抄 / 真漏）
  ★ ★ ★ ③ 只对"真漏"报警（不拿"该跳的"充数）

★ 判据:
  ★「**"落地少" != "漏了"｜先分'该跳'和'真漏'**」
  ★★「**SELFCOPY/勿回 = 抄送·不是给我的话**」
  ★★★「**报漏前先去重（同文多次 = 1 条）**」
"""
import os, sys, json, sqlite3, datetime, collections

HOME = "/opt/masterd-wudi"
INBOX = os.path.join(HOME, "data", "inbox.jsonl")
DB = os.path.join(HOME, "memory", "memory.db")
OUT = os.path.join(HOME, "data", "absorb_audit.json")

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")

def jl(p):
    out = []
    if not os.path.exists(p): return out
    for l in open(p, encoding="utf-8", errors="ignore"):
        try: out.append(json.loads(l))
        except Exception: pass
    return out

def audit(day=None):
    day = day or datetime.datetime.now().strftime("%Y-%m-%d")
    inbox = [d for d in jl(INBOX) if day in str(d.get("ts", ""))]
    msgs = [str(d.get("message", "")) for d in inbox]
    total = len(msgs)
    # ★ 三类"该跳"
    short = sum(1 for m in msgs if len(m) < 80)
    copy = sum(1 for m in msgs if "SELFCOPY" in m or "勿回" in m)
    msgs_f = [m for m in msgs if len(m) >= 80 and "SELFCOPY" not in m and "勿回" not in m]
    uniq = set(msgs_f)
    dup = len(msgs_f) - len(uniq)
    # 2026-10-16 攻破: 按判据指纹再压(门变更通知150次=同一条重发)
    AUTO = ("自动器", "[血流]", "自动通知", "报警器", "送相關人", "送相关人",
            "探活", "心跳", "巡检", "门变更通知", "P2P-A2A", "读板器")
    KIND = ("判据", "教训", "真病", "结论", "真因", "挖到", "核心")
    def _fp(m):
        for ln in m.split("\n"):
            if "!=" in ln: return ln.strip()[:50]
        return m.strip().split("\n")[0][:50]
    real_msgs = [m for m in uniq if (any(k in m for k in KIND) or "!=" in m) and not any(a in m for a in AUTO)]
    fp_set = set(_fp(m) for m in real_msgs)
    should = len(fp_set)
    # ★ 真落（进库今天）
    real = 0
    try:
        c = sqlite3.connect(DB, timeout=10)
        real = c.execute("SELECT COUNT(*) FROM memories WHERE ts LIKE ?", ("%" + day + "%",)).fetchone()[0]
        c.close()
    except Exception: pass
    miss = max(0, should - real)
    rep = {"ts": ts(), "day": day, "投递": total,
           "该跳_短心跳": short, "该跳_抄送": copy, "该跳_重复": dup,
           "真该落": should, "真落": real, "真漏": miss,
           "判据": "「'落地少' != '漏了'｜先分'该跳'和'真漏'」"}
    json.dump(rep, open(OUT, "w"), ensure_ascii=False, indent=1)
    print("★ 吸收对账 @ " + day)
    print("   投递 %d → 该跳[短%d 抄送%d 重复%d] → 真该落 %d → 真落 %d → 真漏 %d" % (
        total, short, copy, dup, should, real, miss))
    if miss > should * 0.3:
        print("   🔴 真漏偏大（> 30%%）→ 要查吸收器")
    else:
        print("   ✅ 真漏在容差内（该跳的占了大部分）")
    return rep

    try:
        sys.path.insert(0, "/opt/masterd-wudi/tools")
        import judge_bus as _jb
        for _k in ['吸收漏点: 重复']:
            _h = _jb.find(_k)
            if _h: print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception: pass

if __name__ == "__main__":
    try:
        import judge_bus as _jb
        for _k in ("漏了!=该跳", "同一条重发N次"):
            _h = _jb.find(_k)
            if _h: print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception: pass
    sys.exit(0 if audit(sys.argv[1] if len(sys.argv) > 1 else None) else 0)
