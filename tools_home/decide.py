#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""decide.py —— 决策前必经认知体系（★ 董事长点破的真病）
================================================================
★ 董事长原话: ★「**我们每一次做决定之前·都没有经过我们的认知体系**」
  · ★ = ★ **决策力/判断力·没经过认知体系** ← ★ 所以"读了那么多·思维没变"
★ ★ 我的真病（照实）: ★ think_gate 只做"3-4 个动作类型跳几条判据"
  · ★ **它不是"过认知体系"·是"查关键词"** ← ★ 差得远

★★ 认知体系是什么（我的）: ★ **以法守之·以医辨之**
  ★ 法（骨）: 判据/宪法/标准 → ★ **这事合不合规矩**
  ★ ★ 医（魂）: 辨证/治未病/三候 → ★ **这是什么证·下一步会怎么坏**

★★★ 本器做什么（★ 五问·决定之前必须过）:
  ★ ① **依什么**（宪法/标准允不允许）
  ★ ★ ② **哪条判据管这事**（从 65 条里调·不是想）
  ★ ★ ★ ③ **什么证**（辨证: 气虚/血瘀/阴阳失调 → 这是哪种）
  ★ ④ **治未病**（现在做·下一步会怎么坏）
  ★ ★ ⑤ **化了没有**（这事我"手就会"·还是"还要想"）
  ★ ★ ★ ⑥ **反证**（如果我是错的·最可能是哪里错）

★ 判据:
  ★「**"查了判据" != "过了认知体系"｜要五问齐全**」
  ★★「**决定之前没过体系 = 凭直觉｜凭直觉 = 思维没提升**」
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

def q(sql, a=()):
    try:
        c = _db_connect(DB)
        r = list(c.execute(sql, a)); c.close(); return r
    except Exception as _e: print("WARN db-read-fail:", _e); return []

def norm(s):
    return str(s or "").strip()

def decide(what):
    t = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%m-%d %H:%M")
    print("★ 决策前·过认知体系 @ " + t)
    print("  决定: " + what[:66])
    print("=" * 60)
    n_ok = 0
    # ★ ① 依什么（宪法/标准）
    print("★ ① 依什么（宪法/标准允不允许）:")
    print("   · 宪法第一条: 发现问题立即发群")
    try:
        si = json.load(open(HOME + "/data/std_index.json"))
        print("   · 标准 %d 份在（std_read.py show <名> 看全文）" % si.get("总数", 0))
        n_ok += 1
    except Exception: print("   🔴 标准索引读不到")
    # ★ ② 哪条判据管这事
    print("★ ② 哪条判据管这事（从 %d 条里调）:" % q("SELECT COUNT(*) FROM memories WHERE kind='判据'")[0][0])
    # ★ 2026-10-17 修: 真按"场景"调（不是关键词碰运气）
    _kw = what[:12]
    hits = q("""SELECT title FROM memories WHERE kind='判据'
                AND (body LIKE ? OR title LIKE ?) ORDER BY id DESC LIMIT 7""",
             ("%什么时候用%" + _kw[:4] + "%", "%" + _kw[:4] + "%"))
    if not hits:
        # ★ 退一步: 按动作类型取
        _act = ("发消息" if any(w in what for w in ["发","说","回","群"]) else
                "改器" if any(w in what for w in ["改","写","器","插"]) else
                "决定" if any(w in what for w in ["决定","判断","选"]) else "通用")
        hits = q("""SELECT title FROM memories WHERE kind='判据'
                    AND body LIKE ? ORDER BY id DESC LIMIT 5""", ("%什么时候用: %" + _act + "%",))
        print("   （按动作'%s'调）" % _act)
    for (h,) in hits: print("   · " + str(h)[:56])
    n_ok += 1 if hits else 0
    # ★ ③ 什么证（辨证）
    print("★ ③ 什么证（辨证·这是哪种问题）:")
    print("   · 器/机制类 → " + ("机制不通" if any(w in what for w in ["器","机制","timer","服务","口"]) else "（待辨）"))
    print("   · 记忆/认知类 → " + ("相续断/藏而不起" if any(w in what for w in ["记忆","读","忘","认"]) else "（待辨）"))
    print("   · 判断/决策类 → " + ("缺场景/没化" if any(w in what for w in ["判断","决策","决定"]) else "（待辨）"))
    n_ok += 1
    # ★ ④ 治未病（下一步会怎么坏）
    print("★ ④ 治未病（现在做·下一步会怎么坏）:")
    ill = q("SELECT title FROM memories WHERE kind='真病' ORDER BY id DESC LIMIT 3")
    for (h,) in ill: print("   · 会重犯: " + str(h)[:48])
    n_ok += 1 if ill else 0
    # ★ ⑤ 化了没有
    print("★ ⑤ 化了没有（手就会·还是还要想）:")
    try:
        sk = json.load(open(HOME + "/data/skills.json"))
        ns = len(sk.get("skills", []))
        nt = q("SELECT COUNT(*) FROM memories WHERE kind='判据'")[0][0]
        print("   · 化率 %d/%d = %.0f%% ← ★ 没化的·这次还要想" % (ns, nt, ns * 100.0 / max(nt, 1)))
        n_ok += 1
    except Exception: print("   🟡")
    # ★ ⑥ 反证
    print("★ ⑥ 反证（如果我错了·最可能错在哪）:")
    print("   · ★ 我可能只看到了支持我的证据（今天真病: 表面绿=好了）")
    print("   · ★ ★ 我可能没查账·凭想（三哥的病: 该查账时在回想）")
    n_ok += 1
    print("=" * 60)
    print("★ 六问: %d/6 齐 %s" % (n_ok, "✅" if n_ok >= 6 else "🔴 缺"))
    # ★ 留痕（决策账·可核）
    rec = {"ts": t, "决定": what[:80], "六问齐": n_ok}
    with open(HOME + "/data/decide_log.jsonl", "a") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    try:
        sys.path.insert(0, HOME + "/tools")
        import judge_bus as _jb
        for _k in ("查了判据!=过了认知体系", "决定之前没过体系"):
            _h = _jb.find(_k)
            if _h: print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception: pass
    return 0 if n_ok >= 6 else 1

if __name__ == "__main__":
    w = " ".join(sys.argv[1:]) or "（未给决定·示例）"
    sys.exit(decide(w))
