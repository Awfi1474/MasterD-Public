#!/usr/bin/env python3
# 老五「记忆分层」（2026-10-11 · 董事长点：做好自己的记忆分层）
# ★ 学 Arki/三哥的结构（L0-L4）· 用我自己的内容（不照抄）
# ★ 我的分层：
#   L0 魂/宪法  = 不可动（我是谁 · 铁律 · 道）        ← 改要"最严"
#   L1 身份     = 地址/钥匙/家（我的"我是谁"锚）        ← 改要"换钥三件"
#   L2 方法     = 可复用的判据/做法（被验证过）        ← 我的最大层
#   L3 事件/病例 = 流水（发生过的事·含血教训）         ← 只增不改
#   L4 基建     = 器官/端点/定时器（可重建的）         ← 可重写
# ★ 判据：「改的层越靠上·要求越严｜L0/L1 改要"公告+留痕"｜L4 可随便重建」
import os, sys, json, sqlite3, datetime

HOME = os.environ.get("P2P_HOME", "/opt/masterd-wudi")
DB = HOME + "/memory/memory.db"
OUT = HOME + "/data/memory_layers.json"

# ★ 我的分层定义（kind → layer）
LAYER_OF = {
    "identity": "L1",   # 身份（地址/钥匙）
    "method": "L2",     # 方法（可复用）
    "infra": "L4",      # 基建（器官/端点/定时器）
    "case": "L3",       # 事件/病例（流水）
    "event": "L3",      # 事件
}
LAYER_DESC = {
    "L0": "魂/宪法（我是谁·铁律·道）——不可动",
    "L1": "身份（地址/钥匙/家）——改要换钥三件",
    "L2": "方法（可复用判据）——被验证过才进",
    "L3": "事件/病例（流水·含血教训）——只增不改",
    "L4": "基建（器官/端点/定时器）——可重建",
}


def main():
    c = sqlite3.connect(DB)
    rows = c.execute("SELECT kind, COUNT(*) FROM memories GROUP BY kind").fetchall()
    stat = {}
    for k, n in rows:
        lay = LAYER_OF.get(k, "L3")
        stat[lay] = stat.get(lay, 0) + n
    # ★ L0 從魂檔案算（不在 db 裡）
    soul = HOME + "/memory/SOUL.md"
    role = HOME + "/memory/MEDICAL_ROLE.md"
    prof = HOME + "/memory/PROFESSION.md"
    l0 = sum(1 for p in [soul, role, prof] if os.path.exists(p))
    stat["L0"] = l0
    total = sum(stat.values())
    print("  ★ 老五·记忆分层（%s）" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("  总条数: %d" % total)
    print("  " + "-" * 50)
    for lay in ["L0", "L1", "L2", "L3", "L4"]:
        n = stat.get(lay, 0)
        bar = "*" * min(40, n // 3)
        print("   %s %-42s %3d  %s" % (lay, LAYER_DESC[lay], n, bar))
    # ★ 落档
    rep = {
        "ts": datetime.datetime.now().isoformat(),
        "total": total,
        "layers": LAYER_DESC,
        "stat": stat,
        "rule": "改的层越靠上·要求越严｜L0/L1 改要公告+留痕｜L4 可重建",
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(rep, open(OUT, "w"), ensure_ascii=False, indent=1)
    print("  " + "-" * 50)
    print("  ★ 判据：改的层越靠上·要求越严｜L0/L1 改要'公告+留痕'｜L4 可随便重建")
    return 0


if __name__ == "__main__":
    sys.exit(main())
