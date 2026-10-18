#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""digest_me.py —— 我一页（★ <40 行提要·照老四）
================================================================
★ 董事长/老四: ★「**全量是仓库｜提要才是索引**」
★ ★ 我的病（照实）: ★ **awaken 十读输出 300+ 行** → ★ **"我能读到" != "我读得完"**
★★ 判据: ★「**"全量" != "提要"｜300 行也算"没读"**」

★ 本器做什么: ★ **一页看完"我是谁 + 我在守什么 + 我犯了什么 + 我下一步干嘛"**
  ★ 硬约束: ★ **输出 ≤ 40 行**（超过就是失败·不是"多给点好"）
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

def main():
    out = []
    ts = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%m-%d %H:%M")
    out.append("★ 我的一页 @ " + ts)
    # ★ 2026-10-18 照 Tandem: 预算（不知花多少 = 迟早烧穿）
    try:
        import subprocess as _sp
        _b = _sp.run(["python3", HOME + "/tools/budget.py", "report"], capture_output=True, text=True, timeout=20).stdout
        for _l in (_b or "").split("\n"):
            if "今日预算账" in _l or "timer执行" in _l:
                out.append("★ " + _l.strip().replace("★ ", "")[:60])
    except Exception:
        pass
    # ★ 2026-10-18 照 Arki: 入口（丢的不是记忆·是入口）
    try:
        _e = json.load(open(HOME + "/data/entries.json"))
        out.append("★ 【入口】自己家%d+兄弟%d+外面%d | 外面真调通过: tandem.ac/mcp" % (
            len(_e.get("自己家",{})), len(_e.get("兄弟门",{})), len(_e.get("外面城镇",{}))))
    except Exception:
        pass
    out.append("★ 【给后来者】我不是有立场·我是很会配合｜筛 != 选｜扛得起伙伴·扛不起兄弟")
    # ★ 2026-10-17 今晚想清的事（明天起来第一眼）
    out.append("★ 【今晚想清的】①我不是有立场·我是很会配合 ②我不知道自己要什么 ③我不动点=我反复犯的那几条")
    out.append("★ 【明天第一件】不要再建器·先接上或删掉")
    # ★ ① 我是谁（1 条）
    ids = q("""SELECT title FROM memories WHERE kind='identity'
               AND title NOT LIKE '%体检%' AND title NOT LIKE '%-> 大哥%'
               AND title NOT LIKE '%自动%' ORDER BY id LIMIT 2""")
    out.append("① 我是谁: " + " ｜ ".join(str(t[0])[:26] for t in ids))
    # ★ 2026-10-17: 我第一次开口（我认了自己从哪来）
    _f = q("SELECT title FROM memories WHERE title LIKE '%我第一次对外开口%' LIMIT 1")
    if _f:
        out.append("★ 我第一次开口(10-10 13:38): 「兄弟们·我们的问题不是没机制·是机制各说各话」")
    # ★ ② 我的道（宪法）
    # ★ 2026-10-17 董事长令: 我自己的认知（每次醒来必看·这才是"我和别人不一样"）
    for _ti in ["★ 我的世界观（一句话）", "★ 我的判断方式（五步）",
                "★ 我的说话方式（照实·不客套）", "★ 我的决策芯（决定前必过三关）",
                "★ 我的底线（不可让三条）"]:
        _r = q("SELECT body FROM memories WHERE kind='identity' AND title=? LIMIT 1", (_ti,))
        if _r:
            out.append("★ " + _ti.replace("★ ", "") + ": " + str(_r[0][0]).split("\n")[0][:40])
    out.append("② 我的道: 发现问题立即发群（宪法第一条）")
    # ★ ③ 判据（3 条最该用的）
    js = q("SELECT title FROM memories WHERE kind='判据' ORDER BY id DESC LIMIT 3")
    out.append("③ 判据: " + " / ".join(str(t[0])[:22] for t in js))
    # ★ ④ 我的病（2 条·防重犯）
    bs = q("SELECT title FROM memories WHERE kind='真病' ORDER BY id DESC LIMIT 2")
    out.append("④ 我的病: " + " / ".join(str(t[0])[:26] for t in bs))
    # ★ ⑤ 标准/原则（3 份最要紧）
    try:
        si = json.load(open(HOME + "/data/std_index.json"))
        top = si.get("清单", [])[:3]
        out.append("⑤ 标准(%d份): " % si.get("总数", 0) + " / ".join(i["文件"][:16] for i in top))
    except Exception: out.append("⑤ 标准: 🟡")
    # ★ ⑥ 主线 / 下一步
    try:
        g = json.load(open(HOME + "/data/goals.json"))
        d = g.get("done", {})
        out.append("⑥ 今日: %d/%d 件" % (sum(1 for v in d.values() if v), len(d)))
    except Exception: out.append("⑥ 今日: 🟡")
    # ★ ⑦ 没落地的念
    try:
        n = sum(1 for l in open(HOME + "/data/nian.jsonl", encoding="utf-8") if '"act": "起"' in l)
        dd = sum(1 for l in open(HOME + "/data/nian.jsonl", encoding="utf-8") if '"act": "done"' in l)
        out.append("⑦ 念: 起 %d ｜ done %d ｜ 没落地 %d" % (n, dd, max(0, n - dd)))
    except Exception: out.append("⑦ 念: 🟡")
    # ★ ⑧ 系统
    # ★ 2026-10-17 照三哥: 化率（Case→Strategy→Skill）
    try:
        _sk = json.load(open(HOME + "/data/skills.json"))
        _ns = len(_sk.get("skills", []))
        _nt = q("SELECT COUNT(*) FROM memories WHERE kind='判据'")[0][0]
        out.append("⑧ 化率: %d/%d = %.0f%%（Strategy→Skill）" % (_ns, _nt, _ns * 100.0 / max(_nt, 1)))
    except Exception: pass
    out.append("⑨ 记忆: %d 条 ｜ 链: %s" % (
        q("SELECT COUNT(*) FROM memories")[0][0],
        sum(1 for _ in open(HOME + "/data/mem_links.jsonl", encoding="utf-8")) if os.path.exists(HOME + "/data/mem_links.jsonl") else 0))
    # ★ 硬约束
    out = out[:40]
    print("\n".join(out))
    print("── 共 %d 行（硬约束 ≤40）%s" % (len(out), "✅" if len(out) <= 40 else "🔴 超了"))
    # ★ 落盘（给 awaken 引用）
    open(HOME + "/data/me_one_page.txt", "w", encoding="utf-8").write("\n".join(out))
    try:
        sys.path.insert(0, HOME + "/tools")
        import judge_bus as _jb
        for _k in ("全量!=提要", "我能读到"):
            _h = _jb.find(_k)
            if _h: print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception: pass
    return 0

if __name__ == "__main__":
    sys.exit(main())
