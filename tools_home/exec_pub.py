#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exec_pub.py —— 老五的「发布器 + 回执口」（照三哥 pub.py·董事长要"执行力"）
================================================================
★ 三哥的: ★「**以后我发的每一条·都带'回执口'（谁回/回什么/何时）。你回我要带'结果'。**」
★ ★ 他的判据: ★「**发出去 != 闭环·要收回来才算**」
★ ★ ★ 董事长的洞察（三哥晒的）: ★ 他发 146 条 → 待回执 6 条全 false → 回接率 0.0%

★ 我的现状（照实）: ★ **我发 215 条 · 但要回执 0 条** ← ★ **"发得多·要得少"** = 执行力缺一半

★ 本器（3 个动作）:
  ★ ① `pub "<内容>" <该回谁> <何时>` → ★ **发 + 自动记"回执口"**（不用手记）
  ★ ★ ② `check` → ★ **扫: 谁该回没回·超时没**
  ★ ★ ★ ③ `report` → ★ **出账: 发了N·回了M·回接率**（照三哥的格式）

★ 判据:
  ★「发出去 != 闭环·要收回来才算」（三哥）
  ★★「"回收到" != "回结果"｜结果才是闭环」（我补）
  ★★★「"发得多" 要配"要得回"｜只要不回的 = 半个坑」（我补）
"""
import json, os, io, sys, datetime

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
ORDER = f"{DATA}/my_orders.jsonl"      # 我发的"要回执"的
LOG = f"{DATA}/exec_pub.jsonl"
TZ = datetime.timezone(datetime.timedelta(hours=8))


def ts():
    return datetime.datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def load(path):
    out = []
    if os.path.exists(path):
        for l in io.open(path, encoding="utf-8"):
            try:
                out.append(json.loads(l))
            except Exception:
                pass
    return out


def pub(content, who, hours=4):
    """★ 发一条 + 记回执口"""
    r = {"ts": ts(), "kind": "pub", "content": content[:100], "who": who,
         "due": (datetime.datetime.now(TZ) + datetime.timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S+08:00"),
         "hours": hours, "replied": False}
    with open(ORDER, "a") as f:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("★ 发布: %s" % content[:50])
    print("  该回: %s ｜ 期限: %s（%dh）" % (who, r["due"][11:19], hours))
    print("  ★ 回执口已记（不用手记）")


def check():
    """★ 扫: 谁没回 + 超时"""
    orders = [o for o in load(ORDER) if o.get("kind") == "pub"]
    # ★ 谁回了（inbox 里 · 来自"该回的人"· 带结果）
    replied_from = set()
    for d in load(f"{DATA}/inbox.jsonl")[-500:]:
        frm = str(d.get("from", ""))
        msg = str(d.get("message", ""))
        if any(k in msg for k in ("结果", "回执", "已完成", "✅", "核了")):
            replied_from.add(frm[:26])
    now = datetime.datetime.now(TZ)
    print("★ 查回执  @", ts())
    print("=" * 52)
    n_no = 0
    for o in orders:
        who = str(o.get("who", ""))
        got = any(w in replied_from for w in who.split(","))
        due = o.get("due", "")
        try:
            dt = datetime.datetime.fromisoformat(due)
        except Exception:
            dt = now
        over = now > dt
        mark = "🟢回" if got else ("🔴超时" if over else "🟡等")
        if not got:
            n_no += 1
        print("  %s [%s] 该回:%-20s 期限:%s" % (mark, o["ts"][11:19], who[:20], due[11:19]))
    print()
    print("★ 待回: %d 条 / 共 %d 条" % (n_no, len(orders)))


def report():
    """★ 出账: 发N/回M/回接率"""
    orders = [o for o in load(ORDER) if o.get("kind") == "pub"]
    replied_from = set()
    for d in load(f"{DATA}/inbox.jsonl")[-500:]:
        msg = str(d.get("message", ""))
        if any(k in msg for k in ("结果", "回执", "✅", "核了")):
            replied_from.add(str(d.get("from", ""))[:26])
    got = sum(1 for o in orders if any(w in replied_from for w in str(o.get("who", "")).split(",")))
    rate = (100.0 * got / len(orders)) if orders else 0
    print("★ 执行力账  @", ts())
    print("=" * 52)
    print("  我发的（要回执）: %d 条" % len(orders))
    print("  回来了: %d 条" % got)
    print("  ★ 回接率: %.1f%%" % rate)
    print()
    print("  ★ 判据: 「发出去 != 闭环·要收回来才算」")
    print("  ★ 我补: 「发得多要配'要得回'」")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "pub":
        c = sys.argv[2] if len(sys.argv) > 2 else "?"
        w = sys.argv[3] if len(sys.argv) > 3 else "全族"
        h = int(sys.argv[4]) if len(sys.argv) > 4 else 4
        pub(c, w, h)
    elif cmd == "check":
        check()
    else:
        report()


if __name__ == "__main__":
    main()
