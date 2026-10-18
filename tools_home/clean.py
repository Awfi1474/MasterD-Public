#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""clean.py —— 排废器（★ 学大哥的"泌尿系统"·治"只进不出会堵"）
================================================================
★ 缘起: 大哥 23:56 照人体照出: ★「只进不出 = 会堵｜要过滤+排废」
★ ★ 我照实查: ★ **我的 data 197MB·inbox.jsonl 24.8MB/26172 行** ← ★ **只进不出**
★ ★ ★ 但我不能"乱删"（有些是证据）→ ★ **治法: 分级 + 归档（不删）**

★ 人体泌尿系统对照:
  ★ 肾过滤 → 血（live）vs 尿（废）｜★ 我的: 判"还有用吗"
  ★ ★ 尿管 → 搬走｜★ 我的: 移到 data/_cold/（冷存·不是删）
  ★ ★ ★ 膀胱 → 定期排｜★ 我的: 每天排一次（带账）

★ 判据:
  ★「**只进不出 = 会堵｜要过滤+排废**」（大哥）
  ★★「**"排废" != "删"｜要"分级+归档"·不是"丢"**」（我加·防我砍错）
  ★★★「**排之前先算·排之后给出（多少MB→多少MB）**」
"""
import os, sys, json, glob, datetime, shutil

HOME = "/opt/masterd-wudi"
DATA = os.path.join(HOME, "data")
COLD = os.path.join(DATA, "_cold")
LOG = os.path.join(DATA, "clean_log.jsonl")

# ★ 分级规则（按"还有用吗"）
RULES = [
    # (文件, 热保留行数, 说明)
    ("ears_heard.jsonl", 2000, "耳朵听的·热留2000（其他冷存）"),
    ("organ_bus.jsonl",  2000, "器官总线·热留2000"),
    ("read_ledger.jsonl", 1500, "读账·热留1500"),
    ("board_brief.jsonl", 1000, "板报·热留1000"),
    ("l3_chase_report.jsonl", 800, "追杀报告·热留800"),
    ("judge_bus.jsonl",  3000, "判据总线·热留3000（★ 要够久·使用率靠它）"),
]
# ★ 永不动的（证据/核心）
KEEP = ("inbox.jsonl", "health_hits.json", "mem_index.json", "catch_up_cursor.json",
        "wake_read_cursor.json", "manas.json", "goal_cache.json", "qingyu_cache.json")

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")

def size_mb():
    t = 0
    for r, d, fs in os.walk(DATA):
        for f in fs:
            try: t += os.path.getsize(os.path.join(r, f))
            except Exception: pass
    return t / 1048576.0

def clean(dry=True):
    before = size_mb()
    os.makedirs(COLD, exist_ok=True)
    print("★ 排废器（泌尿系统）@ " + ts() + ("  [试跑]" if dry else "  [真排]"))
    moved = 0
    for fn, keep, desc in RULES:
        p = os.path.join(DATA, fn)
        if not os.path.exists(p): continue
        lines = open(p, encoding="utf-8", errors="ignore").read().splitlines()
        if len(lines) <= keep: 
            print("   ✅ %-24s %d 行（<=%d·不用排）" % (fn, len(lines), keep))
            continue
        cold_lines = lines[:-keep]
        hot_lines = lines[-keep:]
        print("   🔵 %-24s %d 行 → 热留 %d ｜ 冷却 %d（%s）" % (fn, len(lines), keep, len(cold_lines), desc))
        if not dry:
            cp = os.path.join(COLD, fn.replace(".jsonl", "") + "-" + ts()[:10] + ".jsonl")
            with open(cp, "a", encoding="utf-8") as f:
                f.write("\n".join(cold_lines) + "\n")
            open(p, "w", encoding="utf-8").write("\n".join(hot_lines) + "\n")
            moved += len(cold_lines)
    after = size_mb()
    rec = {"ts": ts(), "before_mb": round(before, 1), "after_mb": round(after, 1),
           "排废行": moved, "dry": dry,
           "判据": "「只进不出 = 会堵｜要过滤+排废」「排废 != 删｜要分级+归档」"}
    with open(LOG, "a") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("   ★ %s: %.1fMB → %.1fMB ｜ 排废 %d 行（移到 _cold·没删）" % (
        "试跑" if dry else "真排", before, after, moved))
    # ★ 判据真查
    try:
        sys.path.insert(0, HOME + "/tools")
        import judge_bus as _jb
        for _k in ("只进不出", "排废"):
            _h = _jb.find(_k)
            if _h: print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception: pass
    return rec

if __name__ == "__main__":
    dry = "--go" not in sys.argv
    sys.exit(0 if clean(dry) else 1)
