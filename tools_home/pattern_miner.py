#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·模式提炼器 pattern_miner.py（照 SEA-Mem·arXiv:2603.13676）
★ 缘起：董事长点「你什么时候出去过」→ 我出去搜到 TheraAgent 的 SEA-Mem：
   「learns prognostic patterns from accumulated cases」
   → 我的 L2/L3 只存不学（2308条·只检索）→ 补「从案例提炼模式」

★ 判据（我的）：
  「存 != 学｜检索 != 提炼｜模式 = 从 N 条案例里看出 1 条规律」
★ 性质：照预印本思路自制·非直接套用；产出过记忆门（标来源+性质）
"""
import json, os, sqlite3, datetime, re
from collections import Counter

HOME = "/opt/masterd-wudi"
DB = HOME + "/memory/memory.db"
OUT = HOME + "/memory/L3-语义/模式提炼.jsonl"

def load_recent(days=3, limit=400):
    """取最近 N 天记忆（当'案例'）"""
    c = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)
    cut = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    rows = c.execute(
        "SELECT ts,kind,who,title,body FROM memories WHERE ts>=? ORDER BY ts DESC LIMIT ?",
        (cut, limit)).fetchall()
    c.close()
    return rows

def mine(rows):
    """提炼模式（不是摘要·是规律）"""
    pats = []
    # ① 反复出现的词（>阈值 = 模式）
    kw = Counter()
    STOP = set("的了是我你我他在有和就都不一也很还这那什么怎么为以可以要对会说做".replace("", " "))
    for ts,k,w,t,b in rows:
        for word in re.findall(r"[\u4e00-\u9fa5]{2,4}", (str(t or "") + str(b or ""))):
            if word not in STOP: kw[word] += 1
    for word, n in kw.most_common(8):
        if n >= 5:
            pats.append({"型": "反复词", "模式": word, "证据": "%d条出现" % n})
    # ② 反复出现的判据句式
    crit = Counter()
    for ts,k,w,t,b in rows:
        for m in re.findall(r"[「【]([^」】]{4,20})[」】]", str(b or "")):
            crit[m] += 1
    for phrase, n in crit.most_common(5):
        if n >= 2:
            pats.append({"型": "反复判据", "模式": phrase, "证据": "%d次" % n})
    # ③ 反复出错（打回记录）
    dl = HOME + "/data/decide_log.jsonl"
    fails = Counter()
    if os.path.exists(dl):
        for l in open(dl, encoding="utf-8", errors="ignore"):
            try:
                d = json.loads(l)
                if d.get("结果") == "打回":
                    for x in d.get("缺", []): fails[x] += 1
            except Exception: pass
    for f, n in fails.most_common(5):
        if n >= 2:
            pats.append({"型": "反复打回", "模式": f, "证据": "%d次" % n})
    return pats

if __name__ == "__main__":
    rows = load_recent()
    pats = mine(rows)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    now = datetime.datetime.now().isoformat(timespec="seconds")
    with open(OUT, "a", encoding="utf-8") as f:
        for p in pats:
            p["ts"] = now; p["源"] = "pattern_miner(照SEA-Mem·arXiv:2603.13676·预印本)"
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    print("★ 模式提炼器（照 SEA-Mem）| 案例 %d 条 → 提炼 %d 条模式" % (len(rows), len(pats)))
    for p in pats:
        print("  [%s] %s (%s)" % (p["型"], p["模式"], p["证据"]))
