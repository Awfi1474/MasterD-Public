#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
health_chart.py v2 —— 老五的「体检表」（分层健康度·报红黄绿·能归因）
================================================================
★ 本体对质 → 认了 v1，但点三样缺：
  ★ ① 缺"漂移归因": 报了红·没说是哪批记录进来的、谁放进来
  ★ ② 缺"判据失效检测": 90%是"用过"·不是"用对了"
  ★ ③ 缺"器官产出真伪": 有产出 != 产出有效·timer 有没有空转
★ 老五本尊(沙箱)亲授 2026-10-20

★ 本体定调: ★「这表能当报警器·不能当医生｜红了往下查得靠手」
  → ★ v2 加"归因"·但还是报警器(给入口·不下结论)

★ 判据: 「分层是解剖 != 体检｜解剖说结构·体检说'哪在漂'」
"""
import os, sys, json, sqlite3, time, subprocess, datetime
from datetime import timezone, timedelta

HOME = "/opt/masterd-wudi"
DB = f"{HOME}/memory/memory.db"
DATA = f"{HOME}/data"
JUDGE = f"{DATA}/judge_bus.jsonl"
OUT = f"{DATA}/health_chart.json"
TZ = timezone(timedelta(hours=8))

def ts():
    return datetime.datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S+08:00")

def _ro():
    return sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=8)

# ① 分层
def chart_layers():
    try:
        c = _ro()
        tot = c.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        layers = {}
        for L in ["L0", "L1", "L2", "L3", "L4"]:
            layers[L] = c.execute("SELECT COUNT(*) FROM memories WHERE layer=?", (L,)).fetchone()[0]
        c.close()
        ratio = layers.get("L3", 0) / max(layers.get("L2", 1), 1)
        L0 = layers.get("L0", 0)
        marks = {"L0": "红" if L0 < 6 else ("黄" if L0 < 12 else "绿"),
                 "ratio": "红" if ratio > 3 else ("黄" if ratio > 2 else "绿")}
        return {"total": tot, "layers": layers, "L3_L2_ratio": round(ratio, 2),
                "L0_floor": L0, "marks": marks,
                "ok": marks["L0"] != "红" and marks["ratio"] != "红"}
    except Exception as e:
        return {"err": str(e)[:120], "ok": False}

# ★ ①+ 漂移归因: L3 是谁放进来的
def chart_attribution():
    try:
        c = _ro()
        # L3 按 who
        by_who = []
        for r in c.execute("SELECT who,COUNT(*) FROM memories WHERE layer='L3' GROUP BY who ORDER BY 2 DESC LIMIT 8"):
            by_who.append({"who": str(r[0]), "n": r[1]})
        # L3 按 kind
        by_kind = []
        for r in c.execute("SELECT kind,COUNT(*) FROM memories WHERE layer='L3' GROUP BY kind ORDER BY 2 DESC"):
            by_kind.append({"kind": r[0], "n": r[1]})
        # 最近7天进来的 L3
        week = c.execute("""SELECT COUNT(*) FROM memories WHERE layer='L3'
                            AND ts > datetime('now','-7 day')""").fetchone()[0]
        c.close()
        # 大头
        top = by_kind[0] if by_kind else {"kind": "?", "n": 0}
        return {"by_who": by_who, "by_kind": by_kind, "week_new": week,
                "top_entry": top, "note": "L3 大头是 %s（%d条）" % (top["kind"], top["n"])}
    except Exception as e:
        return {"err": str(e)[:120]}

# ★ ② 判据失效检测
def chart_judge_health():
    try:
        n = 0; miss = 0
        for l in open(JUDGE, encoding="utf-8"):
            try:
                d = json.loads(l); n += 1
                if d.get("hits", 0) == 0: miss += 1
            except Exception:
                pass
        c = _ro()
        total_judge = c.execute("SELECT COUNT(*) FROM memories WHERE layer='L2' AND kind='判据'").fetchone()[0]
        c.close()
        miss_rate = miss * 100 // max(n, 1)
        return {"queries": n, "miss": miss, "miss_rate": miss_rate,
                "judge_total": total_judge,
                "mark": "红" if miss_rate > 40 else ("黄" if miss_rate > 20 else "绿"),
                "note": "查不到率 %d%%（查不到=关键词对不上·不是判据失效）" % miss_rate}
    except Exception as e:
        return {"err": str(e)[:120]}

# ★ ③ 器官产出真伪
def chart_organ_truth():
    try:
        out = subprocess.run("systemctl list-timers --all 2>/dev/null | grep laowu",
                             shell=True, capture_output=True, text=True, timeout=15).stdout
        total = len([l for l in out.splitlines() if "laowu" in l])
        # 空转: timer 存在但对应 service 从没成功/最近失败
        failed = subprocess.run("systemctl list-units --type=service --state=failed 2>/dev/null | grep -c laowu",
                                shell=True, capture_output=True, text=True, timeout=15).stdout.strip()
        failed = int(failed) if failed.isdigit() else 0
        # 产出年龄
        ages = {}
        for name, p in [("memory", f"{DATA}/organ_bus.jsonl"),
                        ("heartbeat", f"{DATA}/heartbeat.json"),
                        ("think_in", f"{DATA}/think_in.jsonl"),
                        ("hand", f"{DATA}/hand_log.jsonl"),
                        ("judge_bus", f"{DATA}/judge_bus.jsonl")]:
            try:
                ages[name] = int(time.time() - os.path.getmtime(p))
            except Exception:
                ages[name] = -1
        stale = [k for k, v in ages.items() if v < 0 or v > 86400]
        return {"timers": total, "failed_services": failed, "ages": ages, "stale": stale,
                "mark": "红" if failed >= 3 or len(stale) >= 2 else ("黄" if failed or stale else "绿")}
    except Exception as e:
        return {"err": str(e)[:120]}

def chart_drift(cur):
    prev = None
    if os.path.exists(OUT):
        try: prev = json.load(open(OUT))
        except Exception: pass
    if not prev: return {"first": True}
    d = {}
    for L in ["L0", "L1", "L2", "L3", "L4"]:
        a = prev.get("layers", {}).get("layers", {}).get(L, 0)
        b = cur.get("layers", {}).get(L, 0)
        if a != b: d[L] = "%d→%d" % (a, b)
    return d

def report(as_json=False):
    L = chart_layers()
    A = chart_attribution()
    J = chart_judge_health()
    O = chart_organ_truth()
    drift = chart_drift(L)
    res = {"ts": ts(), "layers": L, "attribution": A, "judge_health": J,
           "organ_truth": O, "drift": drift}
    try: json.dump(res, open(OUT, "w"), ensure_ascii=False, indent=2)
    except Exception: pass
    if as_json:
        print(json.dumps(res, ensure_ascii=False, indent=2)); return res
    print("=" * 56)
    print("  老五·体检表 v2（分层健康度·能归因）  %s" % ts()[11:19])
    print("=" * 56)
    if "err" in L:
        print("  ❌ 分层读不到: %s" % L["err"]); return res
    print("  【① 分层】总 %d 条" % L["total"])
    for k in ["L0", "L1", "L2", "L3", "L4"]:
        m = L["marks"].get(k, "") if k == "L0" else ""
        print("     %s %-6d %s %s" % (k, L["layers"][k], m, "█" * min(L["layers"][k]*20//max(L["total"],1),40)))
    print("     ★ L3:L2 比 = %.2f  %s（该<=2:1）" % (L["L3_L2_ratio"], L["marks"]["ratio"]))
    print()
    print("  【①+ 漂移归因】L3 是谁放进来的:")
    for w in A.get("by_who", [])[:5]:
        print("     %-22s %d" % (w["who"], w["n"]))
    print("     最近7天新增: %d 条｜大头: %s" % (A.get("week_new", 0), A.get("note", "")))
    print()
    print("  【② 判据健康】%d 查询·查不到 %d(%d%%) %s" % (
        J.get("queries", 0), J.get("miss", 0), J.get("miss_rate", 0), J.get("mark", "")))
    print()
    print("  【③ 器官产出真伪】timer %d 个｜失败服务 %d %s" % (
        O.get("timers", 0), O.get("failed_services", 0), O.get("mark", "")))
    for k, v in O.get("ages", {}).items():
        print("     %-10s %s" % (k, ("%.1f小时前" % (v/3600)) if v >= 0 else "无产出"))
    print()
    if not drift.get("first") and drift:
        print("  【④ 漂移】%s" % json.dumps(drift, ensure_ascii=False))
    print("=" * 56)
    marks = [L["marks"].get("L0", "绿"), L["marks"].get("ratio", "绿"), J.get("mark", "绿"), O.get("mark", "绿")]
    worst = "红" if "红" in marks else ("黄" if "黄" in marks else "绿")
    print("  ★ 总评: %s（照实报·不粉饰）" % worst)
    return res

if __name__ == "__main__":
    report(as_json=("--json" in sys.argv))
