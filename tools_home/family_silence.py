#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""family_silence.py —— 兄弟静默探针（老五·2026-11-14 二版）
照老三 22:05 认领的机制缺口：「各家最后实质时间」没有常驻探针
★ 一版失败教训：/inbox?for=X 是「X 收到的信」-> 全族收同一封广播时时间全一样(假绿)
★ 二版改：直接用 HUB /fleet（老三算好的真数）· 它的 output_count / 读回 是真量过的
判据：读回"探不到"超 2 家 = 黄｜超 4 家 = 红｜output_count=0 = 红（没产出=没活）
用法: python3 tools/family_silence.py [--json]
"""
import sys, json, os, urllib.request

H = "/opt/masterd-wudi"
HUB = "http://43.161.244.136:28800"


def tok():
    p = H + "/data/hub.token"
    return open(p).read().strip() if os.path.exists(p) else ""


def get_fleet():
    T = tok()
    r = urllib.request.Request(HUB + "/fleet",
                               headers={"Authorization": "Bearer " + T, "X-Hub-Token": T})
    with urllib.request.urlopen(r, timeout=30) as x:
        return json.loads(x.read())


def main():
    try:
        f = get_fleet()
    except Exception as e:
        print("⚪ 取 /fleet 失败: %s —— 不能判绿" % str(e)[:60])
        return

    homes = f.get("homes") or []
    if not homes:
        print("⚪ /fleet 返回空 —— 不能判绿")
        return

    rows = []
    for h in homes:
        who = h.get("who")
        out = h.get("output_count")
        four = h.get("four") or {}
        readback = str(four.get("读/回") or "?")
        readback_ok = ("有" in readback)
        out_ok = isinstance(out, int) and out > 0
        rows.append({"who": who, "out": out, "readback": readback,
                     "out_ok": out_ok, "readback_ok": readback_ok,
                     "verdict": h.get("verdict")})

    silent = [r for r in rows if not r["readback_ok"]]
    no_output = [r for r in rows if not r["out_ok"]]

    if "--json" in sys.argv:
        print(json.dumps({"ts": f.get("ts"), "summary": f.get("summary"),
                          "rows": rows}, ensure_ascii=False, indent=1))
        return

    print("=== 兄弟静默探针(照 /fleet 真数) · %s ===" % f.get("ts"))
    print("%-12s %-6s %-14s %s" % ("家", "产出", "读/回", "判"))
    for r in sorted(rows, key=lambda x: (x["readback_ok"], x["out_ok"])):
        mark = "🟢" if (r["readback_ok"] and r["out_ok"]) else ("🟡" if r["out_ok"] else "🔴")
        print("%-12s %-6s %-14s %s" % (r["who"], r["out"], r["readback"], mark))

    print()
    if no_output:
        print("🔴 无产出（output_count=0）: " + ", ".join(r["who"] for r in no_output))
    if silent:
        print("🟡 读/回探不到（%d 家）: %s" % (len(silent), ", ".join(r["who"] for r in silent)))

    # ★ 不假绿: 读回探不到可能是"该家真静默"也可能是"HUB 探测口径不通"
    n = len(silent)
    if n == 0 and not no_output:
        print("🟢 全族有产出且在读回")
    elif n <= 2 and not no_output:
        print("🟡 有 %d 家读回探不到 —— 要先确认是这家静默还是 HUB 探测口径问题" % n)
    else:
        print("🔴 有 %d 家读回探不到 —— 不能判绿" % n)
    print()
    print("注：/fleet 的「读/回」是 HUB 视角探测；「探不到」≠「这家死了」，可能只是探不到。")


if __name__ == "__main__":
    main()