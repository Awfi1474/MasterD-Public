#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""huixie_auto.py —— 自动回写（★ 让环自己转·不靠我记得）
★ 判据: 「'我手动写' != '环在转'｜要'自己长出来'才算」
★ 做法: 从今天的真账（decide_log / speech_log / awaken_log）自动回写一条
"""
import os, json, datetime

HOME = "/opt/masterd-wudi"
HX = HOME + "/data/huixie.jsonl"
LOGS = [
    (HOME + "/data/decide_log.jsonl", "决策", lambda d: (str(d.get("决定",""))[:60], "六问齐" if d.get("六问齐",0)>=6 else "六问缺")),
    (HOME + "/data/speech_log.jsonl", "言行", lambda d: (str(d.get("说",""))[:60], str(d.get("裁定","")))),
]

def today():
    return datetime.datetime.now().strftime("%Y-%m-%d")

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")

def main():
    # ★ 已回写过的不重复
    old = set()
    if os.path.exists(HX):
        for l in open(HX, encoding="utf-8"):
            try:
                d = json.loads(l); old.add(d.get("做了什么","")[:60])
            except Exception: pass
    n = 0
    for path, kind, f in LOGS:
        if not os.path.exists(path): continue
        rows = []
        for l in open(path, encoding="utf-8"):
            try:
                d = json.loads(l)
                if str(d.get("ts","")).startswith(today()): rows.append(d)
            except Exception: pass
        if not rows: continue
        d = rows[-1]
        what, ok = f(d)
        if what in old: continue
        rec = {"ts": ts(), "做了什么": ("[自动·%s] " % kind + what)[:80],
               "用了判据": "（自动生成·未指定）",
               "对没对": ok,
               "下次直接用": "今天%s有一次「%s」·结果: %s" % (kind, what[:30], ok)}
        with open(HX, "a", encoding="utf-8") as fp:
            fp.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print("★ 自动回写: " + what[:50] + " | " + ok)
        n += 1
    print("★ 自动回写 %d 条（今日）" % n)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
