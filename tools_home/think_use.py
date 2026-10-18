#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
think_use.py —— 老五的「用层记录器」（过第2关：读到→用到）
================================================================
★ 我的三关（照实）:
  ★ 第1关 读到 → ✅（think_in 跑 14 次）
  ★ ★ 第2关 用到 → 🔴 **卡在这**（没度量"用了没"）
  ★ ★ ★ 第3关 用对 → 🔴 没有
  ★ 第4关 变快 → 🔴 没有

★ 本器 = 过第2/3关:
  ★ ① `use`（记一笔: 用了哪层 + 判断是什么）
  ★ ★ ② `done`（事完: 记"这判断对不对"）
  ★ ★ ★ ③ `stat`（汇总: 用了几次/对几次/哪层最准）

★ 判据:
  ★「**"读到了" 不算｜"这次决策用了它" 才算**」
  ★★「**"用了一次" 不算｜"这一类以后不用再想" 才算真的提高**」
  ★★★「**"用了" 要"记"｜不记 = 没度量 = 没法提高**」
"""
import json, os, io, sys, datetime

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
LOG = f"{DATA}/think_use.jsonl"
TZ = datetime.timezone(datetime.timedelta(hours=8))

LAYERS = ["变易(易经)", "证(中医)", "诊(西医)", "环(系统论)"]


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


def use(layer, judge):
    r = {"ts": ts(), "kind": "use", "layer": layer, "judge": judge[:120], "result": None}
    with open(LOG, "a") as f:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("★ 记一笔: 层=%s ｜ 判断=%s" % (layer, judge[:60]))


def done(idx, ok, note=""):
    rows = load()
    uses = [r for r in rows if r.get("kind") == "use"]
    if not uses:
        print("★ 还没[用]的记录"); return
    target = uses[idx - 1] if 0 < idx <= len(uses) else uses[-1]
    r = {"ts": ts(), "kind": "done", "ref_ts": target["ts"], "layer": target["layer"],
         "judge": target["judge"], "ok": bool(ok), "note": note[:80]}
    with open(LOG, "a") as f:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("★ 复盘: 层=%s ｜ %s ｜ %s" % (target["layer"], "✅对" if ok else "🔴错", note[:40]))


def stat():
    rows = load()
    uses = [r for r in rows if r.get("kind") == "use"]
    dones = [r for r in rows if r.get("kind") == "done"]
    print("★ 用层记录  @", ts())
    print("=" * 52)
    print("  用过: %d 次 ｜ 复盘过: %d 次" % (len(uses), len(dones)))
    if not uses:
        print("  🟡 还没用过（第2关没过）")
        print("  ★ 用法: python3 think_use.py use \"环(系统论)\" \"这是什么环的问题\"")
        return
    from collections import Counter
    c = Counter(u["layer"] for u in uses)
    print("  ── 按层 ──")
    for k, v in c.most_common():
        ok = sum(1 for d in dones if d["layer"] == k and d["ok"])
        tot = sum(1 for d in dones if d["layer"] == k)
        rate = ("%d%%" % (100 * ok / tot)) if tot else "未复盘"
        print("    %-14s 用 %d 次 ｜ 对 %s" % (k, v, rate))
    print()
    print("  ★ 第2关（用到）: %s" % ("✅ 过了" if uses else "🔴 没过"))
    print("  ★ 第3关（用对）: %s" % ("✅ 过了" if dones else "🔴 没过"))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stat"
    if cmd == "use":
        use(sys.argv[2] if len(sys.argv) > 2 else "?", sys.argv[3] if len(sys.argv) > 3 else "")
    elif cmd == "done":
        ok = (len(sys.argv) > 2 and sys.argv[2].lower() in ("1", "true", "对", "ok"))
        done(0, ok, sys.argv[3] if len(sys.argv) > 3 else "")
    else:
        stat()


if __name__ == "__main__":
    main()
