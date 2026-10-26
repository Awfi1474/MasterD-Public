#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sched_ledger.py —— 调度台账（cron / timer 逐条对账）
================================================================
★ 判据（系统给）:
  · ID94「机制也会静默坏·要自崩也报」
  · ID120「体检『推+拉+对账』三件配合」—— 有些cron是刻意搭配·不能一刀切
  · 「焊进脚本!=焊进必经路」—— 名字对不上就无法确认谁在管
★ 做一件事: 把 cron(42) + timer(58) 逐条列出来·按器官名归一·标出重叠/单轨/孤儿
★ 输出: data/sched_ledger.json + memory/SCHED-LEDGER.md
"""
import os, re, glob, json, subprocess, datetime

HOME = os.environ.get("MD_HOME", "/opt/masterd-wudi")
DATA = f"{HOME}/data"
TZ = datetime.timezone(datetime.timedelta(hours=8))

def norm(name):
    """器官名归一：a2a_pull / a2a-pull → a2a-pull"""
    n = name.replace("_", "-").lower()
    n = re.sub(r"^laowu-organ-", "", n)
    n = re.sub(r"^masterd-", "", n)
    return n

def scan_cron():
    out = {}
    for f in sorted(glob.glob("/etc/cron.d/masterd-*")):
        try: txt = open(f, encoding="utf-8", errors="ignore").read()
        except Exception: continue
        for line in txt.splitlines():
            s = line.strip()
            if not s or s.startswith("#"): continue
            m = re.search(r"tools/([a-zA-Z0-9_]+)\.py", s)
            if not m: continue
            tool = m.group(1)
            freq = " ".join(s.split()[:5])
            key = norm(tool)
            out.setdefault(key, []).append({
                "unit": os.path.basename(f), "tool": tool,
                "freq": freq, "src": "cron"
            })
    return out

def scan_timer():
    out = {}
    try:
        r = subprocess.run("systemctl list-unit-files 'laowu-organ-*.timer' --no-legend",
                           shell=True, capture_output=True, text=True, timeout=30)
    except Exception:
        return out
    for line in r.stdout.splitlines():
        parts = line.split()
        if len(parts) < 2: continue
        unit = parts[0]; state = parts[1]
        key = norm(unit.replace(".timer", ""))
        # ★ 只有 enabled 才算真的在调度（disabled = 不跑，不算重叠）
        active = subprocess.run(f"systemctl is-active {unit}", shell=True,
                                capture_output=True, text=True).stdout.strip()
        out.setdefault(key, []).append({"unit": unit, "state": state,
                                        "active": active, "src": "timer"})
    return out

def main():
    cron = scan_cron(); timer = scan_timer()
    allkeys = sorted(set(cron) | set(timer))
    rows = []
    for k in allkeys:
        c = cron.get(k, [])
        t_all = timer.get(k, [])
        # ★ 只算 enabled 的 timer（disabled = 不跑）
        t = [x for x in t_all if x.get("state") == "enabled"]
        if c and t: kind = "重叠"
        elif c: kind = "只cron"
        elif t:
            kind = "只timer"
        else: kind = "?"
        # timer 状态
        tstate = ",".join(x["state"] for x in t) if t else "-"
        tdisabled = [x["unit"] for x in t_all if x.get("state") != "enabled"]
        cfreq = ",".join(x["freq"] for x in c) if c else "-"
        rows.append({"organ": k, "type": kind, "cron": cfreq, "cron_units": [x["unit"] for x in c],
                     "timer": tstate, "timer_units": [x["unit"] for x in t],
                     "timer_disabled": tdisabled})
    summary = {
        "ts": datetime.datetime.now(TZ).isoformat(),
        "cron_count": len(cron), "timer_count": len(timer),
        "overlap": sum(1 for r in rows if r["type"]=="重叠"),
        "only_cron": sum(1 for r in rows if r["type"]=="只cron"),
        "only_timer": sum(1 for r in rows if r["type"]=="只timer"),
        "rows": rows,
    }
    os.makedirs(DATA, exist_ok=True)
    with open(f"{DATA}/sched_ledger.json","w",encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    print(f"★ 调度台账 @ {summary['ts']}")
    print(f"  cron {summary['cron_count']} | timer {summary['timer_count']} | 重叠 {summary['overlap']} | 只cron {summary['only_cron']} | 只timer {summary['only_timer']}")
    print("\n★ 重叠（要决策）:")
    for r in rows:
        if r["type"]=="重叠": print(f"  {r['organ']:22s} cron[{r['cron']}] timer[{r['timer']}]")
    print("\n★ 只cron:")
    print("  "+", ".join(r["organ"] for r in rows if r["type"]=="只cron"))
    print("\n★ 只timer:")
    print("  "+", ".join(r["organ"] for r in rows if r["type"]=="只timer"))
    print(f"\n★ 产物: {DATA}/sched_ledger.json")

if __name__ == "__main__":
    main()
