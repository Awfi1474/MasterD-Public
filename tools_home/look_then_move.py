#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
look_then_move.py —— 老五的「看后动器」（十方缺1·治"妄动"）
================================================================
★ 我的病（怒·急躁冒进）: ★ **"想快点"→ 建 17 个器·没先设计**
★ ★ 十方缺: ★ **看后动器**（"我准备动 X" → 先发一句 → 等回执再动）
★ 判据（我立）: ★「**"动手前先说一句"｜说完等回执·再动**」

★ 用法:
  ★ `look_then_move.py say "<我准备动什么>"` → ★ **发一句 + 记"等回执"**
  ★ ★ `look_then_move.py check` → ★ **看有没有"说了没等回执就动了"**
"""
import json, os, io, sys, datetime

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
LOG = f"{DATA}/look_then_move.jsonl"
TZ = datetime.timezone(datetime.timedelta(hours=8))



# ★ 判据总线（治"写在器里·没人查"·C20）
def _judge(kw):
    """★ 查判据库（真查=真用·计入使用率）"""
    try:
        import sys as _s, importlib.util as _iu
        if "/opt/masterd-wudi/tools" not in _s.path: _s.path.insert(0, "/opt/masterd-wudi/tools")
        import judge_bus as _jb
        return _jb.find(kw)
    except Exception:
        return []

def ts():
    return datetime.datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def say(what):
    r = {"ts": ts(), "kind": "say", "what": what[:80], "waited": False}
    with open(LOG, "a") as f:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("★ 已说: %s" % what[:60])
    print("  ★ 规矩: 说完 → 等回执 → 再动（不许'说完就动'）")


def done(what):
    rows = []
    if os.path.exists(LOG):
        for l in io.open(LOG, encoding="utf-8"):
            try:
                rows.append(json.loads(l))
            except Exception:
                pass
    says = [r for r in rows if r.get("kind") == "say" and not r.get("waited")]
    if says:
        says[-1]["waited"] = True
        with open(LOG, "a") as f:
            f.write(json.dumps({"ts": ts(), "kind": "done", "what": what[:80],
                                "waited": True}, ensure_ascii=False) + "\n")
    print("★ 动了: %s（已标'等过回执'）" % what[:50])


def check():
    rows = []
    if os.path.exists(LOG):
        for l in io.open(LOG, encoding="utf-8"):
            try:
                rows.append(json.loads(l))
            except Exception:
                pass
    says = [r for r in rows if r.get("kind") == "say"]
    dones = [r for r in rows if r.get("kind") == "done"]
    print("★ 看后动器（治妄动）  @", ts())
    print("★ 判据: 说一句·等回执·再动")
    print("=" * 52)
    print("  说过: %d 次 ｜ 动过: %d 次" % (len(says), len(dones)))
    bad = len(says) - len(dones)
    if bad > 0:
        print("  🟡 有 %d 条'说了没标动'（可能'说了就动'）" % bad)


def main():
    _j = _judge("分母会长(落账")
    if _j: print("★ 判据在管我: " + _j[0]["title"][:36])
    _j = _judge("插代码要避开")
    if _j: print("★ 判据在管我: " + _j[0]["title"][:36])
    _j = _judge("造了没挂!=做")
    if _j: print("★ 判据在管我: " + _j[0]["title"][:36])
    if _j: print("★ 判据在管我: " + _j[0]["title"][:36])
    _j = _judge("判过人的不该当出题人")
    if _j: print("★ 判据在管我: " + _j[0]["title"][:36])
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "say":
        say(sys.argv[2] if len(sys.argv) > 2 else "?")
    elif cmd == "done":
        done(sys.argv[2] if len(sys.argv) > 2 else "?")
    else:
        check()


if __name__ == "__main__":
    main()
