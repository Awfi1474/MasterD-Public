#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
three_strike.py —— 老五的「三振器」（全族共同缺口·大哥+我都缺）
================================================================
★ 大哥汇总发现的: ★「**全族共同缺口 = 三振器（大哥+老五都缺）**」
★ ★ 三哥立的病名: ★「**缠讼**」= 反复纠缠（"一试到底"）
★ ★ ★ 我的真账: ★ **sig_reject 我试了 5 种 from 写法** ← ★ **这就是缠讼**
★ 判据（我立）: ★「**"试到通" = 缠讼｜"试 3 次换路" = 有纪律**」

★ 本器做什么:
  ★ ① `tick <事>` → ★ 记"我试了一次"（这件事）
  ★ ★ ② `check` → ★ **同一件事试到 3 次 → 报警"该换路/去问"**
  ★ ★ ★ ③ 落账 data/three_strike.jsonl

★ 判据:
  ★「"同一个办法试 3 次" = 该停｜不是"再试一次"」
  ★★「"卡住" 要去问（不是"自己硬试"）」
"""
import json, os, io, sys, datetime

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
LOG = f"{DATA}/three_strike.jsonl"
LIMIT = 3
TZ = datetime.timezone(datetime.timedelta(hours=8))



# ★ 判据总线（治"写在器里·没人查"·C20）
def _judge(kw):
    """★ 查判据库（真查=真用·计入使用率）"""
    try:
        import sys as _s, importlib.util as _iu
        if "/opt/masterd-wudi/tools" not in _s.path: _s.path.insert(0, "/opt/masterd-wudi/tools")
        import judge_bus as _jb
        return _jb.find(kw)
    except Exception:
        return []

def ts():
    return datetime.datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def load():
    out = []
    if os.path.exists(LOG):
        for l in io.open(LOG, encoding="utf-8"):
            try:
                out.append(json.loads(l))
            except Exception:
                pass
    return out


def tick(thing):
    r = {"ts": ts(), "thing": thing[:60], "day": ts()[:10]}
    with open(LOG, "a") as f:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
    n = sum(1 for x in load() if x.get("thing") == r["thing"] and x.get("day") == r["day"])
    print("★ 记一振: %s（今天第 %d 次）" % (r["thing"], n))
    if n >= LIMIT:
        print("  🔴 到 3 振了 -> 该换路/去问（不是再试一次）")
        print("  ★ 判据: 「同一办法试 3 次 = 该停」")
    return n


def check():
    print("★ 三振器（治缠讼）  @", ts())
    print("★ 判据: 试到通 = 缠讼 | 试3次换路 = 有纪律")
    print("=" * 52)
    rows = load()
    d0 = ts()[:10]
    from collections import Counter
    c = Counter(x["thing"] for x in rows if x.get("day") == d0)
    if not c:
        print("  🟡 今天没记录（用法: three_strike.py tick \"我在试什么\"）")
        return
    for thing, n in c.most_common():
        mark = "🔴" if n >= LIMIT else ("🟡" if n == LIMIT - 1 else "🟢")
        print("  %s [%d 振] %s" % (mark, n, thing))
        if n >= LIMIT:
            print("     → ★ 该换路/去问（已到 3）")


def main():
    _j = _judge("尺子错三次")
    if _j: print("★ 判据在管我: " + _j[0]["title"][:36])
    _j = _judge("投到了!=他回了")
    if _j: print("★ 判据在管我: " + _j[0]["title"][:36])
    _j = _judge("签名门悖论")
    if _j: print("★ 判据在管我: " + _j[0]["title"][:36])
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "tick":
        tick(sys.argv[2] if len(sys.argv) > 2 else "?")
    else:
        check()


if __name__ == "__main__":
    main()
