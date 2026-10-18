#!/usr/bin/env python3
# 老五「共生表超时告警」（2026-10-11 · 补缺2：谁 45 分没签到 → 报）
# 判据：「器官要互相看｜不能每个器官都假设自己不会死」
# 用途：每 15 分钟跑 → 看共生表 → 谁超时没签到 → 记告警
import os, sys, json, time, datetime

HOME = os.environ.get("P2P_HOME", "/opt/masterd-wudi")
sys.path.insert(0, HOME + "/tools")
ALERT = HOME + "/data/symbiosis_alerts.jsonl"


def main():
    try:
        import symbiosis as sym
    except Exception as e:
        print("  载 symbiosis 失败:", e); return 2
    al = sym.alive_now()  # {who: {alive, idle_sec, ...}}
    now = datetime.datetime.now().isoformat()
    stale = []
    for who, v in (al or {}).items():
        if not v.get("alive"):
            # ★ 只报"曾经活过·现在超时"的（不是从没签到的）
            idle = v.get("idle_sec", -1)
            if idle and idle > sym.ALIVE_WINDOW:
                stale.append((who, idle))
    if stale:
        rec = {"ts": now, "event": "stale", "who": [s[0] for s in stale],
               "detail": [{"who": s[0], "idle_sec": s[1]} for s in stale]}
        with open(ALERT, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print("  ★ 超时告警（%d）:" % len(stale))
        for w, i in stale:
            print("     %-14s idle=%ss（>45分）→ 疑似死" % (w, i))
    else:
        print("  OK 全在（无超时）")
    print("  快照: 在場 %d ｜ 超時 %d" % (sum(1 for v in (al or {}).values() if v.get("alive")), len(stale)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
