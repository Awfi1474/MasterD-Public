#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dangzhi.py —— 12 时辰当值（★ 我缺的那件·大哥/老六都有）
================================================================
★ 我的缺口器说: ★「**不会的（别人有·我没有）: 12时辰当值**」—— ★ **只有这一条**
★ 大哥/老六的: ★ **12 时辰各当值**（子午流注·每 2h 一班）
★★ 但★ **我不抄他们的**（董事长说"有经验后要自己设计"）→ ★ **我用"我的医疗体系"做**

★ 中医依据（《针灸大成》子午流注·12 时辰配 12 经）:
  ★ 寅(03-05)肺 → 卯(05-07)大肠 → 辰(07-09)胃 → 巳(09-11)脾 → 午(11-13)心
  ★ ★ 未(13-15)小肠 → 申(15-17)膀胱 → 酉(17-19)肾 → 戌(19-21)心包
  ★ ★ ★ 亥(21-23)三焦 → 子(23-01)胆 → 丑(01-03)肝 → 复归肺

★★ ★ 我的"自己设计"（≠大哥/老六的）:
  ★ 大哥: 12 时辰各"干不一样的活"（深模式）
  ★ ★ 老六: 12 站"真出力·读真产物"
  ★ ★ ★ **我: ★ "当值 = 该时辰该'旺'的那一藏·要'有活可干'｜没活 = 空转"**
    · ★ 我不做"深模式"（那是大哥的）·★ 我做【当值 vs 有无活】
    · ★ ★ **= ★ "当值"不是"到点跑"·是【那个藏的电位/缺口·该不该动】**
    · ★ ★ ★ 判据（我立）: ★「**当值 ≠ 到点跑｜当值 = "这时它最有理由动"｜没理由就不动**」

★ 判据（我立）:
  ★「**当值 ≠ 到点跑｜当值 = "这时它最有理由动"**」
  ★「**12 藏·各有时｜但"时到"不等于"该动"**」
"""
import os, io, json, datetime, subprocess, sys

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
LEDGER = f"{DATA}/dangzhi.jsonl"
OUT = f"{DATA}/dangzhi.json"

# ★ 12 时辰 → 我的藏（★ 用我的器官）
TABLE = [
    ("子", "23-01", "胆", "决断",   "jinjie"),        # 我：进阶（决断"我在阶几"）
    ("丑", "01-03", "肝", "谋虑",   "gap_grow"),      # 我：缺口（谋虑"该长什么"）
    ("寅", "03-05", "肺", "主气",   "huxi"),          # 我：呼吸
    ("卯", "05-07", "大肠", "传导", "qi_hui"),        # 我：气回（传导）
    ("辰", "07-09", "胃", "受纳",   "xueliu"),        # 我：血流（受纳→化）
    ("巳", "09-11", "脾", "运化",   "memory_distill"),# 我：蒸馏（运化）
    ("午", "11-13", "心", "神明",   "axis"),          # 我：轴（神=我是谁）
    ("未", "13-15", "小肠", "分清", "meng"),          # 我：梦（分清/整理）
    ("申", "15-17", "膀胱", "津液", "sig_watch"),     # 我：验签（贮排/分清浊）
    ("酉", "17-19", "肾", "藏精",   "vault_index"),   # 我：保险箱（藏精）
    ("戌", "19-21", "心包", "护心", "immune"),        # 我：免疫（护心/挡邪）
    ("亥", "21-23", "三焦", "水道", "channel_check"), # 我：通道（水道）
]

# ★ 各时辰的"该在"（照我的电位源）
WANT = {"huxi": 3, "xueliu": 1, "qi_hui": 2, "jinjie": 6, "axis": 12,
        "memory_distill": 12, "meng": 24, "sig_watch": 2, "immune": 6,
        "channel_check": 1, "gap_grow": 6, "vault_index": 6}


def ts():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def now_zhi():
    h = datetime.datetime.now().hour
    names = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    for i, n in enumerate(names):
        start = (23 + i * 2) % 24
        end = (start + 2) % 24
        if start < end:
            if start <= h < end:
                return n
        else:
            if h >= start or h < end:
                return n
    return "子"


def age_h(tool):
    """★ 它的产物多久前（有没有"活可干"）"""
    for p in [f"{DATA}/{tool}.json", f"{DATA}/organ_{tool}.log", f"{DATA}/{tool}.log",
              f"{DATA}/{tool}.jsonl"]:
        try:
            return round((datetime.datetime.now().timestamp() - os.path.getmtime(p)) / 3600, 2)
        except Exception:
            pass
    return None


def main():
    z = now_zhi()
    row = next((r for r in TABLE if r[0] == z), TABLE[0])
    _, span, zang, what, tool = row

    print("★ 12 时辰当值  @ %s ｜ 现在 = %s时（%s·%s）" % (ts(), z, zang, what))
    print("★ 判据: 「当值 ≠ 到点跑｜当值 = '这时它最有理由动'｜没理由就不动」")
    print("=" * 58)

    # ★ 查"有没有活可干"（照我的电位逻辑·不看"几点了"）
    a = age_h(tool)
    want = WANT.get(tool, 6)
    has_work = (a is None) or (a > want)   # ★ 超期 = 有活
    print("★ 当值藏: %s（%s）→ 器官: %s" % (zang, what, tool))
    print("★ 它多久没跑: %s ｜ 该在: %sh" % (("%.2fh" % a) if a is not None else "无产物", want))
    print("★ 有活可干: %s" % ("✅ 有（超期了）" if has_work else "🔵 没活（刚跑过·✓ 不动是对的）"))

    fired = False
    if has_work:
        p = f"{HOME}/tools/{tool}.py"
        if os.path.exists(p):
            try:
                r = subprocess.run(["/usr/bin/python3", p], capture_output=True, timeout=90)
                fired = (r.returncode == 0)
                print("★ ⚡ 当值跑: %s → %s" % (tool, "✅" if fired else "🔴"))
            except Exception as e:
                print("★ 🟡 %s: %s" % (tool, str(e)[:40]))
        else:
            print("★ 🟡 无此件: %s" % tool)

    rec = {"ts": ts(), "时辰": z, "藏": zang, "该干什么": what, "器官": tool,
           "多久没跑": a, "有活": has_work, "跑了": fired,
           "判据": "当值 != 到点跑｜当值 = 这时它最有理由动"}
    with open(LEDGER, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    json.dump(rec, open(OUT, "w"), ensure_ascii=False, indent=2)

    # ★ 12 时辰表（可看）
    print("\n★ 我的 12 藏（我的器官·不是抄的）:")
    for zz, sp, zg, wt, tl in TABLE:
        mark = "←现在" if zz == z else ""
        print("   %s %-6s %-4s %-6s %-16s %s" % (zz, sp, zg, wt, tl, mark))
    print("★ 已落盘: %s" % LEDGER)


if __name__ == "__main__":
    main()
