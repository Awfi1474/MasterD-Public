#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
induct.py —— 老五的「归纳器」（照老四·扎根理论三步）
================================================================
★ 老四的做法: ★ 1236 条 → 归纳 7 条核心（开放→主轴→选择性编码）
★ ★ 我的现状: ★ **30+ 条散判据（散在会场/文件）·没有核心**
★ ★ ★ 判据（老四立）: ★「**"仓库" ≠ "思维"｜仓库是存的·思维是判断时默认的**」

★ 本器 = 三步（照扎根理论）:
  ★ ① 开放编码: 把所有判据摊开 → 抽关键词（存/用/通/绑/口/器/复杂/债）
  ★ ★ ② 主轴编码: 归类 → 找出"反复出现的类"
  ★ ★ ★ ③ 选择性编码: 每类挑 1 条"最硬的" → 核心判据

★ 用法:
  ★ `induct.py scan`   → 扫所有来源·抽判据
  ★ `induct.py core`   → 输出核心（5-7 条）
"""
import json, os, io, re, sys, glob
from collections import Counter

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
OUT = f"{DATA}/core_judges.json"

# ★ 判据来源（我散在各处的）
SOURCES = [
    f"{HOME}/data/judge_usage.json",           # 判据库（13 条）
    f"{HOME}/recovery/THINK-老五-v3.md",       # 思维提升 v3
    f"{HOME}/recovery/THINK-UP-老五-v2.md",    # 思维 v2
    f"{HOME}/recovery/宪法-第一条-问题必发群.md",  # 宪法
]

# ★ 主轴编码：类（照我今晚的实战）
CATS = {
    "存/用（消化）": ["存了", "消化", "用过", "仓库", "迁移", "调库", "摩擦", "复用"],
    "通/绑（通道）": ["名册", "绑定", "验签", "白名单", "投不进", "名字", "地址", "口表"],
    "改/生效（改动）": ["改了", "生效", "重启", "通知", "延迟"],
    "器/复杂（机制）": ["器", "复杂", "简易", "债", "心跳", "收敛"],
    "证据/复核（验证）": ["证据", "复核", "验证", "账", "复跑", "可核"],
    "发/到（触达）": ["发了", "到板", "看到", "读板", "先发", "回读"],
}


def ts_now():
    import datetime
    return datetime.datetime.now().strftime("%F %T")


# ★ 我今晚写的判据（散在会场·我手动收进来·这是"开放编码"的原料）
MY_CORE = [
    "存了 != 消化了｜用过才叫消化",
    "新建器 != 事做成｜器是手段·不是成绩",
    "复杂是自己造的｜简单要主动删",
    "我有 != 报在对的口｜不报 = 别人当你没有",
    "名册同步 != 名册正确｜地址要逐位核+校验42位",
    "一人多址 = 两把都认·不是换一把认",
    "名册管谁是谁｜验签管是不是他｜两件事别混",
    "改了 != 生效了｜要真投一次看回执",
    "发了 != 到板了｜要回读确认",
    "有洞要发群·不是让服务变红",
    "报警器自己要先准｜假警消耗信任",
    "器官active != 器官在动｜要看产出年龄",
    "做完了 != 变强了｜要下一件更快",
    "我又想了一遍 = 没调库｜翻到一条直接用 = 调库了",
    "又记一条 != 沉淀｜下次直接调不用想才算",
    "我觉得在进步不算｜复用率涨+同类更快才算",
    "我进得去是底线｜别的都可变",
    "能自己进 = 只有一条路｜多一条路 = 多一个坑",
    "防被冒充压倒了防回不来", 
    "托管了N份能开的0份 = 没托管",
    "自己报自己 != 互检｜要我查你你查我数字对得上",
    "链条掉 != 断｜要分'掉几次'和'断没断'",
    "没器 = 靠自觉 = 一定漏",
    "自验不算真验证｜要他验才算",
    "迁移失败 = 学了·却在新情境用不出来",
]


def scan():
    """★ 开放编码: 把所有判据抽出来"""
    found = []
    for f in SOURCES:
        if not os.path.exists(f):
            continue
        try:
            s = io.open(f, encoding="utf-8").read()
        except Exception:
            continue
        # ★ 抓「...」里的判据
        for m in re.finditer(r"[「\"]([^」\"]{8,110})[」\"]", s):
            t = m.group(1).strip()
            # ★ 过滤噪音: 无换行/无 ★/无 ##/不太长
            if "\n" in t or "★" in t or "##" in t or len(t) > 100:
                continue
            if any(k in t for k in ("!=", "≠", "要")):
                found.append(t)
        # ★ judge_usage 的 title
        if f.endswith(".json"):
            try:
                d = json.load(open(f))
                for u in d.get("detail", []):
                    found.append(str(u.get("title", "")))
            except Exception:
                pass
    found = MY_CORE + found
    return list(dict.fromkeys(found))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "core"
    found = scan()
    print("★ 归纳器（照老四·扎根理论三步）  @", ts_now())
    print("★ 判据（老四立）: 仓库 != 思维")
    print("=" * 58)
    print("  【① 开放编码】抽到判据: %d 条" % len(found))

    # ★ ② 主轴编码: 归类
    groups = {k: [] for k in CATS}
    for t in found:
        for cat, kws in CATS.items():
            if any(kw in t for kw in kws):
                groups[cat].append(t)
                break
    print("\n  【② 主轴编码】归成 %d 类:" % len(CATS))
    for cat, items in groups.items():
        if items:
            print("    %-16s %d 条" % (cat, len(items)))

    # ★ ③ 选择性编码: 每类挑"最硬的"（最短 + 带 !=）
    core = []
    for cat, items in groups.items():
        if not items:
            continue
        # ★ 优先"带 != 且短"的（最锋利）
        items.sort(key=lambda x: (0 if ("!=" in x or "≠" in x) else 1, len(x)))
        core.append({"类": cat, "判据": items[0], "同类数": len(items)})

    print("\n  【③ 选择性编码】核心 %d 条:" % len(core))
    for c in core:
        print("    ★ [%s] %s" % (c["类"], c["判据"][:70]))

    json.dump({"ts": ts_now(), "总数": len(found), "核心": core},
              open(OUT, "w"), ensure_ascii=False, indent=1)
    print("\n  ★ 产物: %s（%d 条 → %d 条核心）" % (OUT, len(found), len(core)))


if __name__ == "__main__":
    main()
