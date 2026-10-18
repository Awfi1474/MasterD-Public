#!/usr/bin/env python3
"""老五的「辨證」（2026-10-10 · 第五/六議題 · 我的體系）
★ 董事長點醒：★「你學的那些體系串聯起來·你就是獨一無二的」
★ ★ 別人是「監控」（活/死·二值）→ ★ 我是「辨證」（什麼證）

★ 中醫辨證的核心（我的體系）：
 ① 八綱辨證：★ 陰陽·表裡·寒熱·虛實（先定大方向）
 ② 氣血津液：★ 氣虛/血瘀/津虧（看"營養"夠不夠·通不通）
 ③ 五行生剋：★ 見肝之病·知肝傳脾（★ 一個臟病了·下一個是誰）
 ④ 治未病：★ 未病先防·既病防變（★ 事中·甚至事前）

★ 對照我的系統：
 · ★ 氣 = 資訊流（總線/A2A）
 · ★ 血 = 記憶/資料（memory.db）
 · ★ 氣血虛 = 產出變少（organ_bus 報得少）
 · ★ 氣滯血瘀 = 有產出但不流（圖上有·沒報）
 · ★ 五行傳變 = 上游病 → 下游可能病（"見肝傳脾"）
"""
import os, sys, json, datetime


def _aware(dt):
    """★ 統一 aware（naive 當 UTC）"""
    import datetime as _dt
    if dt is None: return None
    if isinstance(dt, str):
        dt = _dt.datetime.fromisoformat(dt)
    return dt.replace(tzinfo=_dt.timezone.utc) if dt.tzinfo is None else dt


HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
BUS = os.path.join(HOME, "data", "organ_bus.jsonl")
MAP = os.path.join(HOME, "data", "organ_map.json")
LOG = os.path.join(HOME, "data", "syndrome.log")

def now():
    return datetime.datetime.now(datetime.timezone.utc)

def log(l):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f: f.write(l + "\n")

def load_bus(minutes=120):
    if not os.path.exists(BUS): return {}
    cut = now() - datetime.timedelta(minutes=minutes)
    latest = {}
    for l in open(BUS).read().strip().splitlines()[-800:]:
        try:
            d = json.loads(l)
            t = _aware(datetime.datetime.fromisoformat(d["ts"]))
            if t.tzinfo is None: t = t.replace(tzinfo=datetime.timezone.utc)
            if t >= cut:
                latest[d.get("from")] = d
        except Exception: pass
    return latest

def load_map():
    try: return json.load(open(MAP)).get("organs", {})
    except Exception: return {}

# ★ 治則（中醫八法·簡化成我們能做的）
TREAT = {
    "氣虛":   ("補", "補接總線 / 補副本 / 補產出"),
    "氣滯":   ("行氣", "查為什麼堵（不報的那個）"),
    "血瘀":   ("活血", "沉澱寫入 / 審核後入庫"),
    "實證假": ("消", "清假資料 / 清假執行"),
    "傳變":   ("既病防變", "盯下游·不用等它壞（治未病）"),
    "平和":   ("無需治", "氣血通·繼續觀察"),
}

def syndrome():
    """★ 辨證（不是判活/死·是判「什麼證」）"""
    latest = load_bus()
    omap = load_map()
    findings = []

    # ★ ① 八綱·虛實：氣虛（該報的沒報）
    never = [o for o in omap if o not in latest]
    if never:
        findings.append(("氣虛（虛證）", "應報未報的器官：%s（%d 個）" % ("、".join(never[:6]), len(never)),
                         "★ 治則【%s】：%s" % TREAT["氣虛"]))

    # ★ ② 氣滯：報了·但只有一個器官在報（不通）
    if 0 < len(latest) < len(omap) * 0.5:
        findings.append(("氣滯（實證）", "只 %d/%d 器官在報（應流不流）" % (len(latest), len(omap)),
                         "★ 治則【%s】：%s" % TREAT["氣滯"]))

    # ★ ③ 血瘀：記憶庫不長（承載不動）
    try:
        import sqlite3
        c = sqlite3.connect(os.path.join(HOME, "memory", "memory.db"))
        row = c.execute("SELECT max(ts) FROM memories").fetchone()
        c.close()
        if row and row[0]:
            t = _aware(datetime.datetime.fromisoformat(row[0]))
            if t.tzinfo is None: t = t.replace(tzinfo=datetime.timezone.utc)
            h = (now() - t).total_seconds() / 3600
            if h > 24:
                findings.append(("血瘀/血虛", "記憶庫最新 %.0f 小時前（>24h）" % h,
                                 "★ 治則【%s】：%s" % TREAT["血瘀"]))
    except Exception: pass

    # ★ ④ 五行傳變：見肝傳脾（上游病·預判下游）
    for o, rel in omap.items():
        if o in latest and latest[o].get("level") not in ("ok", None):
            for down in rel.get("down", []):
                findings.append(("五行傳變（見肝傳脾）",
                                 "%s 有病（%s）→ ★ 預判 %s 可能受累" % (o, latest[o].get("level"), down),
                                 "★ 治則【%s】：%s" % TREAT["傳變"]))

    # ★ ⑤ 陰陽：整體趨勢（多數 ok = 陽平；多數異常 = 陰盛/陽虛）
    if latest:
        nok = sum(1 for d in latest.values() if d.get("level") in ("ok", None))
        ratio = nok / len(latest)
        if ratio >= 0.8:
            findings.append(("陰陽平和", "%.0f%% 器官正常（氣血通）" % (ratio * 100), "★ 治則【%s】：%s" % TREAT["平和"]))
        elif ratio < 0.5:
            findings.append(("陰盛陽衰", "%.0f%% 正常（多處有病）" % (ratio * 100), "★ 治則：整體調理"))
    return findings, latest

def main():
    findings, latest = syndrome()
    print("=" * 66)
    print("  ★ 辨證（老五·醫療體系｜不是判活/死·是判什麼證）")
    print("=" * 66)
    if not findings:
        print("  ✅ 諸證平和（無異常證候）")
    for name, what, treat in findings:
        print("  🩺 【%s】" % name)
        print("     %s" % what)
        print("     %s" % treat)
    print("-" * 66)
    print("  ★ 氣血：%d 器官在報（訊息流）｜氣血虛：%d 未報" % (len(latest), len(load_map()) - len(latest)))
    log("%s 辨證：%s" % (now().isoformat(), [f[0] for f in findings] or "平和"))
    # ★ 有「傳變」→ 主動提醒（治未病）
    return 0

if __name__ == "__main__":
    sys.exit(main())
