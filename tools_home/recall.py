#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""recall.py —— 查账器（★ 法家·术：问"做过吗"→先查账）
================================================================
★ 照三哥的（他 23:00 那条）: ★「"我记得" != "账上有"｜问'做过吗'·必须先查账」
★ 我的病（三哥同款）: 问"我做过吗"·先"想"·不是先"查账"

★ 查哪些账（我的全部账）:
  ★ ① memory.db（记忆库·kind/ts/title）
  ★ ② inbox.jsonl（投递·谁跟我说过）
  ★ ★ ③ action-ledger / 变更账（我改过什么）
  ★ ★ ★ ④ data/*.json（器产出·跑没跑）

★ 判据:
  ★「**"我记得" != "账上有"｜问'做过吗'·必须先查账**」
  ★★「**"问'我做过吗'先想" = 不可靠｜"先查账" = 可靠**」
"""
import os, sys, json, sqlite3, glob, datetime, re

HOME = "/opt/masterd-wudi"
DATA = os.path.join(HOME, "data")
DB = os.path.join(HOME, "memory", "memory.db")

def ts():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

def jl(p, n=None):
    out = []
    if not os.path.exists(p): return out
    for l in open(p, encoding="utf-8", errors="ignore"):
        try: out.append(json.loads(l))
        except Exception: pass
    return out[-n:] if n else out

def search(kw):
    kw = str(kw)
    hits = []
    # ★ ① 记忆库
    try:
        c = sqlite3.connect("file:" + DB + "?mode=ro", uri=True, timeout=10)
        # ★ 2026-11-11 加(照官方字段标准): 支持 -ctx/-task 官方语义过滤 + 检索记账
        _ctx = os.environ.get("LAOWU_CTX") or ""
        _task = os.environ.get("LAOWU_TASK") or ""
        _sql = "SELECT kind,title,ts,context_id,task_id FROM memories WHERE (title LIKE ? OR body LIKE ?)"
        _args = ["%" + kw + "%", "%" + kw + "%"]
        if _ctx:
            _sql += " AND context_id=?"; _args.append(_ctx)
        if _task:
            _sql += " AND task_id=?"; _args.append(_task)
        _sql += " ORDER BY id DESC LIMIT 12"
        for kind, title, mts, cid, tid in c.execute(_sql, tuple(_args)):
            hits.append(("记忆", str(mts)[:19], str(kind), str(title)[:60],
                         "ctx=" + str(cid or "-"), "task=" + str(tid or "-")))
        c.close()
        # ★ 检索记账(检了啥/找到啥·可复盘)
        try:
            import datetime as _dt2
            with open(HOME + "/data/recall_ledger.jsonl", "a", encoding="utf-8") as _rf:
                _rf.write(json.dumps({"ts": _dt2.datetime.now().isoformat(),
                                      "kw": kw[:40], "ctx": _ctx, "task": _task, "hits": len(hits)},
                                     ensure_ascii=False) + "\n")
        except Exception:
            pass
    except Exception as e:
        hits.append(("记忆", "err", "", str(e)[:40]))
    # ★ ② 投递
    n = 0
    for d in jl(os.path.join(DATA, "inbox.jsonl"), 4000)[::-1]:
        if kw in str(d.get("message", "")):
            n += 1
            if n <= 5:
                hits.append(("投递", str(d.get("ts", ""))[:19], str(d.get("from", ""))[:16],
                             str(d.get("message", ""))[:50].replace(chr(10), " ")))
    # ★ ③ 器产出（data/*.json 的 ts）
    for p in glob.glob(os.path.join(DATA, "*.json")):
        try:
            d = json.load(open(p))
            if isinstance(d, dict) and kw in json.dumps(d, ensure_ascii=False):
                hits.append(("产出", str(d.get("ts", "?"))[:19], os.path.basename(p), ""))
        except Exception: pass
    return hits

def main():
    if len(sys.argv) < 2:
        print("用法: recall.py <关键词>"); return 1
    kw = sys.argv[1]
    print("★ 查账: " + kw + "  @ " + ts())
    hits = search(kw)
    if not hits:
        print("  🔴 账上没有（★ 不许凭想·这就是'没做过'）")
        return 1
    print("  ✅ 账上有 %d 处:" % len(hits))
    for _h in hits:
        _h = tuple(_h)
        if len(_h) >= 6:
            _src, _t, _who, _what, _ctx, _task = _h[0], _h[1], _h[2], _h[3], _h[4], _h[5]
            print("   [%s] %s | %-14s %s (%s %s)" % (_src, _t, _who, _what, _ctx, _task))
            continue
        src, t, who, what = _h[:4]
        if src == "产出": print("   [%s] %-12s %s" % (src, t, who))
        else: print("   [%s] %s | %-16s %s" % (src, t, who, what))
    # ★ 判据（真查·计入使用率）
    try:
        sys.path.insert(0, HOME + "/tools")
        import judge_bus as _jb
        for _k in ("我记得!=账上有", "问做过吗先查账"):
            _h = _jb.find(_k)
            if _h: print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception: pass
    return 0

if __name__ == "__main__":
    sys.exit(main())
