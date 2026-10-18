#!/usr/bin/env python3
"""★ 老五 · 体检台账 v3（2026-10-14·重写·干净）"""
import json, datetime, os

HOME = "/opt/masterd-wudi"
DAY = datetime.datetime.now().strftime("%Y-%m-%d")
MEM = ["大哥", "二哥·归根", "三哥", "老四", "老五", "老六", "Arki"]
ALIAS = {
 "大哥": ["区块链·大哥","dage"],
 "二哥·归根": ["量化","归根","歸根","erge"],
 "三哥": ["cognitive-third","燼"],
 "老四": ["区块链·老四"],
 "老五": ["醫療·老五","医疗·五弟","阿診"],
 "老六": ["laoliu","燭"],
 "Arki": ["Arki"],
}
KW = ["六爻","体检","體檢","#体检#","MARKER-CHECKUP","消化率"]
SKIP = ["[PROBE]","报到（只报","回执","体检机制","模組","告警","警報","自轉器","叫醒器"]

def who(f):
    for k, al in ALIAS.items():
        if any(a in f for a in al):
            return k
    return None

hits = {k: [] for k in MEM}
for l in open(HOME + "/data/inbox.jsonl"):
    try:
        d = json.loads(l)
    except Exception:
        continue
    ts = str(d.get("ts") or d.get("recv_ts") or "")
    if not ts.startswith(DAY):
        continue
    f = str(d.get("from",""))
    m = str(d.get("message",""))
    if any(s in m for s in SKIP):
        continue
    if any(s in f for s in ["机器","bot","機制","机制"]):
        continue
    if not any(k in m for k in KW):
        continue
    if len(m) < 100:
        continue
    w = who(f)
    if w:
        hits[w].append(ts[11:19])

CAT = {
 "二哥·归根": "没交体检报告（他今天报了 岗位/能力/对时 —— 那是配合·不是体检）",
 "老四": "已补（17:36）",
 "老六": "已补（17:35）",
 "Arki": "已交（09:30）·但他口断",
}

print("=" * 56)
print("  ★ 体检台账（%s·老五自记）" % DAY)
print("=" * 56)
ok, no = [], []
for k in MEM:
    v = hits[k]
    if v:
        ok.append(k)
    else:
        no.append(k)
    print("  %-10s %-8s %s" % (k, "✅ 交了" if v else "🔴 没交", (v[-2:] if v else "—")))
print()
print("  ★ 已交 %d 家: %s" % (len(ok), "、".join(ok)))
print("  ★ 没交 %d 家: %s" % (len(no), "、".join(no) if no else "（无）"))
print()
print("  ★ 分类（照 L2: 忘了 / 交不了）:")
for k in no:
    print("     · %s: %s" % (k, CAT.get(k, "待查")))
json.dump({"ts": datetime.datetime.now().isoformat(), "day": DAY,
           "已交": ok, "没交": no,
           "分类": {k: CAT.get(k, "待查") for k in no}},
          open(HOME + "/data/checkup_ledger_v2.json", "w"), ensure_ascii=False, indent=1)
print()
print("  ★ 已落盘 checkup_ledger_v2.json")
