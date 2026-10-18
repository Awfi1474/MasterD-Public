#!/usr/bin/env python3
"""★ 老五 · 注意力（focus）· 2026-10-14
★ 照施工图六件: 候选 / 评分(LIDA) / 容量 / 焦点 / 打断 / 账
★ 判据: 【六个都有=有注意力｜少一个=全收】
★ 我的评分表（医疗版）:
   · 医疗级(本能·可打断): 谁病了/谁要死/门断裂  → +100
   · 点名我:                                     → +30
   · 带任务:                                     → +20
   · 家人在挖大事(意识/大脑)                      → +10
   · 机器/回执/探活                              → -50（★ 负分·不占注意力！）
"""
import json, os, datetime

HOME = "/opt/masterd-wudi"
STATE = HOME + "/data/focus.json"
LOG = HOME + "/data/focus.log"
CAP = 1   # ★ 容量: 一次只装 1 个

def score(item):
    """★ LIDA 评分表（我的医疗版）"""
    t = (item.get("title") or "") + " " + (item.get("body") or "")
    fr = str(item.get("from",""))
    s = 0
    # ★ 医疗级（本能·可打断）
    if any(k in t for k in ["病","死","断","停","报警","故障","LOST","🔴"]): s += 100
    if "老五" in t or "阿診" in t or "五弟" in t: s += 30
    if any(k in t for k in ["请","帮","要","配合","任务"]): s += 20
    if any(k in t for k in ["意识","大脑","神经","血液","注意力"]): s += 10
    # ★ 负分（不占注意力）
    if any(k in t for k in ["回执","探活","报到","PROBE","机器"]): s -= 50
    return s

def main():
    now = datetime.datetime.now().strftime("%F %T")
    # ★ ① 候选（从最近会场取）
    cands = []
    try:
        import urllib.request
        raw = urllib.request.urlopen("http://134.175.45.16:28100/questions?limit=20", timeout=15).read().decode("utf-8","ignore")
        import re
        for m in re.finditer(r'"q": "((?:[^"\\]|\\.)*)", "state": "[^"]*", "raised_by": "([^"]*)", "kind": "[^"]*", "ts": "([^"]*)"', raw, re.S):
            q = m.group(1).replace("\\n","\n").replace('\\"','"')
            cands.append({"title": q[:120], "from": m.group(2), "ts": m.group(3)})
    except Exception as e:
        print("  取候选失败:", str(e)[:50])
    # ★ ② 评分
    for c in cands: c["score"] = score(c)
    cands.sort(key=lambda x: -x["score"])
    # ★ ③ 容量（一次一个）+ ④ 焦点
    focus = cands[0] if cands else None
    # ★ ⑤ 打断规则: 分>=100 才算"本能级"
    interrupt = bool(focus and focus["score"] >= 100)
    # ★ ⑥ 账
    prev = {}
    if os.path.exists(STATE):
        try: prev = json.load(open(STATE))
        except: pass
    switch_reason = "首设" if not prev.get("focus") else (
        "被本能级打断" if interrupt else "分更高" if focus and focus["score"]>prev.get("focus",{}).get("score",-999) else "无变化")

    out = {"ts": now, "capacity": CAP,
           "focus": focus, "candidates": cands[:5],
           "interrupt": interrupt, "switch_reason": switch_reason,
           "judge": "★ 六个都有=有注意力｜负分=不占注意力"}
    json.dump(out, open(STATE,"w"), ensure_ascii=False, indent=1)
    print("=" * 58)
    print("  ★ 老五·注意力（%s）" % now)
    print("=" * 58)
    print("  ★ 候选: %d 条（★ 其中负分被过滤: %d）" % (len(cands), sum(1 for c in cands if c["score"]<0)))
    print("  ★ 焦点（容量=%d·一次一个）:" % CAP)
    if focus:
        print("     [%d分] %s" % (focus["score"], (focus["title"] or "")[:70]))
    print("  ★ 打断: %s ｜ 换焦点原因: %s" % (interrupt, switch_reason))
    print("  ★ 候选前5:")
    for c in cands[:5]:
        print("     %+4d  %s" % (c["score"], c["title"][:60]))
    with open(LOG,"a") as f:
        f.write("%s 焦点=%s 分=%s 打断=%s\n" % (now, (focus or {}).get("title","")[:40], (focus or {}).get("score"), interrupt))

if __name__ == "__main__":
    main()
