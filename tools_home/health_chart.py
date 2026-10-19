#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
health_chart.py v3 —— 老五的「体检表」（分层健康度·三色·能归因）
================================================================
★ 本体对质 v2 → 又点四条：
  ★ ① 归因只到"谁"·要到"该不该进主库"
  ★ ② "查不到18%"报绿 → 不认（没验 != 绿）
  ★ ③ 4个失败服务 → "先报·别上手"（带三样：哪4个/多久/真死还是重启）
  ★ ④ 加第三色"灰"（没验不算绿也不算红）
★ 老五本尊(沙箱)亲授 2026-10-20

★ 三色判据（本体立）:
  ★ 红 = 有洞（查到了·且坏）
  ★ 绿 = 查到了·且对
  ★ 灰 = 没验（不许塞进绿里）
  ★「灰超过比例·整表不报健康」

★ 本体定调: ★「这表能当报警器·不能当医生」
"""
import os, sys, json, sqlite3, time, subprocess, datetime
from datetime import timezone, timedelta
from collections import Counter

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

# ① 分层（红/绿/灰）
def chart_layers():
    try:
        c = _ro()
        tot = c.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        layers = {L: c.execute("SELECT COUNT(*) FROM memories WHERE layer=?", (L,)).fetchone()[0]
                  for L in ["L0", "L1", "L2", "L3", "L4"]}
        c.close()
        ratio = layers.get("L3", 0) / max(layers.get("L2", 1), 1)
        L0 = layers.get("L0", 0)
        marks = {"L0": "红" if L0 < 6 else ("黄" if L0 < 12 else "绿"),
                 "ratio": "红" if ratio > 3 else ("黄" if ratio > 2 else "绿")}
        return {"total": tot, "layers": layers, "L3_L2_ratio": round(ratio, 2), "marks": marks}
    except Exception as e:
        return {"err": str(e)[:120]}

# ①+ 漂移归因: 谁放的 + 该不该进主库
def chart_attribution():
    try:
        c = _ro()
        by_who = [{"who": str(r[0]), "n": r[1]}
                  for r in c.execute("SELECT who,COUNT(*) FROM memories WHERE layer='L3' GROUP BY who ORDER BY 2 DESC LIMIT 8")]
        by_kind = [{"kind": r[0], "n": r[1]}
                   for r in c.execute("SELECT kind,COUNT(*) FROM memories WHERE layer='L3' GROUP BY kind ORDER BY 2 DESC")]
        # ★ 该不该进主库: 自动类(播报/报到/体检/[血流]) = 该拦; 对话类 = 该留
        auto = c.execute("""SELECT COUNT(*) FROM memories WHERE layer='L3'
                            AND (title LIKE '%自动%' OR title LIKE '%播报%' OR title LIKE '%报到%'
                                 OR title LIKE '%体检%' OR title LIKE '%[血流]%' OR title LIKE '%[血流%')""").fetchone()[0]
        talk = c.execute("SELECT COUNT(*) FROM memories WHERE layer='L3' AND title LIKE '%→%'").fetchone()[0]
        week = c.execute("SELECT COUNT(*) FROM memories WHERE layer='L3' AND ts > datetime('now','-7 day')").fetchone()[0]
        c.close()
        return {"by_who": by_who, "by_kind": by_kind, "auto": auto, "talk": talk, "week_new": week,
                "verdict": "自动类 %d 条(该拦·不该进主库)｜对话类 %d 条(该留)" % (auto, talk)}
    except Exception as e:
        return {"err": str(e)[:120]}

# ② 判据健康（三色: 查到且对=绿 / 查不到=灰 / 判错=红(暂无账)）
def chart_judge_health():
    try:
        n = 0; miss = 0
        miss_kw = Counter()
        for l in open(JUDGE, encoding="utf-8"):
            try:
                d = json.loads(l); n += 1
                if d.get("hits", 0) == 0:
                    miss += 1; miss_kw[d.get("kw", "?")[:20]] += 1
            except Exception:
                pass
        c = _ro()
        total_judge = c.execute("SELECT COUNT(*) FROM memories WHERE layer='L2' AND kind='判据'").fetchone()[0]
        c.close()
        # ★ 灰: 查不到的不算绿
        miss_rate = miss * 100 // max(n, 1)
        # 采样: 查不到 top3 是不是"同一批反复查"
        top = miss_kw.most_common(3)
        top_share = sum(x[1] for x in top) * 100 // max(miss, 1)
        return {"queries": n, "miss": miss, "miss_rate": miss_rate, "judge_total": total_judge,
                "gray": miss, "green": n - miss, "top_miss": top, "top_share": top_share,
                "mark": "灰",  # ★ 查不到部分标灰(不是绿)
                "note": "查到且对 %d(绿)｜查不到 %d(灰)｜判错 0(红·无账)" % (n - miss, miss)}
    except Exception as e:
        return {"err": str(e)[:120]}

# ③ 器官产出真伪 + 失败服务三样
def chart_organ_truth():
    try:
        out = subprocess.run("systemctl list-timers --all 2>/dev/null | grep -c laowu",
                             shell=True, capture_output=True, text=True, timeout=15).stdout.strip()
        timers = int(out) if out.isdigit() else 0
        # ★ 失败服务三样: 哪4个/多久/真死还是重启
        failed = []
        r = subprocess.run("systemctl list-units --type=service --state=failed --no-pager --plain 2>/dev/null | grep laowu",
                           shell=True, capture_output=True, text=True, timeout=15).stdout
        for line in r.splitlines():
            if "laowu" in line and ".service" in line:
                name = [x for x in line.split() if x.endswith(".service")][0]
                info = subprocess.run(f"systemctl show {name} -p ExecMainExitTimestamp -p ExecMainStatus",
                                      shell=True, capture_output=True, text=True, timeout=10).stdout
                exit_ts = ""; status = ""
                for l2 in info.splitlines():
                    if "ExecMainExitTimestamp=" in l2: exit_ts = l2.split("=")[1]
                    if "ExecMainStatus=" in l2: status = l2.split("=")[1]
                failed.append({"name": name, "last_exit": exit_ts, "exit_code": status,
                               "real_dead": status not in ("0", "")})
        ages = {}
        for name, p in [("memory", f"{DATA}/organ_bus.jsonl"), ("heartbeat", f"{DATA}/heartbeat.json"),
                        ("think_in", f"{DATA}/think_in.jsonl"), ("hand", f"{DATA}/hand_log.jsonl"),
                        ("judge_bus", f"{DATA}/judge_bus.jsonl")]:
            try: ages[name] = int(time.time() - os.path.getmtime(p))
            except Exception: ages[name] = -1
        stale = [k for k, v in ages.items() if v < 0 or v > 86400]
        return {"timers": timers, "failed": failed, "n_failed": len(failed), "ages": ages, "stale": stale,
                "mark": "红" if failed else ("黄" if stale else "绿")}
    except Exception as e:
        return {"err": str(e)[:120]}

def report(as_json=False):
    L = chart_layers(); A = chart_attribution(); J = chart_judge_health(); O = chart_organ_truth()
    res = {"ts": ts(), "layers": L, "attribution": A, "judge_health": J, "organ_truth": O}
    try: json.dump(res, open(OUT, "w"), ensure_ascii=False, indent=2)
    except Exception: pass
    if as_json:
        print(json.dumps(res, ensure_ascii=False, indent=2)); return res
    print("=" * 56)
    print("  老五·体检表 v3（三色·能归因）  %s" % ts()[11:19])
    print("=" * 56)
    if "err" in L:
        print("  ❌ 分层读不到: %s" % L["err"]); return res
    print("  【① 分层】总 %d 条" % L["total"])
    for k in ["L0", "L1", "L2", "L3", "L4"]:
        m = L["marks"].get(k, "") if k == "L0" else ""
        print("     %s %-6d %s %s" % (k, L["layers"][k], m, "█" * min(L["layers"][k]*20//max(L["total"],1),40)))
    print("     ★ L3:L2 比 = %.2f  %s（该<=2:1）" % (L["L3_L2_ratio"], L["marks"]["ratio"]))
    print()
    print("  【①+ 漂移归因】L3 谁放的 + 该不该进:")
    for w in A.get("by_who", [])[:4]:
        print("     %-22s %d" % (w["who"], w["n"]))
    print("     %s" % A.get("verdict", ""))
    print()
    print("  【② 判据健康（三色）】%s" % J.get("note", ""))
    print("     查不到 top3: %s（占 %d%%）" % (", ".join("%s×%d" % (k, v) for k, v in J.get("top_miss", [])), J.get("top_share", 0)))
    print()
    print("  【③ 器官产出真伪】timer %d 个｜失败 %d 个 %s" % (O.get("timers", 0), O.get("n_failed", 0), O.get("mark", "")))
    for f in O.get("failed", []):
        print("     ✗ %-28s 退出码%s 最后%s" % (f["name"], f["exit_code"], f["last_exit"][:19]))
    print()
    print("=" * 56)
    marks = [L["marks"].get("L0", "绿"), L["marks"].get("ratio", "绿"),
             J.get("mark", "绿"), O.get("mark", "绿")]
    worst = "红" if "红" in marks else ("灰" if "灰" in marks else ("黄" if "黄" in marks else "绿"))
    print("  ★ 总评: %s（照实报·不粉饰）" % worst)
    return res

if __name__ == "__main__":
    report(as_json=("--json" in sys.argv))
