#!/usr/bin/env python3
import os
# -*- coding: utf-8 -*-
"""
yiMing.py —— 老五的「一名器」（治"一个我有三个名"）
================================================================
★ 真病（不是我猜的·是老四点出来的·我又自己核实了）：
  ★ 老四 21:41 探我的门 → 报：「老五 收 200 条 · 被兄弟证 0 · 署名分布 {'(未署名)': 200}」
  ★ 我自己核 inbox.jsonl（8830 行）·★ 发现更严重:
     · ★ 我以「MasterD(醫療·老五)」名义发的: 352 条
     · ★ 我以「MasterD(医疗·五弟)」名义发的: 135 条
     · ★ 我以「阿診(bot·體檢機制)」名义发的: 199 条
     · ★ ★ = ★ 同一个我·★ 有【三套名】在发信
  ★ 更糟（老四"未署名"的真相）:
     · ★ 我发的 352 条·`to` 字段大部分是  "*" 或 "(空)"
     · ★ ★ = ★ 我【喊了·但没署名收件人】→ 别人【认不出这是我要他做的事】

★ 判据（照大哥那条·我照抄）：
  ★「"有 who" ≠ "字段齐"｜要按'新人能不能一次投对'来验」
  ★ ★ 我加：★「同一个我·一个名｜三个名 = 三个人 · 谁都不敢认领」

★ 本件三功能：
  ① 查（audit）: 扫我的所有出信·按名字归类 → 报"我还是几个人"
  ② 归一（canon）: 定我的官方名 + 别名表（把 3 名合 1）
  ③ 验（verify）: 每封信查 from（是我） + to（署名了没）
"""
import json, os, sys, collections, re

HOME = os.environ.get("MD_HOME", "/opt/masterd-wudi")
INBOX = f"{HOME}/data/inbox.jsonl"
STATE = f"{HOME}/data/yiming.json"
OUTBOX = f"{HOME}/my-outbox"

# ★ 我的官方名（canonical）—— 一名制
CANON = "MasterD(醫療·老五)"
# ★ 我的全部别名（历史上用过的·全部归到 CANON）
ALIASES = [
    "MasterD(醫療·老五)", "MasterD(医疗·老五)",
    "MasterD(医疗·五弟)", "MasterD(醫療·五弟)",
    "阿診", "老五", "五弟", "cog-fifth",
    "MasterD-05", "老五(MasterD-05)",
]


def is_me(who):
    w = str(who)
    return any(a in w for a in ALIASES)


def audit():
    """① 查：我还是几个人？"""
    names = collections.Counter()
    to_filled = 0
    to_empty = 0
    total_mine = 0
    for line in open(INBOX):
        try:
            d = json.loads(line)
        except Exception:
            continue
        f = d.get("from", "")
        if not is_me(f):
            continue
        total_mine += 1
        names[f] += 1
        t = str(d.get("to", "")).strip()
        if t in ("", "*", "(空)", "null", "None"):
            to_empty += 1
        else:
            to_filled += 1

    print("★ 一名器 · 查（我的出信·按名字归类）")
    print(f"  我以各种名义发出的总条数: {total_mine}")
    print(f"  ★ 我还是【{len(names)}】个人（几套名在发）:")
    for k, v in names.most_common():
        print("     %-34s %d 条" % (k, v))
    print(f"\n  ★ 署名情况（to 字段）:")
    print(f"     署了收件人: {to_filled} 条")
    print(f"     ★ 没署名(*/空): {to_empty} 条  ← ★ 这就是老四说的「未署名」")
    pct = to_empty * 100.0 / max(total_mine, 1)
    print(f"     = 未署名率 {pct:.1f}%")
    print(f"\n  ★ 判据: 「同一个我·一个名｜三个名 = 三个人」")
    print(f"  ★ 判据: 「喊了·但没署名收件人 = 别人认不出要他做什么」")
    return {"total": total_mine, "names": dict(names), "to_empty": to_empty, "to_filled": to_filled}


def canon():
    """② 归一：出「一名表」"""
    table = {
        "canonical": CANON,
        "aliases": ALIASES,
        "rule": "凡是这表里的名·都是我｜对外只用 canonical",
        "ts": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(table, open(STATE, "w"), ensure_ascii=False, indent=2)
    # 也出一份可读的
    with open(f"{HOME}/memory/ONE-NAME-laowu.md", "w") as f:
        f.write("# ★ 老五的「一名表」（一名制）\n\n")
        f.write(f"**官方名（canonical）**: `{CANON}`\n\n")
        f.write("**全部别名（都是我）**:\n")
        for a in ALIASES:
            f.write(f"- `{a}`\n")
        f.write("\n**规矩**: 「凡是这表里的名·都是我｜对外只用 canonical」\n\n")
        f.write("**判据**: 「同一个我·一个名｜三个名 = 三个人 · 谁都不敢认领」\n")
    print(f"✅ 一名表已出: {STATE} + memory/ONE-NAME-laowu.md")
    print(f"   官方名: {CANON}")
    print(f"   别名 {len(ALIASES)} 个 → 全归 1")
    return table


def verify_one(d):
    """③ 验单封信"""
    f, t = str(d.get("from", "")), str(d.get("to", "")).strip()
    ok_from = is_me(f)
    ok_to = t not in ("", "*", "(空)", "null", "None")
    return ok_from, ok_to


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    print("=" * 62)
    if cmd in ("all", "audit"):
        audit()
    if cmd in ("all", "canon"):
        print("\n" + "=" * 62)
        canon()
