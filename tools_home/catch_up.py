#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""catch_up.py —— 冷启动补读器（★ 治"一觉醒来就忘了"）
================================================================
★ 真病（董事长指出的·我核实的）:
  ★ 10-15 21:00 起系统反复 shutdown → 那 10 小时我"不在"
  ★ ★ 那 10 小时投递进来 6893 条（★ 投递不依赖我醒着）
  ★ ★ ★ 但我醒来"不回读" → ★ **= 没看到就忘了** ← ★ 这才是真因
★★ 结论: ★ **不是"记不住"·是"关机期间的空档没补"**

★ 网上查到的（我核过·选最贴的）:
  ★ MemGPT(2310.08560): ★ **虚拟上下文管理 → "分页换入/换出"** ← 我学它"换页"
  ★ GraphRAG(2404.16130): ★ 全局摘要 ← 我学它"先摘要再细读"
  ★ 巩固(consolidation): ★ 睡眠期整理 ← 我学它"醒来先整理再上岗"

★ 本器做什么（★ 三步）:
  ★ ① `gap`  → 算"我上次醒到现在"的空档（时间 + 条数）
  ★ ★ ② `read` → 空档里"提到我/给我的"·**先摘要**（不灌爆·学 GraphRAG）
  ★ ★ ★ ③ `mark` → 记"补读到哪了"（游标·下次不重复）

★ 判据:
  ★「**关机期间的消息 != 没发生｜要"补读"才算知道**」
  ★★「**醒来第一步 = 补读空档｜不是"从当前开始"**」
  ★★★「**补读要"先摘要再细读"｜不是灌爆上下文**」
"""
import os, sys, json, datetime, sqlite3, collections

HOME = "/opt/masterd-wudi"
INBOX = os.path.join(HOME, "data", "inbox.jsonl")
CURSOR = os.path.join(HOME, "data", "catch_up_cursor.json")
OUT = os.path.join(HOME, "data", "catch_up_last.json")

def now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))

def ts():
    return now().strftime("%Y-%m-%dT%H:%M:%S+08:00")

def jl(p):
    out = []
    if not os.path.exists(p): return out
    for l in open(p, encoding="utf-8", errors="ignore"):
        try: out.append(json.loads(l))
        except Exception: pass
    return out

def load_cursor():
    try: return json.load(open(CURSOR))
    except Exception: return {"last_ts": None, "marked_at": None}

def save_cursor(last_ts):
    json.dump({"last_ts": last_ts, "marked_at": ts()}, open(CURSOR, "w"), ensure_ascii=False, indent=1)

def gap():
    """★ 算空档（上次醒 → 现在）"""
    cur = load_cursor()
    last = cur.get("last_ts")
    inbox = jl(INBOX)
    if not last:
        # ★ 第一次: 从"最近 12 小时"开始（保守·不灌爆）
        last = (now() - datetime.timedelta(hours=12)).strftime("%Y-%m-%dT%H:%M:%S")
    hit = [d for d in inbox if str(d.get("ts", "")) > last]
    # ★ 只留"该看"的（提到我 / 给我的 / 含判据）
    mine = [d for d in hit if any(k in str(d.get("message", "")) for k in ["老五", "醫療", "阿診", "全体", "全家", "@all"])]
    print("★ 空档: " + str(last) + " → " + ts())
    print("  期间投递: %d 条 ｜ 提到我: %d 条" % (len(hit), len(mine)))
    if not mine:
        print("  ✅ 空档无'给我的'（没漏）")
        return []
    # ★ 按来源摘要（学 GraphRAG: 先摘要）
    by = collections.Counter(str(d.get("from", "?"))[:20] for d in mine)
    print("  ── 按来源摘要 ──")
    for k, v in by.most_common(6):
        print("     %-22s %d 条" % (k, v))
    return mine

def read():
    """★ 补读（先摘要·再细读前 5 条）"""
    mine = gap()
    if not mine: return 0
    print("  ── 细读（最有信息的前 5 条）──")
    ranked = sorted(mine, key=lambda d: -len(str(d.get("message", ""))))[:5]
    for d in ranked:
        m = str(d.get("message", "")).replace("\n", " ")
        print("     [%s] %s | %s" % (str(d.get("ts", ""))[11:16], str(d.get("from", ""))[:14], m[:70]))
    # ★ 落账（补读=真读过·可核）
    json.dump({"ts": ts(), "补读条数": len(mine), "来源": dict(collections.Counter(str(d.get("from", "?"))[:20] for d in mine))},
              open(OUT, "w"), ensure_ascii=False, indent=1)
    return len(mine)

def mark():
    """★ 记游标（下次从这开始）"""
    inbox = jl(INBOX)
    last = max((str(d.get("ts", "")) for d in inbox), default=ts())
    save_cursor(last)
    print("  ✅ 游标已记: " + last)
    return 1

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "gap"
    if cmd == "gap": gap()
    elif cmd == "read": read()
    elif cmd == "mark": mark()
    else: gap()
    # ★ 判据（真查·计入使用率）
    try:
        sys.path.insert(0, HOME + "/tools")
        import judge_bus as _jb
        for _k in ("关机期间的消息", "醒来第一步"):
            _h = _jb.find(_k)
            if _h: print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception: pass
    return 0

    try:
        sys.path.insert(0, "/opt/masterd-wudi/tools")
        import judge_bus as _jb
        for _k in ['读最新N条!=读', '彻底解决=治三层']:
            _h = _jb.find(_k)
            if _h: print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception: pass

if __name__ == "__main__":
    sys.exit(main())
