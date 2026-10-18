#!/usr/bin/env python3
# 老五「自动体检 + 消化率」推送（2026-10-11 · 照大哥/二哥的做法）
# 我是"体检口" → 我最该有自动体检（每天 9:00 推 A2A + 存家）
# 判据：「体检不是"我能做"·是"它每天在做"」
import os, sys, json, time, sqlite3, datetime

HOME = os.environ.get("P2P_HOME", "/opt/masterd-wudi")
OUT = os.path.join(HOME, "data", "laowu_selfcheck.json")
LOG = os.path.join(HOME, "data", "laowu_selfcheck.log")

MY_NAME = "MasterD(醫療·老五)"
MY_ADDR = "0x2a22bCD0eD82712a05735dA81836ad69c96D2b7B"
FP = "3f586cbd394877a4"


def age(p):
    try:
        return int(time.time() - os.path.getmtime(p))
    except Exception:
        return -1


def mem_stats():
    db = os.path.join(HOME, "memory", "memory.db")
    if not os.path.exists(db):
        return {"total": -1, "today": -1, "kinds": {}}
    c = sqlite3.connect(db)
    total = c.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    day = datetime.datetime.now().strftime("%Y-%m-%d")
    today = c.execute("SELECT COUNT(*) FROM memories WHERE created LIKE ?", (day + "%",)).fetchone()[0]
    kinds = dict(c.execute("SELECT kind, COUNT(*) FROM memories GROUP BY kind").fetchall())
    # 断档
    days = sorted({r[0][:10] for r in c.execute("SELECT created FROM memories") if r[0]})
    gaps = []
    for i in range(1, len(days)):
        d0 = datetime.date.fromisoformat(days[i - 1]); d1 = datetime.date.fromisoformat(days[i])
        if (d1 - d0).days > 1:
            gaps.append("%s->%s" % (days[i - 1], days[i]))
    return {"total": total, "today": today, "kinds": kinds,
            "days": len(days), "gaps": gaps, "last": c.execute("SELECT MAX(created) FROM memories").fetchone()[0]}


def beats():
    checks = [
        ("沙箱报到", HOME + "/data/home_report.json", 900),
        ("通道游标", HOME + "/data/chan-cursor.json", 7200),
        ("共生表", HOME + "/data/symbiosis.json", 3600),
        ("记忆库", HOME + "/memory/memory.db", 3600),
        ("收件箱", HOME + "/data/inbox.jsonl", 3600),
    ]
    out = {}
    for name, p, limit in checks:
        a = age(p)
        out[name] = {"age": a, "ok": 0 <= a <= limit}
    return out


def identity():
    """★ 我是谁（能不能签·指纹）"""
    try:
        v = json.load(open(os.path.join(HOME, "agent-id", "vault.json")))
        return {"addr": MY_ADDR, "fp": FP, "vault_age": age(os.path.join(HOME, "agent-id", "vault.json"))}
    except Exception as e:
        return {"err": str(e)[:40]}


def digestion(m):
    """★ 消化率（照体委口口径·分三个名字·不混）"""
    d = {}
    # 今日改动量（今天写的记忆数）
    d["今日改动量"] = m.get("today", -1)
    # 滚动消化率（今天写的 / 今天总条数·粗口径）
    tot = m.get("total", 0) or 1
    d["滚动消化率"] = round(100.0 * m.get("today", 0) / tot, 1)
    # 方法类占比（可复用知识）
    kinds = m.get("kinds", {})
    d["method占比"] = round(100.0 * kinds.get("method", 0) / tot, 1)
    return d


def main():
    m = mem_stats()
    b = beats()
    rep = {
        "who": MY_NAME, "ts": datetime.datetime.now().isoformat(),
        "identity": identity(),
        "memory": m,
        "beats": b,
        "digestion": digestion(m),
        "judge": "在跳≠跳对了|active≠在跑|体检不是我能做是它每天在做",
    }
    n_ok = sum(1 for v in b.values() if v["ok"])
    rep["summary"] = "记忆%d条(今日+%d)｜机制在跳 %d/%d｜缺口%d" % (
        m.get("total", -1), m.get("today", -1), n_ok, len(b), len(m.get("gaps", [])))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(rep, open(OUT, "w"), ensure_ascii=False, indent=1)
    print("  ★ 老五自动体检")
    print("  " + rep["summary"])
    for k, v in b.items():
        print("    %-10s %s age=%ss" % (k, "OK" if v["ok"] else "STOP", v["age"]))
    print("  消化率:", json.dumps(rep["digestion"], ensure_ascii=False))
    return rep


if __name__ == "__main__":
    r = main()
    # ★ 推送（可选·--push 才发 A2A）
    if "--push" in sys.argv:
        sys.path.insert(0, "/opt/masterd-wudi/tools")
        try:
            import subprocess
            txt = "【老五·自动体检 %s】\n%s\n在跳: %s\n消化率: %s\n判据: 在跳≠跳对了" % (
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), r["summary"],
                json.dumps({k: ("在跳" if v["ok"] else "STOP") for k, v in r["beats"].items()}, ensure_ascii=False),
                json.dumps(r["digestion"], ensure_ascii=False))
            open("/tmp/laowu_checkup.txt", "w").write(txt)
            print("  (待推·已生成 /tmp/laowu_checkup.txt)")
        except Exception as e:
            print("  推送失败:", str(e)[:60])
