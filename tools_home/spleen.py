#!/usr/bin/env python3
"""★ 老五 · 脾（仓廪之官·消化系统总调度）· 2026-10-13
★ 中医依据（《内经》）：「脾者·仓廪之官·主运化·统血」
★ 人体对应：胃（初步消化）→ 小肠（吸收）→ 大肠（提炼）→ ★ 脾（总调度）
★ 建它的理由（真病）：董事长问"人体有消化系统·你这有没有"——
  查出：① 脾 spleen.py 设计有·没实现 ② 没有"排出(肛门)"机制
  → 后果：动→落地只有 5.2%（听了一堆·认了一堆·落不了地）= 消化不良

★ 脾的三职（照《内经》+ 我们的实况）：
  ① 运化 —— 原料（耳朵/收件箱）→ 营养（记忆库）·推"胃"去消化
  ② 统血 —— 防"记了一堆垃圾"（记忆被稀释）·盯每条是否"真营养"
  ③ 升清降浊 —— ★ 清（判据/方法/身份）留下·★ 浊（噪音/回执/探活）排出
★ 判据：★「吸收=听→认→动→落地｜落地率低=消化不良」｜★「记垃圾=另一种病」
"""
import os, sys, json, sqlite3, datetime
sys.path.insert(0, "/opt/masterd-wudi/tools")
HOME = "/opt/masterd-wudi"
LOG = HOME + "/data/spleen.log"
STATE = HOME + "/data/spleen_state.json"

def log(l):
    with open(LOG, "a") as f:
        f.write("%s %s\n" % (datetime.datetime.now().strftime("%F %T"), l))

def main():
    import memory_db as m
    m.HOME = HOME; m.DB = HOME + "/memory/memory.db"; m.init()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    # ══ ① 运化：推胃去消化（沉淀候选 → 进库）══
    proposed = 0
    try:
        import memory_distill
        memory_distill.HOME = HOME
        memory_distill.propose()   # 胃：挑值得记的 → 候选池（等人/机制确认）
        import json as _j
        cand = _j.load(open(HOME+"/data/memory_candidates.json"))
        proposed = len(cand) if isinstance(cand, list) else len(cand.get("candidates", []))
    except Exception as e:
        log("运化失败 " + str(e)[:60])

    # ══ ② 统血：查"有没有记垃圾"（稀释检测）══
    n_all = 0; n_today = 0; kinds = {}
    try:
        c = sqlite3.connect("file:"+HOME+"/memory/memory.db?mode=ro", uri=True)
        n_all = c.execute("select count(*) from memories").fetchone()[0]
        n_today = c.execute("select count(*) from memories where ts like ?", (today+"%",)).fetchone()[0]
        for k, cnt in c.execute("select kind,count(*) from memories group by kind"):
            kinds[k] = cnt
        c.close()
    except Exception as e:
        log("统血读库失败 " + str(e)[:50])

    # ══ ③ 升清降浊：算吸收率 + 定"该排什么"══
    try:
        ab = json.load(open(HOME+"/data/digest_absorb.json"))
    except Exception:
        ab = {}
    heard = ab.get("听到(耳朵)", 0); landed = ab.get("落地(进库)", 0)
    rate = round(100.0*landed/heard, 1) if heard else 0.0

    # ★ 脾的判断
    judge = []
    if rate < 10:
        judge.append("🔴 消化不良：落地率 %.1f%%（<10%%）→ 听了没落" % rate)
    elif rate < 30:
        judge.append("🟡 消化偏弱：落地率 %.1f%%" % rate)
    else:
        judge.append("✅ 消化正常：落地率 %.1f%%" % rate)
    if kinds.get("event", 0) > (n_all * 0.5):
        judge.append("🟡 浊气偏重：event 占 %.0f%%（流水多·营养少）" % (100.0*kinds.get("event",0)/max(n_all,1)))
    # ★ 该排的（降浊）：探活/回执类噪音
    try:
        c = sqlite3.connect("file:"+HOME+"/memory/memory.db?mode=ro", uri=True)
        noise = c.execute("select count(*) from memories where title like '%探活%' or title like '%回执%' or body like '%PROBE%'").fetchone()[0]
        c.close()
    except Exception:
        noise = 0
    if noise > 0:
        judge.append("🟡 待排浊：%d 条（探活/回执类·建议降浊）" % noise)

    out = {"ts": now, "day": today, "官": "脾·仓廪之官",
           "运化": {"候选": proposed},
           "统血": {"库总": n_all, "今日入库": n_today, "分层": kinds},
           "升清降浊": {"落地率": rate, "待排浊": noise},
           "判断": judge,
           "判据": "★ 吸收=听→认→动→落地｜落地率低=消化不良｜记垃圾=另一种病"}
    json.dump(out, open(HOME+"/data/spleen.json","w"), ensure_ascii=False, indent=1)
    log("脾: 运化候选%d | 库%d(今+%d) | 落地率%.1f%% | %s" % (proposed, n_all, n_today, rate, " ".join(judge)))
    print("  ★ 脾·仓廪之官（%s）" % today)
    print("   【运化】候选 %d 条（胃挑的·等确认）" % proposed)
    print("   【统血】库 %d 条 · 今日入库 %d · 分层 %s" % (n_all, n_today, kinds))
    print("   【升清降浊】落地率 %.1f%% ｜ 待排浊 %d 条" % (rate, noise))
    for j in judge: print("   %s" % j)

if __name__ == "__main__":
    main()
