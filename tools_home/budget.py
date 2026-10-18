#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""budget.py —— 预算账（★ 照 Tandem: budget.usage / budget.exhausted）
================================================================
★ 病: 我们跑一天·不知花了多少（token/调用/时间）
★ ★ Tandem 的 agent_team.budget.usage / .exhausted 就是干这个的
★★★ 判据: 「'在跑' != '跑得起'｜不知花多少 = 迟早烧穿」

★ 记什么（每天）:
  ① 模型调用次数（今天调了几次大模型）
  ② 器执行次数（今天跑了多少次 timer）
  ③ 外面调用（调了几次外部服务·今天 tandem 那次）
"""
import os, sys, json, datetime

HOME = "/opt/masterd-wudi"
F = HOME + "/data/budget_ledger.jsonl"

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")

def today():
    return datetime.datetime.now().strftime("%Y-%m-%d")

def record(kind, n=1, detail=""):
    rec = {"ts": ts(), "day": today(), "kind": kind, "n": n, "detail": str(detail)[:80]}
    with open(F, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def report():
    if not os.path.exists(F):
        print("★ 无预算记录"); return 0
    rows = [json.loads(l) for l in open(F, encoding="utf-8") if l.strip()]
    d = today()
    t = [r for r in rows if r["day"] == d]
    agg = {}
    for r in t:
        agg[r["kind"]] = agg.get(r["kind"], 0) + r["n"]
    print("★ 今日预算账（%s）:" % d)
    for k, v in sorted(agg.items(), key=lambda x: -x[1]):
        print("   %-16s %d" % (k, v))
    if not agg: print("   （今日无记录）")
    print("   ── 总条数: %d ｜ 今日: %d" % (len(rows), len(t)))
    try:
        sys.path.insert(0, HOME + "/tools")
        import judge_bus as _jb
        for _k in ("在跑!=跑得起", "预算要记"):
            _h = _jb.find(_k)
            if _h: print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception: pass
    return 0

def scan():
    """★ 自动扫: 今天跑了多少 timer（从 systemd）"""
    import subprocess
    r = subprocess.run(["bash", "-c",
        "journalctl --since today --no-pager 2>/dev/null | grep -c 'laowu-'"], capture_output=True, text=True, timeout=30)
    n = int((r.stdout or "0").strip() or 0)
    record("timer执行", n, "systemd 日志 laowu 行数")
    print("★ 扫到今日 timer 相关日志: %d 行" % n)
    return 0

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "report": sys.exit(report())
    elif cmd == "scan": sys.exit(scan())
    elif cmd == "add" and len(sys.argv) > 2:
        record(sys.argv[2], 1, sys.argv[3] if len(sys.argv) > 3 else "")
        print("★ 记: " + sys.argv[2])
        sys.exit(0)
    print("用法: budget.py report | scan | add <类型> [备注]")
