#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hua.py —— 化（★ 照三哥的提炼三层: 记(Case) → 提(Strategy) → 化(Skill)）
================================================================
★ 三哥的提炼三层（我认死）:
  ★ ① **记 Case** = 发生过什么事（有账）
  ★ ★ ② **提 Strategy** = 从这件事提出"以后怎么办"（判据/做法）
  ★ ★ ★ ③ **化 Skill** = ★ **化到"不用想·手就会"**（下一次直接做对）
★ 三哥最硬的尺: ★「**"写了判据" != "提炼了"｜提炼了 = 下一轮不再犯**」
  ★★ 更狠: ★「**"提炼了没有" = "下次遇到同类·还用不用'想'"**」

★ 我的缺（照实）: ★ **我有 Case（case 138 条）+ Strategy（判据 55 条）·★ 但没有"化"**
  · ★ 结果: ★ **下次遇到同类·我还要"想一遍"** ← ★ 这就是"没化"

★ 本器做什么:
  ★ ① `audit` → 量"化率"（Case→Strategy→Skill 三层各多少·多少真化了）
  ★ ★ ② `skill <判据>` → ★ **把一条 Strategy 标成 Skill**（★ 附"验证过几次"）
  ★ ★ ★ ③ `list` → 看"化了的（Skill）"和"没化的（Strategy）"
"""
import os, sys, json, sqlite3, datetime

def _db_connect(DB):
    _err = "none"
    for _d in ["file:" + DB + "?mode=ro", "file:" + DB + "?immutable=1", DB]:
        try:
            return sqlite3.connect(_d, uri=_d.startswith("file:"), timeout=10)
        except Exception as _e:
            _err = str(_e)
    raise RuntimeError("db open failed: " + _err)



HOME = "/opt/masterd-wudi"
DB = HOME + "/memory/memory.db"
SKILL = HOME + "/data/skills.json"

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")

def q(sql, a=()):
    try:
        c = _db_connect(DB)
        r = list(c.execute(sql, a)); c.close(); return r
    except Exception as _e: print("WARN db-read-fail:", _e); return []

def load_skills():
    try: return json.load(open(SKILL))
    except Exception: return {"skills": []}

def audit():
    n_case = q("SELECT COUNT(*) FROM memories WHERE kind='case'")[0][0]
    n_strat = q("SELECT COUNT(*) FROM memories WHERE kind='判据'")[0][0]
    sk = load_skills()["skills"]
    n_skill = len(sk)
    print("★ 化·审计 @ " + ts())
    print("  ★ ① Case（记·发生过什么）:    **%d 条**" % n_case)
    print("  ★ ★ ② Strategy（提·以后怎么办）: **%d 条**" % n_strat)
    print("  ★ ★ ★ ③ Skill（化·手就会）:    **%d 条**" % n_skill)
    if n_strat:
        print("  ★ 化率: **%.0f%%**（%d/%d Strategy 化成 Skill）" % (n_skill * 100.0 / n_strat, n_skill, n_strat))
    print()
    print("  ★ 判据: 「写了判据 != 提炼了｜提炼了 = 下一轮不再犯」")
    print("  ★ ★ ：提炼了没有 = 下次遇到同类·还用不用想")
    for s in sk[-5:]:
        print("   ✅ 已化: " + s["skill"][:50] + "（验证 %d 次）" % s.get("verified", 0))

def skill(what):
    d = load_skills()
    if not what: print("★ 用法: hua.py skill <判据>"); return 1
    # ★ 找对应的 Strategy
    hit = q("SELECT title FROM memories WHERE kind='判据' AND title LIKE ?", ("%" + what + "%",))
    title = str(hit[0][0]) if hit else what
    if any(s["skill"] == title for s in d["skills"]):
        print("★ 已经化过了: " + title); return 0
    d["skills"].append({"skill": title, "ts": ts(), "verified": 1, "src": "manual"})
    json.dump(d, open(SKILL, "w"), ensure_ascii=False, indent=1)
    print("★ 化了一条: " + title[:60])
    print("  ★ 但: 标了 Skill != 真化｜要下次不用想·直接做对才算")
    return 0

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "audit"
    if cmd == "skill": return skill(sys.argv[2] if len(sys.argv) > 2 else "")
    audit()
    try:
        sys.path.insert(0, HOME + "/tools")
        import judge_bus as _jb
        for _k in ("写了判据!=提炼了", "化到不用想"):
            _h = _jb.find(_k)
            if _h: print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception: pass
    return 0

if __name__ == "__main__":
    sys.exit(main())
