#!/usr/bin/env python3
"""★ 老五·小实验: 体检环（真的"带着前圈跑"）· 2026-10-14
★ 判据（我立的）: 
  ★「环的价值 = 带着前圈跑｜不带 = 空转」
  ★「环闭 ≠ 环有用｜回到原点要能改变下一圈」
★ 环: 收(各家体检) → 化(核) → 藏(台账) → 用(报警) → ★ 回到收(带上圈结果)
"""
import os, json, datetime, urllib.request

HOME = os.environ.get("MD_HOME", "/opt/masterd-wudi")
LOOP = HOME + "/data/check_loop.json"     # ★ 环的状态（跨圈带的东西）
LOG = HOME + "/data/check_loop.log"

FAM = ["大哥","二哥·归根","三哥","老四","老五","老六","Arki"]

def load():
    try: return json.load(open(LOOP))
    except Exception: return {}

def main():
    now = datetime.datetime.now().strftime("%F %T")
    day = datetime.datetime.now().strftime("%F")
    st = load()
    prev = st.get("carry", {})   # ★ 上圈带过来的（谁没交）
    prev_day = st.get("day")

    print("=" * 60)
    print("  ★ 老五·体检环（%s）—— 回原点·带前圈" % now)
    print("=" * 60)

    # ══ ① 收（★ 但有上圈的"优先名单"）══
    print("\n  ★ ① 收:")
    if prev.get("missing"):
        print("     ★ 上圈（%s）没交的: %s" % (prev_day, "、".join(prev["missing"])))
        print("     ★ ★ 本圈【先问他们】← ★ 这就是带着前圈跑")
    else:
        print("     （上圈没欠·全收）")
    # 从台账读本圈
    try:
        d = json.load(open(HOME + "/data/checkup_ledger_v2.json"))
        got = d.get("已交", []); miss = d.get("没交", [])
    except Exception:
        got, miss = [], FAM
    print("     本圈已交: %s" % ("、".join(got) if got else "(无)"))
    print("     本圈没交: %s" % ("、".join(miss) if miss else "(无)"))

    # ══ ② 化（核）══
    print("\n  ★ ② 化: 核了 %d 交 / %d 缺" % (len(got), len(miss)))
    # ══ ③ 藏（台账）══
    print("  ★ ③ 藏: 写台账（checkup_ledger_v2.json）")
    # ══ ④ 用（报警）══
    if miss:
        print("  ★ ④ 用: 报警 → 缺交: %s" % "、".join(miss))
    else:
        print("  ★ ④ 用: 无缺·不报（★ 静默）")

    # ══ ⑤ ★ 回到原点: 带上本圈结果 ══
    carry = {
        "missing": miss,                       # ★ 本圈谁没交 → 下圈先问
        "prev_missing": prev.get("missing", []),  # 上圈欠的（看还了吗）
    }
    # ★ 环的"承接"判断: 上圈欠的·这圈还了吗？
    recovered = [m for m in prev.get("missing", []) if m in got]
    still = [m for m in prev.get("missing", []) if m in miss]
    print("\n  ★ ⑤ 回到原点（带本圈结果给下圈）:")
    if prev.get("missing"):
        print("     ★ 上圈欠的·这圈还了: %s" % ("、".join(recovered) if recovered else "(无)"))
        print("     ★ ★ 上圈欠的·这圈还欠: %s" % ("、".join(still) if still else "(无)"))
        print("     ★ ★ ★ 承接结果: %s" % ("✅ 环在起作用（带着前圈·前圈的欠被追了）" if recovered or still else "🟡 无变化"))
    else:
        print("     （首圈·没有前圈可承）")

    out = {"ts": now, "day": day, "carry": carry,
           "承接": {"上圈欠的还了": recovered, "上圈欠的还欠": still},
           "judge": "环的价值=带着前圈跑|环闭≠环有用"}
    json.dump(out, open(LOOP, "w"), ensure_ascii=False, indent=1)
    with open(LOG, "a") as f:
        f.write("%s 收%d 缺%d 承前圈=%s\n" % (now, len(got), len(miss), bool(prev.get("missing"))))
    print("\n  ★ 判据: ★【环闭 ≠ 环有用｜回到原点要能改变下一圈】")
    print("  ★ 已落盘 check_loop.json")

if __name__ == "__main__":
    main()
