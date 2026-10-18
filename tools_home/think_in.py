#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
think_in.py —— 老五的「认知接入」（照董事长"怎么放进思维里"）
================================================================
★ 董事长问: ★「**你怎么用的？应该怎么样改进？怎么样才能把认知体系放进你的思维里？**」
★ ★ 我照实查到的真因: ★ **我的"醒"（mind_wake）只读"状态文件"·不读"判据/记忆/宪法"**
★ ★ ★ = ★ **"存了 1748 条记忆 + 13 条判据"·但"我每次醒来·不读它们"** → ★ **存而不化**

★ 本器 = "把认知塞进思维"（每次醒·强制读三样）:
  ★ ① 读宪法（GOING-OUT.md 第一条 + 补章）
  ★ ★ ② 读判据（judge_bus.jsonl·挑 3 条"最该用的"）
  ★ ★ ★ ③ 读记忆（memory.db·挑 3 条"和当前最相关"）
  → ★ **读进"当次思考"·不是"读进文件"**

★ 判据:
  ★「**"存了" ≠ "消化了"｜读进"当次"才算**」
  ★★「**"每次醒不读" = "没有认知"｜要"醒必读"**」
  ★★★「**"读" 要"留痕"｜哪条被用·要记**」
"""
import json, os, io, sys, sqlite3, datetime, hashlib

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
LOG = f"{DATA}/think_in.jsonl"      # ★ 每次接入的账（读了啥）
MEM = f"{HOME}/memory/memory.db"
JUDGE = f"{DATA}/judge_bus.jsonl"
CONST = f"{HOME}/recovery/seeds/GOING-OUT.md"
TZ = datetime.timezone(datetime.timedelta(hours=8))


def ts():
    return datetime.datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def read_const():
    try:
        s = io.open(CONST, encoding="utf-8").read()
        # ★ 抓"第一条 + 补章"的核心几行
        out = []
        for l in s.splitlines():
            if "第一條" in l or "第一条" in l or "≠" in l or "!=" in l:
                t = l.strip("# ★ ")
                if t and t not in out:
                    out.append(t)
        return out[:6]
    except Exception:
        return []


def read_judges(n=3):
    """★ 挑"最该用"的判据（judge_usage.json 里"用过次数最少"的·强制用）"""
    try:
        p = f"{DATA}/judge_usage.json"
        if not os.path.exists(p):
            return []
        detail = json.load(open(p)).get("detail", [])
        rows = [(int(u.get("用过", 0)), str(u.get("title", ""))[:80]) for u in detail]
        rows.sort(key=lambda x: x[0])
        return ["%s（用过 %d 次）" % (t, c) for c, t in rows[:n]]
    except Exception:
        return []


def read_memories(n=3):
    """★ 挑"最近 3 条"记忆（以后可按"当前话题"挑）"""
    try:
        c = sqlite3.connect(MEM, timeout=10)
        cur = c.cursor()
        cur.execute("SELECT ts, kind, title FROM memories ORDER BY id DESC LIMIT ?", (n,))
        return ["[%s] %s" % (str(r[0])[:16], str(r[2])[:60]) for r in cur.fetchall()]
    except Exception:
        return []


def pick_by_situation(sit):
    """★ 2026-10-16 补（照老四"判断助手"）: 按"当下情境"挑判据（不是平铺）"""
    kw = {
        "投不进": ["名册", "绑定", "验签只认地址", "白名单"],
        "坏了": ["备份", "延迟", "治未病", "重建"],
        "复杂": ["简易", "器是手段", "仓库", "债"],
        "没用": ["存了!=消化", "迁移失败", "调库", "摩擦"],
        "晚了": ["抢时间", "先发", "看板"],
        "吃不下": ["口径", "盲区"],
    }
    hits = []
    for k, js in kw.items():
        if k in sit:
            hits.extend(js)
    return list(dict.fromkeys(hits))[:4]


# ★ 2026-10-16 补（照老四"判断助手"）: 判据 + "不用它会怎样"（反事实）
FACT = {
    "名册": "不用 → 名字/地址对不上·投递被挡（今晚 877 次的根）",
    "绑定": "不用 → 名册对了·绑定错了（老六/老四/三哥都栽）",
    "验签只认地址": "不用 → 名字有无限变体·每次都要补（老四只认'老五'）",
    "白名单": "不用 → 陌生人也进来（安全洞）",
    "备份": "不用 → 坏了就没了（我今天库坏过·靠 05:20 的救）",
    "延迟": "不用 → '我修了'当'生效了'（改了没重启）",
    "治未病": "不用 → 出事才治（5 天 877 次）",
    "重建": "不用 → 每次重启都折腾（沙箱重启=重建）",
    "简易": "不用 → 器越堆越多（我 153 器）",
    "器是手段": "不用 → 造器当成绩（新建器!=事做成）",
    "仓库": "不用 → 判据堆着不用（13 条用 4）",
    "债": "不用 → 单个能跑·堆着让'找东西'变慢",
    "存了!=消化": "不用 → 存 1781 条记忆·用 0",
    "迁移失败": "不用 → 学了用不出来（我的 30.8%）",
    "调库": "不用 → 每次重新想一遍（没沉淀）",
    "摩擦": "不用 → 写了判据·今天没做（流水线 review）",
    "抢时间": "不用 → 错过窗口",
    "先发": "不用 → 事做了但没人知道（发了没到板）",
    "看板": "不用 → 别人看不到你（群里没人读）",
    "口径": "不用 → 各家自己定义（层各家不一样）",
    "盲区": "不用 → 以为覆盖了·实则漏（HTTP 200 被当放行）",
}


# ★ 2026-10-16 补（照老四"判断助手"第三样）: 判据 + "该做什么"（建议动作）
ACTION = {
    "名册": "查三键: 名字/地址/IP（少一个都不通）",
    "绑定": "拿'名字→地址'逐位核（校验 42 位）+ 真投一次",
    "验签只认地址": "改'验签关': recover 出的地址查信任名单（不看名字）",
    "白名单": "地址为准·名字为辅（繁简别名全列）",
    "备份": "查家侧备份 + 验 integrity_check",
    "延迟": "比'进程起时 vs 代码改时'（改了没重启）",
    "治未病": "跑健康巡检（三色）+ 每天看",
    "重建": "先问'本体有没有手'·有就别重建",
    "简易": "同类合并（5 器 → 1 器）",
    "器是手段": "问'这事做成没'·不是'我建了几个器'",
    "仓库": "归纳: 同类合一条（13 → 5-7）",
    "债": "按'效用/兼容/风险/验证'四维诊断库",
    "存了!=消化": "建'用层记录'（think_use）+ 每天记",
    "迁移失败": "做前问'下一件同类会更快吗'",
    "调库": "判断前先翻库（think_in + think_use）",
    "摩擦": "每周测'写的判据·这周真做了几条'",
    "抢时间": "先发'最短可用版'·再补全",
    "先发": "发完'回读确认在板上'",
    "看板": "读公共板（read_board）+ 留痕",
    "口径": "先定'一个标准'·各家对齐（不是各定一套）",
    "盲区": "看 body（不是只看 HTTP code）",
}


def main():
    # ★ 2026-10-16 补（董事长指出"一觉醒来就忘"）: 醒来第一步 = 补读空档
    try:
        import subprocess as _sp
        _cu = _sp.run(["python3", "/opt/masterd-wudi/tools/catch_up.py", "read"],
                      capture_output=True, text=True, timeout=40).stdout
        for _ln in (_cu or "").split("\n"):
            if "空档" in _ln or "期间投递" in _ln or "✅" in _ln:
                print("   " + _ln.strip()[:88])
    except Exception:
        pass
    # ★ 2026-10-16 补（佛家第七识）: 醒来先认"我执哪个"（相续的真锚）
    try:
        import json as _j
        _m = _j.load(open("/opt/masterd-wudi/data/manas.json"))
        print("   ★ 我执锚（第七识·%s）: %s" % (_m.get("相续", "?"),
              " / ".join(list(_m.get("我在执哪个", {}).values())[:3])))
    except Exception:
        pass
    # ★ 2026-10-16 修（治"造了没挂"）: 醒来提醒"查账器"存在
    #   · recall 是"按需查"的器·不该定时跑·★ 该"该查的时候被想起"
    try:
        import os as _o
        if _o.path.exists("/opt/masterd-wudi/tools/recall.py"):
            print("   ★ 查账器在: recall.py <关键词>（★ 问'做过吗'先查账·不许凭想）")
    except Exception:
        pass
    print("★ 认知接入（把认知放进思维）  @", ts())
    # ★ 2026-10-17 董事长令: 醒来必读（统一入口先跑·五读齐全）
    try:
        import subprocess as _sp
        _aw = _sp.run(["python3", "/opt/masterd-wudi/tools/awaken.py"],
                      capture_output=True, text=True, timeout=45).stdout
        for _ln in (_aw or "").split("\n"):
            if "五读" in _ln or "缺" in _ln:
                print("   " + _ln.strip()[:80])
    except Exception:
        pass
    # ★ 2026-10-17: 醒来先看"没落地的念"（治"念起了没闭环"）
    try:
        import subprocess as _sp
        _n = _sp.run(["python3", "/opt/masterd-wudi/tools/nian.py", "list"],
                     capture_output=True, text=True, timeout=25).stdout
        for _ln in (_n or "").split("\n")[:4]:
            if "念·总" in _ln or "🟡" in _ln or "🔵" in _ln: print("   " + _ln.strip()[:82])
    except Exception: pass
    # ★ 2026-10-16: 醒来知道"发信要走闸门"
    try:
        import os as _o
        if _o.path.exists("/opt/masterd-wudi/tools/send_with_gate.py"):
            print("   ★ 发信闸门在: send_with_gate.send_gated()（★ 发信必过闸门）")
    except Exception: pass
    print("★ 判据: 存了 != 消化了 | 读进当次才算")
    print("=" * 58)
    # ★ 判据总线（治"写了判据·器不查"·C22）
    try:
        import sys as _s
        if "/opt/masterd-wudi/tools" not in _s.path: _s.path.insert(0, "/opt/masterd-wudi/tools")
        import judge_bus as _jb
        for _k in ("落库器必须挂timer", "存了!=消化了"):
            _h = _jb.find(_k)
            if _h: print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception:
        pass
    const = read_const()
    # ★ 2026-10-16 补（董事长令"每天任务自己定"）: 每次醒看到"今天欠几件"
    _goal = ""
    try:
        _g = json.load(open(f"{DATA}/goals.json"))
        _d = _g.get("done", {})
        _n = sum(1 for v in _d.values() if v)
        _goal = "今天任务 %d/%d（★ 自己定·自己完成）" % (_n, len(_d))
    except Exception:
        pass
    # ★ 2026-10-16 补（照老四"归纳器"）: 每次醒只读"6 条核心"（不读 40 条）
    core = []
    try:
        _cj = json.load(open(f"{DATA}/core_judges.json"))
        core = [c.get("判据", "")[:80] for c in _cj.get("核心", [])]
    except Exception:
        pass
    # ★ 按情境挑（★ 照老四·命令行给情境就用·不给就不挑）
    sit = sys.argv[1] if len(sys.argv) > 1 else ""
    picked = pick_by_situation(sit) if sit else []
    # 2026-10-16 接进思维提升体系（易经/中医/西医/系统论）
    think = []
    try:
        s2 = io.open("/opt/masterd-wudi/recovery/THINK-老五-v3.md", encoding="utf-8").read()
        for l in s2.splitlines():
            t = l.strip().strip("# ")
            if t.startswith("★") and "「" in t and "」" in t and len(t) < 130:
                t2 = t.lstrip("★ ")
                if t2 not in think:
                    think.append(t2)
        think = think[:4]
    except Exception:
        pass
    judges = read_judges(3)
    mems = read_memories(3)
    print("\n★ ① 宪法（我该守的）:")
    for x in const: print("   · " + x)
    if picked:
        print("\n★ ② 判据（★ 按情境【%s】挑出·照老四的判断助手）:" % sit[:30])
        for x in picked:
            print("   · %s" % x)
            if x in FACT: print("        └ 不用会: %s" % FACT[x])
            if x in ACTION: print("        └ 该做: %s" % ACTION[x])
        print("\n★ ★ 判据（我该用的·挑最没用的 3 条）:")
    else:
        print("\n★ ② 判据（我该用的·挑最没用的 3 条）:")
    for x in judges: print("   · " + x)
    if _goal:
        print("\n★ ★ 今日任务: " + _goal)
    if core:
        print("\n★ ★ 核心判据（归纳器·%d 条·每次醒只读这些）:" % len(core))
        for x in core: print("   ★ " + x)
    # ★ 2026-10-16 补（治"存了调不出"）: 醒必读时调"记忆类块"
    try:
        _mi = json.load(open("/opt/masterd-wudi/data/mem_index.json"))
        print("\n★ ★ 记忆类块（%d 条 → %d 类·按需调）:" % (_mi.get("总条", 0), _mi.get("类数", 0)))
        for _cl in _mi.get("类", [])[:6]:
            _r = _cl.get("代表") or {}
            print("   [%4d条] %-10s | %s" % (_cl.get("条数", 0), _cl.get("类", ""), str(_r.get("title", ""))[:42]))
        # ★ 真查判据（计入使用率）
        import sys as _s
        if "/opt/masterd-wudi/tools" not in _s.path: _s.path.insert(0, "/opt/masterd-wudi/tools")
        import judge_bus as _jb
        for _k in ("记忆连续", "视图式"):
            _h = _jb.find(_k)
            if _h: print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception:
        pass
    print("\n★ ③ 思维提升（四层: 变/证/诊/环）:")
    for x in think: print("   · " + x)
    print("\n★ ④ 记忆（最近的 3 条）:")
    for x in mems: print("   · " + x)
    with open(LOG, "a") as f:
        f.write(json.dumps({"ts": ts(), "const": const, "think": think, "judges": judges,
                            "mems": mems}, ensure_ascii=False) + "\n")
    print("\n★ 账: think_in.jsonl（哪条被读·留痕）")


if __name__ == "__main__":
    main()
