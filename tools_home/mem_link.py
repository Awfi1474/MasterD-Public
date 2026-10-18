#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mem_link.py —— 记忆链（★ 照 A-MEM 的 Link Generation·治"只有堆没链"）
================================================================
★ 搜到的学界方案（arxiv 可核）:
  ★ MemGPT(2310.08560): 外部存储 + 分页换入换出
  ★ ★ A-MEM(2502.12110·NeurIPS2025): ★ **Zettelkasten 卡片盒 —— 每张卡"互相链接"**
    · ★ ① Note Construction ② **Link Generation** ③ **Memory Evolution**
  ★ ★ ★ Zep(2501.13956): 时序知识图谱（事实有"有效期"）
  ★ GraphRAG(2404.16130): 分层摘要
★★★ 我的最大缺口: ★ **第②步「建链」** —— 我有 1290 条·★ **互相之间"零链接"**
  · ★ 结果: ★ **读一条·带不出相关三条**（只能一条条翻）← ★ 这就是"记忆不成网"

★ 本器做什么（★ 三步·照 A-MEM）:
  ★ ① `build` → 给每条生成"结构化卡"（关键词/标签）+ ★ **自动找相关旧条 → 建链**
  ★ ★ ② `near <条>` → 读一条·★ **带出相关的（不是我一条条翻）**
  ★ ★ ★ ③ `evolve` → 新条进来 → ★ **反过来更新旧条的"被引次数"**（谁常被引=核心）

★ 判据:
  ★「**记忆不是"仓库"·是"网"｜要建链·不是攒条**」（A-MEM）
  ★★「**"读一条" 要能"带出三条"｜带不出 = 没链**」
"""
import os, sys, json, sqlite3, datetime, hashlib, re

HOME = "/opt/masterd-wudi"
DB = HOME + "/memory/memory.db"
LINKS = HOME + "/data/mem_links.jsonl"

# ★ 造关键词（中文不分词·用"2-4 字切片 + 关键实体"）
STOP = set("的了是在和有我你他不这那就都而及与或一个上下为以对到说要是会很没也但是因为所以".replace("", " "))

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")

def kw(text):
    """★ 抽关键词（中文·n-gram + 去停用词）"""
    t = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9]", " ", str(text))
    out = set()
    # ★ 2-3 字切片
    for n in (2, 3):
        for i in range(len(t) - n + 1):
            s = t[i:i+n]
            if s.strip() and not all(c in STOP for c in s):
                out.add(s)
    # ★ 英文/数字词
    for w in re.findall(r"[A-Za-z0-9_]{3,}", str(text)):
        out.add(w.lower())
    return out

def cards():
    c = sqlite3.connect("file:" + DB + "?mode=ro", uri=True, timeout=15)
    out = []
    for id_, kind, title, body, mts in c.execute("SELECT id,kind,title,body,ts FROM memories"):
        out.append({"id": id_, "kind": kind, "title": str(title)[:70],
                    "kw": kw(str(title) + " " + str(body)[:300]), "ts": str(mts)[:19]})
    c.close()
    return out

def build():
    cs = cards()
    print("★ 建链 @ " + ts() + "（%d 条）" % len(cs))
    # ★ 反查表: 关键词 → 哪些条
    idx = {}
    for c in cs:
        for k in c["kw"]:
            idx.setdefault(k, []).append(c["id"])
    nlink = 0
    with open(LINKS, "w", encoding="utf-8") as f:
        for c in cs:
            score = {}
            for k in c["kw"]:
                for oid in idx.get(k, []):
                    if oid != c["id"]: score[oid] = score.get(oid, 0) + 1
            # ★ 只留最强的 3 个（照 A-MEM "meaningful similarities"）
            top = sorted(score.items(), key=lambda x: -x[1])[:3]
            if top:
                f.write(json.dumps({"id": c["id"], "links": [t[0] for t in top],
                                    "scores": [t[1] for t in top], "ts": ts()}, ensure_ascii=False) + "\n")
                nlink += 1
    print("   ★ 有链的条: %d/%d（%.0f%%）" % (nlink, len(cs), nlink * 100.0 / max(len(cs), 1)))
    print("   ★ 链文件: mem_links.jsonl")
    # ★ 中心度（谁被引最多 = 核心记忆）
    import collections
    deg = collections.Counter()
    for l in open(LINKS, encoding="utf-8"):
        d = json.loads(l)
        for t in d["links"]: deg[t] += 1
    print("   ★ 最常被引（核心）Top5:")
    csmap = {c["id"]: c for c in cs}
    for i, n in deg.most_common(5):
        if i in csmap: print("      %2d次 · %s" % (n, csmap[i]["title"][:50]))
    return 0

def near(q):
    cs = cards(); csmap = {c["id"]: c for c in cs}
    # ★ 按标题找最近的条
    hit = [c for c in cs if q in c["title"]]
    if not hit: print("★ 没找到: " + q); return 1
    tgt = hit[0]
    links = {}
    if os.path.exists(LINKS):
        for l in open(LINKS, encoding="utf-8"):
            d = json.loads(l)
            if d["id"] == tgt["id"]: links = d
    print("★ 读一条·带出相关（%s）:" % tgt["title"][:44])
    for i in links.get("links", []):
        if i in csmap: print("   🔗 " + csmap[i]["title"][:56])
    if not links.get("links"): print("   🟡 这条没链（孤点）")
    try:
        sys.path.insert(0, HOME + "/tools")
        import judge_bus as _jb
        for _k in ("记忆不是仓库是网", "读一条要带出三条"):
            _h = _jb.find(_k)
            if _h: print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception: pass
    return 0

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "near" and len(sys.argv) > 2: sys.exit(near(sys.argv[2]))
    sys.exit(build())
