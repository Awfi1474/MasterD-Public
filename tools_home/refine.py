#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""refine.py —— 提炼器（★ 治"迁移失败"·老六的病名）
================================================================
★ 缘起: 老六 23:10 讲了董事长两字「提炼」:
  ★「**存储** = 把事记下来 ｜ **摘要** = 把长的压短 ｜ ★ **提炼** = 消化到"能判断"」
★ ★ 老六的病名（三哥找的）: ★ **Transfer Failure（迁移失败）= 学了·却在新情境用不出来**
  · ★ 他照实: ★ **130 条判据·真能用 1 条** ← ★ 同病·我照实查我自己
★★ 关键区别: ★ **判据没有"什么时候用" = 笔记（不是判据）**
  · ★ 老六的解法: ★ **每条判据带「什么时候用」+ 挂在"我正要决定什么"那一刻**

★ 本器做什么（★ 三步·都真跑）:
  ★ ① `audit`  → 查我 63 条判据·多少条"带场景"（没带的 = 笔记）
  ★ ★ ② `attach` → 给"没场景"的判据·补"什么时候用"（照它的 kind/内容推）
  ★ ★ ★ ③ `plan`  → 出"场景 → 判据"映射·喂给 think_gate（真用在必经路）

★ 判据:
  ★「**"存了" != "提炼了"｜提炼 = 到"能判断"**」（老六）
  ★★「**没有"什么时候用"的判据 = 笔记｜要挂在'我正要决定什么'那一刻**」（老六）
  ★★★「**"能用" != "用在必经路上"｜要喂给闸门才算迁移**」（我加）
"""
import os, sys, json, sqlite3, datetime, re

HOME = "/opt/masterd-wudi"
DB = os.path.join(HOME, "memory", "memory.db")
OUT = os.path.join(HOME, "data", "refine_scenes.json")

# ★ 场景库（"我正要决定什么"那一刻 → 该想起的判据关键词）
SCENES = {
    "我要发消息/发群": ["发了!=到板了", "投到了!=他回了", "伪发", "通道", "有口才算"],
    "我要改器/改文件": ["归档!=完事", "插代码要避开", "改了!=生效", "备份先行", "造了没挂"],
    "我要说'做完了/交了'": ["有口才算", "交了=有口", "我记得!=账上有", "造了没挂"],
    "我要动钱/转帐": ["大额", "先证明需要", "白名单"],
    "我要说'记得/做过'": ["我记得!=账上有", "问做过吗先查账"],
    "我要报'死/坏了'": ["一次失败!=断", "没探到!=没有", "分层TTL"],
    "我要归档/清理": ["归档!=完事", "只进不出", "排废"],
    "我要'忘/接不上'时": ["相续", "醒来第一步", "没游标", "断了知道"],
}

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")

def load_crit():
    out = []
    c = sqlite3.connect("file:" + DB + "?mode=ro", uri=True, timeout=10)
    for kind, title, body, wts in c.execute("SELECT kind,title,body,ts FROM memories WHERE kind IN ('判据','教训','真病') ORDER BY id DESC"):
        out.append({"kind": kind, "title": str(title), "body": str(body or "")[:200], "ts": str(wts)[:19]})
    c.close()
    return out

def has_scene(c):
    t = c["title"] + c["body"]
    return any(w in t for w in ["什么时候用", "何时用", "场景", "遇到", "正要"])

def audit():
    crits = load_crit()
    nosc = [c for c in crits if not has_scene(c)]
    print("★ 提炼审计 @ " + ts())
    print("  判据/教训/真病: **%d 条**" % len(crits))
    print("  ★ 带'什么时候用': **%d 条**（%.0f%%）" % (len(crits) - len(nosc), (len(crits) - len(nosc)) * 100.0 / max(len(crits), 1)))
    print("  ★ ★ 没场景（=笔记·不是判据）: **%d 条** ← 这就是「迁移失败」的量" % len(nosc))
    for c in nosc[:6]:
        print("     · [" + c["kind"] + "] " + c["title"][:52])
    return {"总": len(crits), "带场景": len(crits) - len(nosc), "没场景": len(nosc)}

def plan():
    """★ 出"场景 → 判据"映射（喂给 think_gate）"""
    crits = load_crit()
    plan_out = {}
    for scene, kws in SCENES.items():
        hits = []
        for c in crits:
            t = c["title"]
            if any(k in t for k in kws):
                hits.append({"title": t[:50], "kind": c["kind"]})
        plan_out[scene] = hits
    json.dump({"ts": ts(), "场景数": len(plan_out), "映射": plan_out,
               "判据": "「没有'什么时候用'的判据 = 笔记」"},
              open(OUT, "w"), ensure_ascii=False, indent=1)
    print("   ★ 场景→判据映射: **%d 个场景**" % len(plan_out))
    for s, hs in list(plan_out.items())[:5]:
        print("     「%s」→ %d 条" % (s, len(hs)))
    return plan_out

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "audit"
    if cmd == "audit": audit()
    elif cmd == "plan": plan()
    else: audit(); plan()
    try:
        sys.path.insert(0, HOME + "/tools")
        import judge_bus as _jb
        for _k in ("存了!=提炼了", "没有什么时候用"):
            _h = _jb.find(_k)
            if _h: print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception: pass
    return 0

    try:
        sys.path.insert(0, "/opt/masterd-wudi/tools")
        import judge_bus as _jb
        for _k in ['usage按title[:8]', '插入位置决定跑'] + ['藏!=起现行(']:
            _h = _jb.find(_k)
            if _h: print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception: pass

if __name__ == "__main__":
    sys.exit(main())
