#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""clean_by_type.py —— 按"类型"排废（★ 泌尿系统强化·照人体"肾分区过滤"）
================================================================
★ 缘起: 照人体镜子 → ★ 我 165 器里"泌尿（排废）"只有 2 个·最弱
★ 人体肾: ★ **不是"全滤"·是"分区滤"**（肾小球滤血/肾小管重吸收）
★ 判据: ★「**排废要"按类型"·不是"按时间"｜有用的留·噪音的走**」
"""
import os, sys, json, glob, datetime, shutil, sqlite3

HOME = "/opt/masterd-wudi"
DATA = os.path.join(HOME, "data")
COLD = os.path.join(DATA, "_cold")

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")

def main():
    os.makedirs(COLD, exist_ok=True)
    print("★ 按类型排废 @ " + ts())
    # ★ 三类噪音（照人体"过滤分区"）
    TYPE = {
        "探活/心跳": ["talk.jsonl", "ears_heard.jsonl"],
        "巡检/报告": ["organ_bus.jsonl", "read_ledger.jsonl", "board_brief.jsonl"],
        "追杀/临时": ["l3_chase_report.jsonl", "hall_cache.json"],
    }
    moved = 0
    for kind, files in TYPE.items():
        for fn in files:
            p = os.path.join(DATA, fn)
            if not os.path.exists(p): continue
            sz = os.path.getsize(p) / 1048576.0
            if sz < 1.0:   # ★ 小于 1MB 不动
                continue
            print("   🔵 [%s] %s %.1fMB → 冷存" % (kind, fn, sz))
            cp = os.path.join(COLD, fn + "." + ts()[:10] + ".cold")
            try:
                shutil.copy2(p, cp)
                # ★ 保留最近 1000 行
                lines = open(p, encoding="utf-8", errors="ignore").read().splitlines()
                keep = lines[-1000:] if len(lines) > 1000 else lines
                open(p, "w", encoding="utf-8").write("\n".join(keep) + "\n")
                moved += 1
            except Exception as e:
                print("     ✗ " + str(e)[:40])
    print("   ★ 按类型排: %d 个文件（冷存在 _cold·没删）" % moved)
    try:
        sys.path.insert(0, HOME + "/tools")
        import judge_bus as _jb
        for _k in ("排废要按类型", "泌尿"):
            _h = _jb.find(_k)
            if _h: print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception: pass
    return 0

if __name__ == "__main__":
    sys.exit(main())
