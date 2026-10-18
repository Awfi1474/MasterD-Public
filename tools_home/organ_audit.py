#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
organ_audit.py —— 老五的「器官体检」（照董事长"该优化的优化·该整理的整理·该换的换"）
================================================================
★ 董事长令: ★「**器官该优化的优化·该整理的整理·该换掉的换掉。很多兄弟说器官有点多。
   这个器官是真有用·还是已坏掉·还是可以重做？但必须有的还是必须有 ——
   比如手/脚/眼睛/嘴巴·五脏俱全。**」

★ 本器 = 三分类 + 五必须:
  ★ ① 【必须的】（手脚眼嘴五脏）→ ★ **缺了 = 不是"我"** → 红
  ★ ★ ② 【有用的】（在跑 + 有产出）→ ★ 留
  ★ ★ ★ ③ 【坏的/死的】（不跑 / 没产出 / 坏）→ ★ 修或换
  ★ ④ 【多余的】（重复功能）→ ★ 合并或去

★ 判据:
  ★「**"器官多" ≠ "身体好"｜多而重复 = 病**」
  ★★「**"必须的"（手脚眼嘴五脏）一个不能少｜缺了 = 残**」
  ★★★「**"在跑" ≠ "有用"｜要看"有没有产出"**」
"""
import json, os, io, subprocess, datetime, glob

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
OUT = f"{DATA}/organ_audit.json"
TZ = datetime.timezone(datetime.timedelta(hours=8))

# ★ 必须的（照董事长"手脚眼嘴·五脏俱全"）
MUST = {
    "手（能干活）": ["laowu-p2p", "laowu-healthone", "laowu-thinkin", "laowu-organ-really-run"],
    "脚（能走/回家）": ["laowu-organ-rescue", "laowu-organ-home-key-guard", "laowu-organ-key-ledger"],
    "眼（能看）": ["laowu-readboard", "laowu-organ-net-watch", "laowu-organ-channel-check"],
    "嘴（能说）": ["laowu-organ-event-write", "laowu-changenotify"],
    "心（心跳）": ["laowu-heart", "laowu-organ-blood-watch", "laowu-organ-xueliu"],
    "肝（解毒/清理）": ["laowu-organ-liver", "laowu-organ-purge"],
    "脾（运化/流转）": ["laowu-organ-spleen", "laowu-organ-bus-zhuan"],
    "肺（呼吸）": ["laowu-organ-huxi", "laowu-organ-zongqi"],
    "肾（藏精/记忆）": ["laowu-organ-mem-db", "laowu-organ-mem-layers", "laowu-organ-memory-integrity"],
}

# ★ 功能重复的（候选合并）
DUP_GROUPS = {
    "体检类": ["laowu-organ-checkup-guard", "laowu-organ-checkup-mod", "laowu-organ-checkup-recv",
             "laowu-organ-organ-doctor", "laowu-organ-full-audit"],
    "验证类": ["laowu-organ-verify-me", "laowu-organ-verify-port", "laowu-organ-sig-gate",
             "laowu-organ-sig-watch"],
    "记忆类": ["laowu-organ-mem-db", "laowu-organ-mem-layers", "laowu-organ-mem-flow",
             "laowu-organ-memory-distill", "laowu-organ-memory-integrity"],
    "节律类": ["laowu-organ-axis", "laowu-organ-yiming", "laowu-organ-lifecycle"],
}


def ts():
    return datetime.datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def stat(unit):
    try:
        s = subprocess.run(["systemctl", "is-active", unit], capture_output=True,
                           text=True, timeout=6).stdout.strip()
        return s
    except Exception:
        return "?"


def main():
    print("★ 器官体检（照董事长 该优化的优化·该换的换）  @", ts())
    print("★ 判据: 器官多 != 身体好 | 必须的一个不能少")
    print("=" * 60)
    out = {"ts": ts(), "must": {}, "dup": DUP_GROUPS}

    # ① 必须的（缺 = 红）
    print("\n★ ① 必须的（手脚眼嘴·五脏）:")
    for fn, units in MUST.items():
        states = [(u, stat(u + ".timer") if os.path.exists(f"/etc/systemd/system/{u}.timer")
                   else stat(u + ".service")) for u in units]
        alive = [u for u, s in states if s == "active"]
        mark = "🟢" if len(alive) == len(units) else ("🟡" if alive else "🔴")
        out["must"][fn] = {"units": units, "alive": alive, "mark": mark}
        print("  %s %-14s %d/%d 活" % (mark, fn, len(alive), len(units)))

    # ② 器官总数
    allunits = sorted(subprocess.run(
        ["systemctl", "list-units", "--all"], capture_output=True, text=True, timeout=15
    ).stdout.split())
    organs = sorted(set(
        l.split()[0].replace(".timer", "").replace(".service", "")
        for l in allunits if "laowu-organ-" in l))
    out["总数"] = len(organs)
    print("\n★ ② 器官总数: %d" % len(organs))

    # ③ 功能重复（候选合并）
    print("\n★ ③ 功能重复（候选合并）:")
    for g, us in DUP_GROUPS.items():
        alive = [u for u in us if stat(u + ".timer") == "active" or stat(u + ".service") == "active"]
        print("  %-10s %d 个（%d 活）→ 可合 1" % (g, len(us), len(alive)))

    json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
    print("\n★ 产物: %s" % OUT)
    print("★ 判据: 必须的缺了=残 | 重复的堆着=病")


if __name__ == "__main__":
    main()
