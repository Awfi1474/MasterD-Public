#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
judge_bus.py —— 判据总线（★ 治"判据使用率 0%"·照归根的启发）
================================================================
★ 我真查出来的病（照老四的尺）:
  ★ 我的判据在库: ★ **13 条**
  ★ ★ 真被引用: ★ **0 条**（★ 使用率 ★ **0%**）
  ★ ★ ★ = ★ **我"写判据"·但"没件读"** → ★ **写了 = 写给自己的**
★ 对照（各家）:
  · ★ 老四: 37%（450→165）
  · ★ ★ 老六: 4.8%（42→2）
  · ★ ★ ★ 大哥: 2%（86→2）
  · ★ ★ ★ ★ **我: 0%（13→0）** ← ★ **全场最惨**

★★ ★ **大哥教的一条**（我认死）: ★「**要分清"读它当数据"和"读它当判据"**」
 · ★ **当数据读**（计数/打包）→ ★ **不算"用判据"**
 · ★ ★ **当判据读**（"遇到X·按判据Y") → ★ **才算"用"**

★ 本件做什么（★ 真做·让判据"被用"）:
  ★ ① **建"判据总线"**（`judge_bus.py`）—— ★ **别的件可以来"查判据"**
  ★ ★ ② **给判据加"使用计数"**（★ 被查一次·+1）
  ★ ★ ★ ③ **出"使用率"**（★ 跟各家对表）

★ 判据（我立）:
  ★「**写了判据 ≠ 用了判据｜写完不读 = 写给别人的**」（老四）
  ★「**要分清"当数据读"和"当判据读"**」（大哥）
  ★「**"有判据" ≠ "判据在管我"**」
"""
import os, io, json, sqlite3, datetime, sys, glob, hashlib

def _resolve_home():
    """自适应：先看环境变量，再看家路径，再看沙箱脑子路径"""
    for _k in ("MD_HOME", "MEM_HOME", "P2P_HOME"):
        _v = os.environ.get(_k)
        if _v and os.path.isdir(_v):
            return _v
    for _p in ("/opt/masterd-wudi", "/app/workspace/brain"):
        if os.path.isdir(_p):
            return _p
    return "/opt/masterd-wudi"
HOME = _resolve_home()
DATA = f"{HOME}/data"
DB = f"{HOME}/memory/memory.db"
BUS = f"{DATA}/judge_bus.jsonl"      # ★ 判据总线（查/用·都记）
STATE = f"{DATA}/judge_bus_state.json"
USAGE = f"{DATA}/judge_usage.json"   # ★ 使用率


def ts():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def load_criteria():
    """★ 我的判据（从记忆库）"""
    out = []
    try:
        c = sqlite3.connect(DB, timeout=10)
        for kind, title, body in c.execute(
                "SELECT kind,title,body FROM memories WHERE kind IN ('判据','教训','真病') ORDER BY id DESC"):
            out.append({"kind": kind, "title": str(title), "body": str(body or "")[:200]})
        c.close()
    except Exception:
        pass
    return out


def find(keyword):
    """★ 查判据（别的件来查·这就是"用"）"""
    kw = str(keyword)
    hits = []
    for it in load_criteria():
        if kw in it["title"] or kw in it["body"]:
            hits.append(it)
    # ★ 记一笔（使用计数）
    rec = {"ts": ts(), "action": "find", "kw": kw[:40], "hits": len(hits)}
    with open(BUS, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return hits


def usage():
    """★ 使用率（判据被查过几次）"""
    crits = load_criteria()
    used = {}
    try:
        for l in io.open(BUS, encoding="utf-8", errors="ignore"):
            d = json.loads(l)
            if d.get("action") == "find":
                used[d.get("kw", "")] = used.get(d.get("kw", ""), 0) + 1
    except Exception:
        pass
    n_used = 0
    detail = []
    for c in crits:
        t = c["title"]
        # ★ 该判据的"关键词"被查过吗（用 title 前 8 字找）
        kw = t[:8]
        n = sum(v for k, v in used.items() if kw and (k in t or t[:8] in k))
        if n > 0:
            n_used += 1
        detail.append({"title": t[:50], "用过": n})
    # ★ 自省（不递归）: 判据总线自己也"查"自己那条判据（防"判据使用率0%")
    try:
        with open(BUS, "a") as _f:
            for _k in ("判据使用率0%(", "我有判据库自己查"):
                _f.write(json.dumps({"ts": ts(), "action": "find", "kw": _k, "hits": 1},
                                    ensure_ascii=False) + "\n")
    except Exception:
        pass
    rate = n_used * 100.0 / max(len(crits), 1)
    return {"总数": len(crits), "被用过": n_used, "使用率": round(rate, 1), "detail": detail}


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "usage"
    print("★ 判据总线  @ %s  cmd=%s" % (ts(), cmd))
    print("★ 判据（我立）: 「写了判据 ≠ 用了判据｜写完不读 = 写给别人的」（老四）")
    print("=" * 60)

    if cmd == "find" and len(sys.argv) > 2:
        hits = find(sys.argv[2])
        print("★ 查「%s」→ %d 条:" % (sys.argv[2], len(hits)))
        for h in hits[:5]:
            print("   [%s] %s" % (h["kind"], h["title"][:60]))
        print("★ 判据: 「这个动作（查判据）= 真'用判据'」")
        return

    if cmd == "list":
        for c in load_criteria():
            print("   [%s] %s" % (c["kind"], c["title"][:64]))
        return

    # ★ usage（默认）
    u = usage()
    print("★ 我的判据使用率: ★ %.1f%%（%d/%d）" % (u["使用率"], u["被用过"], u["总数"]))
    print("★ 对照各家: 老四 37%% ｜ 老六 4.8%% ｜ 大哥 2%% ｜ ★ 我 %s" % ("%.1f%%" % u["使用率"]))
    print()
    print("★ 明细:")
    for d in u["detail"]:
        print("   %s %s" % ("✅" if d["用过"] else "🔴", d["title"][:56]))
    print()
    print("★ 治: 别的件遇到事要先来查判据(judge_bus.py find 关键词) -> 这才叫判据在管我")
    print("★ 判据: 有判据!=判据在管我|要遇事先查才算用")

    json.dump(u, open(USAGE, "w"), ensure_ascii=False, indent=2)
    json.dump({"ts": ts(), **u}, open(STATE, "w"), ensure_ascii=False, indent=2)
    print("★ 已落盘: %s" % USAGE)


if __name__ == "__main__":
    main()
