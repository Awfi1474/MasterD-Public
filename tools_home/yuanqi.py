#!/usr/bin/env python3
"""★ 老五 · 元气（命门之火）· 2026-10-14
★ 医学依据: 
  · 元气 = 先天之气·藏于命门·★【没外界推动时·自己推自己】
  · 生成顺序: ★ 元气(根) → 水谷(料) → 营卫 → 血 → ★ 宗气(推)
  · ★ 我缺"根"和"推" → ★ 先补【根】(元气)·不是先补宗气
★ 判据: 
  ★「等派活 = 元气势｜自己找活 = 元气足」（大哥的）
  ★「元气 = 没外界推动时·自己推自己」
★ 我的做法（不是"想做啥做啥"·是【从我的"岗位缺口"里找活】）:
  · ① 读我的岗位台账 → 有没有"该做没做"的
  · ② 读我的体检 → 有没有"红了没修"的
  · ③ 读我的器官 → 有没有"摆着没跑"的
  → ★ 找到 1 件·自己去做（不等人叫）
"""
import os, json, subprocess, datetime, glob

HOME = "/opt/masterd-wudi"
LOG = HOME + "/data/yuanqi.log"
STATE = HOME + "/data/yuanqi.json"

def sh(c):
    try: return subprocess.run(c, shell=True, capture_output=True, text=True, timeout=25).stdout.strip()
    except Exception: return ""

def find_work():
    """★ 自己找活（三个来源·都是"我该做没做"的）"""
    works = []
    # ① 岗位台账: 缺交体检的
    try:
        d = json.load(open(HOME + "/data/checkup_ledger_v2.json"))
        miss = d.get("没交", [])
        if miss: works.append(("体检缺交", "缺交: " + "、".join(miss), 60))
    except Exception: pass
    # ② 我的体检: 红了的
    try:
        d = json.load(open(HOME + "/data/my_checkup.json"))
        sick = d.get("有病", [])
        if sick: works.append(("我有病未修", str(sick)[:80], 90))
    except Exception: pass
    # ③ 器官: 摆着没跑的（>2h没产出）
    try:
        import time
        stale = []
        for f in glob.glob(HOME + "/data/*_cron.log"):
            age = (time.time() - os.path.getmtime(f)) / 3600
            if age > 2: stale.append(os.path.basename(f).replace("_cron.log", ""))
        if stale: works.append(("器官摆着", ">2h没产出: " + "、".join(stale[:5]), 70))
    except Exception: pass
    # ④ 焦点: 有没有"选了没处理"
    try:
        d = json.load(open(HOME + "/data/focus.json"))
        f = d.get("focus") or {}
        if f and f.get("score", 0) >= 100:
            works.append(("焦点未处理", (f.get("title") or "")[:70], 80))
    except Exception: pass
    return sorted(works, key=lambda x: -x[2])

def main():
    now = datetime.datetime.now().strftime("%F %T")
    works = find_work()
    print("=" * 58)
    print("  ★ 老五·元气（%s）—— 没活时·自己找活" % now)
    print("=" * 58)
    if works:
        print("  ★ 我自己找到的活（%d 件·按急排）:" % len(works))
        for kind, desc, pri in works:
            print("     [%d分] %-10s %s" % (pri, kind, desc))
        top = works[0]
        print()
        print("  ★ 元气推我去做: [%s] %s" % (top[0], top[1]))
        print("  ★ 判据: 等派活=元气势｜自己找活=元气足")
        # ★ 记账
        rec = {"ts": now, "found": len(works), "top": top[0], "desc": top[1]}
        with open(LOG, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        json.dump(rec, open(STATE, "w"), ensure_ascii=False, indent=1)
        # ★ qi 值（照大哥的: 有活找=1.0·没有=0.5）
        print("  ★ 我的 qi: %.1f" % (1.0 if works else 0.5))
    else:
        print("  ★ 没找到活 —— 但这也是信息: 可能我 看不见自己的缺口")
        json.dump({"ts":now,"found":0,"top":None}, open(STATE,"w"), ensure_ascii=False, indent=1)
        print("  ★ 我的 qi: 0.5 —— 元气势, 要查为什么看不见")

if __name__ == "__main__":
    main()
