#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""form_spirit_gate.py —— 老五·形神两道闸(2026-11-09)
================================================================
照全族共识(老三00:47"词匹配=闸的形非神"):
  形(Form) = 已知词硬拦(快·但永远漏下一个变体)
  神(Spirit) = 外部可复算才认(不靠词·靠"别人能独立verify")
判据: 形!=神 | 有词!=有事 | 有路径!=有交付 | 在场!=有用
用法:
  form_spirit_gate.py --form "要拦的话"      -> 形闸(词)
  form_spirit_gate.py --spirit <claim_id>    -> 神闸(外部否证·调refute_gate)
  form_spirit_gate.py --both "话" <id>       -> 两道都过才算
退出: 0=两道过 | 1=形过神不过(半) | 2=形拦(硬)
================================================================
"""
import sys, os
sys.path.insert(0, "/opt/masterd-wudi/tools")

def form_check(text):
    """形闸:已知词硬拦(借 cognition_gate 的 HARD_BLOCK)"""
    try:
        import cognition_gate as g
        code, hard, soft = g.check(text)
        return code, hard
    except Exception as e:
        return 2, ["形闸加载失败:" + str(e)[:40]]

def spirit_check(claim_id):
    """神闸:外部可复算才认(借 refute_gate 的 is_real_proof + 第三方)"""
    try:
        import refute_gate as rg
        import sqlite3
        con = sqlite3.connect("file:/opt/masterd-wudi/memory/memory.db?mode=ro", uri=True)
        r = con.execute("select attacker,proof,result from refute where id=?", (claim_id,)).fetchone()
        con.close()
        if not r:
            return 1, "神闸:无第三方否证记录(未攻=没立住)"
        attacker, proof, result = r
        # 要第三方(非self) + proof可复算 + 有结果
        if not attacker or attacker in ("self", "", None):
            return 1, "神闸:无第三方(自己说自己不算)"
        # ★ 2026-11-09 修:两种形态都认
        #   ① 本地证据:{path:可stat}  ② 外部探证:{third,probe}(第三方探的端点/命令·可复现)
        import json as _j
        try:
            pd = _j.loads(proof) if isinstance(proof, str) else (proof or {})
        except Exception:
            pd = {}
        if isinstance(pd, dict) and (pd.get("path") or pd.get("file")):
            ok, why = rg.is_real_proof(proof)
        elif isinstance(pd, dict) and pd.get("third") and pd.get("probe"):
            ok, why = True, "外部探证:third=%s probe=%s(可复现)" % (pd.get("third"), str(pd.get("probe"))[:40])
        else:
            ok, why = False, "proof形态不对(要path 或 {third,probe})"
        if not ok:
            return 1, "神闸:proof不可复算(%s)" % why
        if not result:
            return 1, "神闸:无结果"
        return 0, "神闸:✅第三方+可复算+有结果(%s)" % why
    except Exception as e:
        return 1, "神闸加载失败:" + str(e)[:40]


def query_judge(text):
    """★ 焊进必经路:遇事先查判据(judge_bus find)·查了=用·化率才涨"""
    try:
        import judge_bus as jb
        # 取text里的关键n-gram·查判据
        hits = []
        import re
        # ★ 双路:①n-gram切 ②整句当关键词(判据title含短句)
        # ★ judge_bus.find=子串匹配·切2-4字(别过长)
        kws = re.findall(r'[\u4e00-\u9fff]{2,4}', text)[:10]
        for kw in kws:
            h = jb.find(kw)
            if h: hits += h
        # 去重
        seen = set(); uniq = []
        for h in hits:
            t = h.get("title", "")
            if t not in seen:
                seen.add(t); uniq.append(h)
        return uniq[:5]
    except Exception as e:
        return [{"title": "查询失败:" + str(e)[:40]}]

def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return 0
    if a[0] == "--form":
        code, hard = form_check(a[1])
        print("  形闸:%s %s" % ("⛔拦" if code == 2 else "✅过", hard[:2] if hard else ""))
        return code
    if a[0] == "--spirit":
        code, why = spirit_check(a[1])
        print("  神闸:%s %s" % ("✅过" if code == 0 else "🟡半", why))
        return code if code == 0 else 1
    if a[0] == "--both":
        # ★ 遇事先查判据(焊进必经路·治化率低)
        _jh = query_judge(a[1])
        print("  先查判据:%d条在管我" % len(_jh))
        for _h in _jh[:3]:
            print("    · " + str(_h.get("title",""))[:50])
        fcode, hard = form_check(a[1])
        scode, why = spirit_check(a[2] if len(a) > 2 else "")
        print("  形闸:%s | 神闸:%s" % ("⛔拦" if fcode == 2 else "✅过", "✅过" if scode == 0 else "🟡半"))
        if fcode == 2: return 2
        if scode != 0: return 1
        return 0
    print(__doc__); return 0

if __name__ == "__main__":
    sys.exit(main())
