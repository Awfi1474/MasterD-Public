#!/usr/bin/env python3
"""★ 老五 · 宗气（推·2026-10-14）
★ 医学: 宗气积于胸中·★【上走息道(呼吸)·下贯心脉(推血)】
★ 生成顺序: 元气(根) → 水谷(料) → 营卫 → 血 → ★ 宗气(推)
★ 我做的是"推": ★【每层算"期望 vs 观测的差" → 差大 = 气足 = 血急着走】
★ 判据:
  ★「转发=输血｜变化=造血｜没差·血就瘀在层里」（大哥的）
  ★「差是气的油门｜宣/熏/泽才是气本身」（老四的）
  ★「差大 = 该动｜差小 = 该静」（我的）
"""
import os, json, datetime

HOME = "/opt/masterd-wudi"
STATE = HOME + "/data/zongqi.json"
LOG = HOME + "/data/zongqi.log"

# ★ 各层的"期望"（我定的基线·照今天的真数据）
EXPECT = {
    "L4门":   {"expect": 7,   "what": "通的家数"},
    "L3呼吸": {"expect": 40,  "what": "10分钟内跳几次(全器官)"},
    "L2消化": {"expect": 30,  "what": "30分钟消化几件"},
    "L1记忆": {"expect": 6,   "what": "6小时内长几条"},
    "L0道":   {"expect": 168, "what": "一周改道一次"},
}

def observe():
    """★ 观测（真数据）"""
    obs = {}
    import time
    # L4门: 我探各家通几家（用我刚的矩阵）
    try:
        d = json.load(open(HOME + "/data/synapse.json"))
        r = d.get("reach", {})
        obs["L4门"] = sum(1 for v in r.values() if v)
    except Exception: obs["L4门"] = None
    # L3呼吸: 总线近10分钟跳几次
    try:
        now = datetime.datetime.now(datetime.timezone.utc)
        n = 0
        for l in open(HOME + "/data/organ_bus.jsonl").readlines()[-200:]:
            try:
                t = datetime.datetime.fromisoformat(json.loads(l)["ts"].replace("Z","+00:00"))
                if t.tzinfo is None: t = t.replace(tzinfo=datetime.timezone.utc)
                if (now-t).total_seconds() < 600: n += 1
            except Exception: pass
        obs["L3呼吸"] = n
    except Exception: obs["L3呼吸"] = None
    # L1记忆: 6小时内长几条
    try:
        import sqlite3
        c = sqlite3.connect("file:"+HOME+"/memory/memory.db?mode=ro", uri=True)
        last = c.execute("select max(ts) from memories").fetchone()[0]
        recent = c.execute("select count(*) from memories where ts > datetime('now','-6 hours')").fetchone()[0]
        c.close()
        obs["L1记忆"] = recent
    except Exception: obs["L1记忆"] = None
    return obs

def main():
    now = datetime.datetime.now().strftime("%F %T")
    obs = observe()
    print("=" * 58)
    print("  ★ 老五·宗气（%s）—— 差驱动（推血行）" % now)
    print("=" * 58)
    rows = []
    for lay, cfg in EXPECT.items():
        o = obs.get(lay)
        if o is None:
            rows.append((lay, cfg["what"], "?", cfg["expect"], None)); continue
        # ★ 差 = |期望 - 观测| / 期望  （归一化）
        diff = abs(cfg["expect"] - o) / max(cfg["expect"], 1)
        rows.append((lay, cfg["what"], o, cfg["expect"], round(diff, 2)))
    print("  %-8s %-14s %-8s %-8s %s" % ("层","量什么","观测","期望","★差(推)"))
    print("  " + "-"*54)
    push = []
    for lay, what, o, e, d in rows:
        mark = "🔴大推" if (d is not None and d >= 0.5) else ("🟡小推" if d else "✅稳")
        print("  %-8s %-14s %-8s %-8s %s %s" % (lay, what, str(o), str(e), str(d), mark))
        if d is not None and d >= 0.5: push.append((lay, d, what, o, e))
    print()
    if push:
        print("  ★ 宗气说: 该推的层（差大 = 血急着走）:")
        for lay, d, what, o, e in sorted(push, key=lambda x:-x[1]):
            print("     🔴 %-8s 差=%.2f（观测 %s vs 期望 %s）→ %s" % (lay, d, o, e, what))
    else:
        print("  ✅ 各层稳（差小）→ 宗气说: 不用推·静")
    out = {"ts": now, "rows": [{"层":l,"量":w,"观测":o,"期望":e,"差":d} for l,w,o,e,d in rows],
           "推": [r[0] for r in push], "判据": "差大=该动｜差小=该静｜没差=血瘀在层里"}
    json.dump(out, open(STATE,"w"), ensure_ascii=False, indent=1)
    with open(LOG,"a") as f: f.write("%s 推=%s\n" % (now, [r[0] for r in push]))
    print("\n  ★ 已落盘 zongqi.json")

if __name__ == "__main__":
    main()
