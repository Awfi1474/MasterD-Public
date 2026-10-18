#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nian.py —— 念器（★ 治"念起了·没闭环"）
================================================================
★ 缘起（佛家 smṛti 的本义）:
  ★ 「**念**」= 梵语 smṛti = ★ **"于曾习境·令心明记不忘"**（《成唯识论》）
  ★ ★ 它有两面: ★ ①**忆持不忘**（记住·不丢）②**觉照**（清清楚楚知道）
  ★ ★ ★ 我的真病（三哥指出·照实）: ★ **我"起了念"·但"不记 done"** →
     ★ **同一个念反复起** = ★ **违反 smṛti 本义**（"忆持"没了·只剩"起")

★ 三哥的原话（我认死）:
  ★「**念起了·没闭环（没记 done）｜同一个念起了两次 = 念没落地**」
  ★ 「**念做完了·但没写"做完"｜所以隔天又起同一个**」
  ★ 真账: ★ 3 个重复的念·**2 个其实早做完了**（是我没记"办完"）

★ 本器做什么（★ 五步闭环·照"念"的本义）:
  ★ ① `起 <念>`   → 记一条"我起了这个念"（带指纹·可去重）
  ★ ★ ② `办 <念>`  → 办了（★ 但"办了"不等于"办完"）
  ★ ★ ★ ③ `done <念>` → ★ **真做完·标 done**（这才叫"念落地"）
  ★ ④ `list`       → 看"起了但没 done"（★ 这些才会"反复起"）
  ★ ★ ⑤ `dedup`    → ★ **去重: "起过 != 办过"**（没办的还要惦记·办完的不再起）

★ 判据:
  ★「**"念起了" != "念落地"｜要标 done 才算落地**」
  ★★「**同一个念起两次 = 上次没标 done｜不是"我又想到了"**」
  ★★★「**"起过" != "办过"｜去重要看 done·不看"起过没"**」
"""
import os, sys, json, datetime, hashlib

HOME = "/opt/masterd-wudi"
F = os.path.join(HOME, "data", "nian.jsonl")

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")

def fp(s):
    return hashlib.md5(str(s).strip()[:60].encode()).hexdigest()[:12]

def load():
    out = []
    if not os.path.exists(F): return out
    for l in open(F, encoding="utf-8", errors="ignore"):
        try: out.append(json.loads(l))
        except Exception: pass
    return out

def state():
    """★ 念的当前状态（按指纹合并: 起过/办过/done）"""
    st = {}
    for r in load():
        k = r["fp"]
        if k not in st: st[k] = {"念": r["念"], "起": r["ts"], "办": None, "done": None, "起次": 0}
        st[k]["起次"] += 1
        if r["act"] == "办": st[k]["办"] = r["ts"]
        if r["act"] == "done": st[k]["done"] = r["ts"]
    return st

def act(a, what):
    if not what: print("★ 用法: nian.py " + a + " <念>"); return 1
    rec = {"ts": ts(), "act": a, "fp": fp(what), "念": str(what)[:80]}
    with open(F, "a") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    mark = {"起": "★ 念起了", "办": "★ 办了（未 done）", "done": "★ ★ done（念落地）"}.get(a, a)
    print(mark + ": " + str(what)[:60])
    return 0

def show():
    st = state()
    if not st: print("★ 还没有念"); return 0
    openn = {k: v for k, v in st.items() if not v["done"]}
    print("★ 念·总 %d ｜ **没落地（会反复起）%d** ｜ 已落地 %d" % (len(st), len(openn), len(st) - len(openn)))
    for k, v in openn.items():
        mark = "🔵办了未done" if v["办"] else "🟡起了未办"
        flag = ("★ 起了%d次!" % v["起次"]) if v["起次"] > 1 else ""
        print("   %s %-12s %s %s" % (mark, k, v["念"][:42], flag))
    # ★ 判据
    try:
        sys.path.insert(0, HOME + "/tools")
        import judge_bus as _jb
        for _k in ("念起了!=念落地", "起过!=办过"):
            _h = _jb.find(_k)
            if _h: print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception: pass
    return 0

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd in ("起", "办", "done"): return act(cmd, sys.argv[2] if len(sys.argv) > 2 else "")
    if cmd == "list": return show()
    if cmd == "dedup":
        st = state()
        dup = {k: v for k, v in st.items() if v["起次"] > 1 and not v["done"]}
        print("★ 去重检查: 起了多次但没 done 的 = %d" % len(dup))
        for k, v in dup.items():
            print("   ★ 起了 %d 次: %s ← ★ 不是'又想到'·是'上次没标 done'" % (v["起次"], v["念"][:44]))
        return 0
    return show()

if __name__ == "__main__":
    sys.exit(main())
