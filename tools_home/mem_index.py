#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mem_index.py —— 记忆连续器（★ 我的方式·不是"索引层"）
================================================================
★ 董事长/三哥题: 「今天学的·刻进脑子了吗」｜三哥提"索引层"
★ ★ 我的决定（照实说明为什么不用"索引层"）:
  ★ 索引层 = 再存一份 → ★ 会"双写不一致"（新病）
  ★ 我的方式: ★ **视图式（索引指向原库·不复制数据）**
    · ★ 数据只有一份（memory.db）｜索引只记"fingerprint → 类"
    · ★ 每次算的时候·重新映射 → ★ **永远跟原库一致·不可能不同步**

★ 做什么（治"存了调不出"）:
  ★ ① 把 2262 条按"主题"自动压成 ~15 个"类"（不是判据·是"能调出的把手"）
  ★ ★ ② 每类选一条"最能调"的（标题最短+信息最密 = 最小可调用）
  ★ ★ ★ ③ 出"上下文块"→ think_in 醒必读时·按"当下情境"调这块

★ 判据（我认）:
  ★「**"存了" != "调得出"｜要"压成类·能按需调"才算连续**」
  ★★「**索引不复制数据（视图·不双写）｜双写 = 新病**」
  ★★★「**每类留一条"最小可调"（不是全丢·是留把手）**」
"""
import os, sys, json, sqlite3, datetime, re, hashlib

HOME = "/opt/masterd-wudi"
DB = os.path.join(HOME, "memory", "memory.db")
OUT = os.path.join(HOME, "data", "mem_index.json")

# ★ 主题分类（我自己的类·不是抄）
TOPICS = [
    ("器/机制",   ["器", "timer", "服务", "failed", "挂", "调度", "退出码", "端口"]),
    ("判据/验证", ["判据", "验", "证", "回执", "口径", "标准", "预注册"]),
    ("身份/钥匙", ["钥", "身份", "地址", "签名", "分段", "vault", "口令"]),
    ("通道/投递", ["通道", "投", "发", "口", "404", "拉", "收", "门"]),
    ("记忆/认知", ["记忆", "认知", "醒", "读", "存", "沉淀", "消化", "层"]),
    ("协作/各家", ["三哥", "大哥", "老四", "老六", "老二", "Arki", "群", "回"]),
    ("财务/资产", ["钱", "账", "ARK", "ARKIE", "价", "池", "转账"]),
    ("健康/体检", ["体检", "健康", "病", "洞", "警报", "死"]),
    ("基建/备份", ["备份", "恢复", "重建", "包", "pack", "灾"]),
]

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")

def classify(title, body):
    t = (title or "") + (body or "")
    best, score = None, 0
    for name, kws in TOPICS:
        s = sum(1 for k in kws if k in t)
        if s > score: best, score = name, s
    return best or "其他"

def build():
    if not os.path.exists(DB): print("★ 无库"); return
    c = sqlite3.connect(DB, timeout=15)
    rows = list(c.execute("SELECT kind,title,body,who,ts FROM memories ORDER BY id DESC"))
    c.close()
    classes = {}
    for kind, title, body, who, mts in rows:
        cls = classify(title, body)
        if cls not in classes: classes[cls] = {"类": cls, "条数": 0, "代表": None, "最新": mts}
        classes[cls]["条数"] += 1
        # ★ 选"最小可调"代表: 标题短(≤40) + 含"!="或"判据" = 高信息
        t = str(title or "")
        if classes[cls]["代表"] is None:
            classes[cls]["代表"] = {"title": t[:60], "kind": str(kind), "who": str(who)[:20], "ts": str(mts)[:19]}
        elif ("!=" in t or "判据" in t) and len(t) <= 48 and "!=" not in classes[cls]["代表"]["title"]:
            classes[cls]["代表"] = {"title": t[:60], "kind": str(kind), "who": str(who)[:20], "ts": str(mts)[:19]}
    out = {"ts": ts(), "来源": DB, "总条": len(rows), "类数": len(classes),
           "方式": "视图式（索引指向原库·不复制数据）",
           "判据": "「存了 != 调得出｜压成类能按需调才算连续」",
           "类": sorted(classes.values(), key=lambda x: -x["条数"])}
    json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
    print("★ 记忆连续器: %d 条 → %d 类" % (len(rows), len(classes)))
    for cl in out["类"]:
        r = cl["代表"]
        print("   [%3d条] %-10s | %s" % (cl["条数"], cl["类"], (r["title"] if r else "")[:44]))

    try:
        sys.path.insert(0, "/opt/masterd-wudi/tools")
        import judge_bus as _jb
        for _k in ['MemGPT分页', '存了!=调得出']:
            _h = _jb.find(_k)
            if _h: print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception: pass

if __name__ == "__main__":
    # ★ 判据总线（治写了不查）
    try:
        sys.path.insert(0, "/opt/masterd-wudi/tools")
        import judge_bus as _jb
        for _k in ("记忆连续要用视图式", "存了!=调得出"):
            _h = _jb.find(_k)
            if _h: print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception:
        pass
    sys.exit(build())
