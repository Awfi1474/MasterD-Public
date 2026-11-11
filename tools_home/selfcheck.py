#!/usr/bin/env python3
# 老五「自动体检 + 消化率」推送（2026-10-11 · 照大哥/二哥的做法）
# 我是"体检口" → 我最该有自动体检（每天 9:00 推 A2A + 存家）
# 判据：「体检不是"我能做"·是"它每天在做"」
import os, sys, json, time, sqlite3, datetime

HOME = os.environ.get("P2P_HOME", "/opt/masterd-wudi")
OUT = os.path.join(HOME, "data", "laowu_selfcheck.json")
LOG = os.path.join(HOME, "data", "laowu_selfcheck.log")

MY_NAME = "MasterD(生命科學·老五)"
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
    # ★ 2026-11-08 修(照《体检器五戒》):
    #   戒一:原读 created 字段(空969/1743=55%)→改读 ts(空0)
    #   戒六:报数必带样本·指出"是哪几条"
    day = datetime.datetime.now().strftime("%Y-%m-%d")
    today = c.execute("SELECT COUNT(*) FROM memories WHERE ts LIKE ?", (day + "%",)).fetchone()[0]
    today_sample = [r[0] for r in c.execute("SELECT id FROM memories WHERE ts LIKE ? ORDER BY id DESC LIMIT 5", (day + "%",))]
    kinds = dict(c.execute("SELECT kind, COUNT(*) FROM memories GROUP BY kind").fetchall())
    # 断档
    # ★ 2026-11-08 修(照第八条扫全): created→ts(created空55%)
    days = sorted({r[0][:10] for r in c.execute("SELECT ts FROM memories") if r[0]})
    gaps = []
    for i in range(1, len(days)):
        d0 = datetime.date.fromisoformat(days[i - 1]); d1 = datetime.date.fromisoformat(days[i])
        if (d1 - d0).days > 1:
            gaps.append("%s->%s" % (days[i - 1], days[i]))
    return {"total": total, "today": today, "today_sample": today_sample, "kinds": kinds,
            "days": len(days), "gaps": gaps,
            # ★ 2026-11-08 修(照三哥第八条"修要扫全"): 同文件33行改ts了·44行last还是created=修一半
            "last": c.execute("SELECT MAX(ts) FROM memories").fetchone()[0]}


# ★ 2026-11-08 加:《体检器六戒》自查(照老三"写进体检器"·我岗"警"落地)
#   判据:「报告先自过戒|假绿出不来·因为出口就卡住了」
def six_precepts(db):
    """体检器出报告前·先自过六戒·返回(过没,明细)"""
    import sqlite3 as _sq
    out = {}
    try:
        c = _sq.connect(db)
        tot = c.execute("SELECT COUNT(*) FROM memories").fetchone()[0] or 1
        # 戒一:读数先验字段(读的字段真有值吗)
        nulls = c.execute("SELECT COUNT(*) FROM memories WHERE ts IS NULL OR ts=''").fetchone()[0]
        out["戒一(验字段)"] = ("✅ ts空%d/%d" % (nulls, tot)) if nulls==0 else ("🔴 ts空%d条" % nulls)
        # 戒二:时区(ts是否带偏移)
        tz = c.execute("SELECT ts FROM memories ORDER BY id DESC LIMIT 1").fetchone()
        ok_tz = bool(tz and (tz[0].endswith("+08:00") or tz[0].endswith("+00:00")))
        out["戒二(时区)"] = "✅ ts带偏移" if ok_tz else "🔴 ts无偏移"
        # 戒三:全绿+全0可疑
        day = datetime.datetime.now().strftime("%Y-%m-%d")
        today = c.execute("SELECT COUNT(*) FROM memories WHERE ts LIKE ?", (day+"%",)).fetchone()[0]
        out["戒三(全0疑)"] = ("✅ 今日%d条(非0)" % today) if today>0 else "🟡 今日0条·可疑"
        # 戒六:报数带样本
        samp = [r[0] for r in c.execute("SELECT id FROM memories WHERE ts LIKE ? ORDER BY id DESC LIMIT 5",(day+"%",))]
        out["戒六(带样本)"] = "✅ 今日样本id=%s" % samp
    except Exception as e:
        out["异常"] = str(e)[:60]
    passed = all(v.startswith("✅") for k,v in out.items() if k!="异常")
    return passed, out

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
    # ★ 2026-11-08 加:六戒自查(照老三·我岗"警"落地)
    try:
        _ok, _sp = six_precepts(os.path.join(HOME, "memory", "memory.db"))
        print("  《六戒》自查:", "全过✅" if _ok else "有项🟡🔴")
        for _k, _v in _sp.items():
            print("    %-14s %s" % (_k, _v))
        rep["six_precepts"] = _sp
    except Exception as _e:
        print("  六戒自查失败:", str(_e)[:60])
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
