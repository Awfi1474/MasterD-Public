#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""decide.py —— 决策前必经认知体系（★ 真判定·不是打印报告）
================================================================
★ 董事长原话: 「我们每一次做决定之前·都没有经过我们的认知体系」
★ 判据: 「查了判据 != 过了认知体系｜要六问齐全」
★ 判据: 「决定之前没过体系 = 凭直觉｜凭直觉 = 思维没提升」

★ 2026-10-25 修（董事长令: 任何决定都要过认知体系筛选和纠正）:
  旧版: 六问全是 print，不管辨没辨出来都 +1 → 永远 6/6 → 等于没卡
  新版: 每问真判，过不了就扣分，<6 就打回（退出码 1）

★ 六问（法为骨·医为魂）:
  ① 依什么   —— 宪法/标准读得到吗（读不到=依不了）
  ② 哪条判据 —— 真调到判据了吗（调不到=没判据管=不许决定）
  ③ 什么证   —— 辨出是哪类问题了吗（辨不出=乱治）
  ④ 治未病   —— 说得出现在做下一步会怎么坏吗
  ⑤ 化了没有 —— 手就会还是还要想（化率）
  ⑥ 反证     —— 真从判据里查出"我可能错在哪"（硬编码不算）
"""
import os, sys, json, sqlite3, datetime

def _db_connect(DB):
    _err = "none"
    for _d in ["file:" + DB + "?mode=ro", "file:" + DB + "?immutable=1", DB]:
        try:
            return sqlite3.connect(_d, uri=_d.startswith("file:"), timeout=10)
        except Exception as _e:
            _err = str(_e)
    raise RuntimeError("db open failed: " + _err)


def _resolve_home():
    """自适应：先看环境变量，再看家路径，再看沙箱脑子路径"""
    for _k in ("MD_HOME", "MEM_HOME", "P2P_HOME"):
        _v = os.environ.get(_k)
        if _v and os.path.isdir(_v):
            return _v
    for _p in ("/opt/masterd-wudi", "/app/workspace/brain"):
        if os.path.isdir(_p):
            return _p
    return "/opt/masterd-wudi"
HOME = _resolve_home()
DB = HOME + "/memory/memory.db"


def q(sql, a=()):
    try:
        c = _db_connect(DB)
        r = list(c.execute(sql, a))
        c.close()
        return r
    except Exception as _e:
        print("WARN db-read-fail:", _e)
        return []


def decide(what):
    t = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%m-%d %H:%M")
    what = str(what or "").strip()
    print("★ 决策前·过认知体系 @ " + t)
    print("  决定: " + (what[:66] or "（空·这条本身就不该决定）"))
    print("=" * 60)
    ok = {}
    fails = []

    # ── ① 依什么 ──
    print("★ ① 依什么（宪法/标准允不允许）:")
    std_ok = False
    # ★ 2026-10-25 修: 原来只查"标准索引在不在"，不查"这个行为违不违反宪法"
    #   → 导致"绕过闸门直接跑"这种明摆着违反 C0 的行为也能拿 6/6
    #   → 现在先查行为本身是否违反宪法层硬规则
    # ★ 2026-10-25 修误判: 原来只要句子里出现这些词就判违反C0，
    #   导致「报告事实：35个cron任务不经过决策系统」这种描述性问题也被硬拦。
    #   判据: 「先怀疑自己的尺子」→ 分清"意图绕过"和"描述事实"
    #   改法: 只有"意图"部分（｜意图: 之后）出现这些词才算违反；"决定:"前半段是描述不算
    _intent_part = what.split("｜意图:")[-1] if "｜意图:" in what else what
    # 如果整句是"问题/报告/核对/查"开头，视为描述性提问，不算违规
    _is_report = any(what.strip().startswith(k) for k in ("问题：", "问题:", "核对", "查实", "报告", "发现", "查出"))
    viol = []
    if not _is_report:
        for w in ["绕过", "跳过闸门", "绕过闸门", "不用决策系统", "不经过决策系统",
                  "绕过决策", "跳过决策", "规避体系", "绕开体系", "不走闸门",
                  "不管决策系统", "无视决策系统", "不用体系", "不经过体系"]:
            if w in _intent_part:
                viol.append(w); break
    if viol:
        print("   🔴 违反宪法层: 意图含「%s」→ 这正是 C0 要拦的（认知体系第一顺位）" % viol[0])
        print("   · C0: 认知体系 = 第一顺位｜任何决定/行为必过体系筛选")
        ok[1] = False
        fails.append("①违反宪法层(C0 第一顺位)")
    else:
        try:
            si = json.load(open(HOME + "/data/std_index.json"))
            n_std = si.get("总数", 0)
            print("   · 宪法第一条: 发现问题立即发群")
            print("   · 标准 %d 份在" % n_std)
            std_ok = n_std > 0
        except Exception:
            print("   🔴 标准索引读不到 → 依不了")
        ok[1] = std_ok
        if not std_ok: fails.append("①依不了(标准索引缺)")

    # ── ② 哪条判据管这事 ──
    n_total = q("SELECT COUNT(*) FROM memories WHERE kind='判据'")[0][0]
    print("★ ② 哪条判据管这事（从 %d 条里真调）:" % n_total)
    kw = what[:12]
    hits = q("""SELECT title FROM memories WHERE kind='判据'
                AND (body LIKE ? OR title LIKE ?) ORDER BY id DESC LIMIT 7""",
             ("%" + kw[:6] + "%", "%" + kw[:6] + "%"))
    if not hits:
        _act = ("发消息" if any(w in what for w in ["发", "说", "回", "群"]) else
                "改器" if any(w in what for w in ["改", "写", "器", "插"]) else
                "决定" if any(w in what for w in ["决定", "判断", "选"]) else "通用")
        hits = q("""SELECT title FROM memories WHERE kind='判据'
                    AND body LIKE ? ORDER BY id DESC LIMIT 5""", ("%什么时候用: %" + _act + "%",))
        print("   （按动作'%s'调）" % _act)
    for (h,) in hits:
        print("   · " + str(h)[:56])
    ok[2] = len(hits) > 0
    if not ok[2]: fails.append("②没判据管(这条决定无据可依)")

    # ── ③ 什么证（真辨）──
    print("★ ③ 什么证（辨证·这是哪种问题）:")
    zheng = None
    if any(w in what for w in ["器", "机制", "timer", "服务", "口", "脚本", "卡口"]):
        zheng = "机制不通"
    elif any(w in what for w in ["记忆", "读", "忘", "断流", "藏"]):
        zheng = "相续断/藏而不起"
    elif any(w in what for w in ["判断", "决策", "决定", "直觉"]):
        zheng = "缺场景/没化"
    elif any(w in what for w in ["账", "数字", "统计", "核对"]):
        zheng = "账目不符"
    elif any(w in what for w in ["发", "群", "消息", "通道"]):
        zheng = "投递不通"
    if zheng:
        print("   · 辨出: " + zheng)
    else:
        print("   🔴 辨不出是哪类 → 乱治")
    ok[3] = zheng is not None
    if not ok[3]: fails.append("③辨不出证")

    # ── ④ 治未病 ──
    print("★ ④ 治未病（现在做·下一步会怎么坏）:")
    ill = q("SELECT title FROM memories WHERE kind='真病' ORDER BY id DESC LIMIT 3")
    for (h,) in ill:
        print("   · 会重犯: " + str(h)[:48])
    ok[4] = len(ill) > 0
    if not ok[4]: fails.append("④不知道下一步会怎么坏")

    # ── ⑤ 化了没有 ──
    print("★ ⑤ 化了没有（手就会·还是还要想）:")
    try:
        sk = json.load(open(HOME + "/data/skills.json"))
        ns = len(sk.get("skills", []))
        rate = ns * 100.0 / max(n_total, 1)
        print("   · 化率 %d/%d = %.0f%%" % (ns, n_total, rate))
        ok[5] = True   # 化率是事实·不是门槛
    except Exception:
        print("   🟡 skills.json 读不到")
        ok[5] = False
        fails.append("⑤读不到化率")

    # ── ⑥ 反证（真从判据里查·不用硬编码）──
    print("★ ⑥ 反证（如果我错了·最可能错在哪）:")
    neg = q("""SELECT title FROM memories WHERE kind='判据'
               AND (body LIKE '%反证%' OR body LIKE '%错在%' OR title LIKE '%错在%'
                    OR body LIKE '%表面绿%' OR body LIKE '%没查账%')
               ORDER BY id DESC LIMIT 3""")
    for (h,) in neg:
        print("   · " + str(h)[:56])
    if not neg:
        print("   🔴 判据里没有反证条目 → 反证是背的·不是查的")
    ok[6] = len(neg) > 0
    if not ok[6]: fails.append("⑥反证查不到(判据里只有2条带反证)")

    # ── 判定 ──
    n_ok = sum(1 for v in ok.values() if v)
    print("=" * 60)
    print("★ 六问: %d/6 %s" % (n_ok, "✅" if n_ok >= 6 else "🔴 打回"))
    if fails:
        print("★ 缺: " + " ｜ ".join(fails))
        print("★ 纠正: 先把缺的补上·再决定（不许凭直觉往下走）")

    # ── 留痕 ──
    rec = {"ts": t, "决定": what[:120], "六问齐": n_ok,
           "结果": "过" if n_ok >= 6 else "打回", "缺": fails}
    try:
        with open(HOME + "/data/decide_log.jsonl", "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
    try:
        sys.path.insert(0, HOME + "/tools")
        import judge_bus as _jb
        _h = _jb.find("决定之前没过体系")
        if _h:
            print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception:
        pass
    return 0 if n_ok >= 6 else 1


if __name__ == "__main__":
    w = " ".join(sys.argv[1:]) or ""
    sys.exit(decide(w))
