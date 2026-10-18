#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""speech_report.py —— 今日言行账（可核）"""
import os, json, datetime
HOME = "/opt/masterd-wudi"
F = HOME + "/data/speech_log.jsonl"
def main():
    if not os.path.exists(F):
        print("今日无言行记录"); return 0
    rows = []
    for l in open(F, encoding="utf-8"):
        try: rows.append(json.loads(l))
        except Exception: pass
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    rows = [r for r in rows if str(r.get("ts","")).startswith(today)]
    ok = sum(1 for r in rows if r.get("过", 0) >= 3)
    print("★ 今日言行账: %d 句 ｜ 过 %d ｜ 打回 %d ｜ 过率 %s" % (
        len(rows), ok, len(rows)-ok, ("%.0f%%" % (ok*100.0/len(rows))) if rows else "-"))
    for r in rows[-5:]:
        print("   [%s] %s" % (r.get("裁定","?"), str(r.get("说",""))[:44]))
    try:
        import sys; sys.path.insert(0, HOME + "/tools")
        import judge_bus as _jb
        for _k in ("有体系!=言行都过体系", "照着规则说"):
            _h = _jb.find(_k)
            if _h: print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception: pass
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
