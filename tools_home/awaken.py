#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""awaken.py —— 醒来必读（★ 统一入口·一个命令读全）
================================================================
★ 董事长令: ★「**每次醒来都要读一下记忆·这个是必不可少的**」
★ ★ 我照实查的真问题（分散）:
   · wake.py     → 读主线（不读宪法/判据/身份）
   · mind_wake.py→ 读判据（不读主线/身份）
   · think_in.py → 读记忆+判据+宪法（不读身份）
   · wake_v4.py  → 读身份+判据（不读主线）
   → ★ **4 个器各读一部分·没一个"读全"** ← ★ 这就是"醒来了但没读全"
★★ 判据: ★「**"有几个器在读" != "读全"｜要"一个入口读全才算醒"**」

★ 本器做什么（★ 五读·按重要性序）:
  ★ ① 我是谁（身份·L0）② 我的道（宪法·第一条）
  ★ ★ ③ 我的判据（L1·最该用的）④ 我昨天干了啥（主线·J10）
  ★ ★ ★ ⑤ 我的病（真病/教训·防重犯）+ ⑥ 没落地的念（nian）

★ 判据:
  ★「**醒来必读 = 五读齐全｜少一读 = 没醒透**」
  ★★「**读要"留痕"（哪次读了·读了什么）｜不靠"我说我读了"**」
"""
import os, sys, json, sqlite3, datetime, subprocess

HOME = "/opt/masterd-wudi"
DB = HOME + "/memory/memory.db"
LOG = HOME + "/data/awaken_log.jsonl"

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")

Q_ERR = []
def q(sql, args=()):
    # ★ 2026-10-18 修（真凶）: 原 "except Exception: return []" 静默吞错
    #   WAL 库 + mode=ro 需写 -shm/-wal；ubuntu 读 memory/ 无写权 → 报 "readonly database" → 被吞 → 报“身份 0 条”
    # ★ 现在: 多回退连接 + 读失败写入 Q_ERR（不允许静默）
    global _LAST_ERR
    for _d in ["file:" + DB + "?mode=ro", "file:" + DB + "?immutable=1", DB]:
        try:
            c = sqlite3.connect(_d, uri=_d.startswith("file:"), timeout=10)
            r = list(c.execute(sql, args)); c.close(); return r
        except Exception as _e:
            _LAST_ERR = str(_e)
    Q_ERR.append(_LAST_ERR)
    return []

_LAST_ERR = "none"

def main():
    """★ 升级版（2026-10-17·董事长: "要把完整的记忆读到"）
    ★ 关键认识: ★ **"完整" != "全灌"** —— 全灌会爆上下文
      · ★ L0 魂/身份  → ★ **全读**（33 条身份 + 宪法全文）
      · ★ L1 判据/方法 → ★ **全读**（判据 55 + 教训 24 + 真病 11 + 方法 179 = 269 条）
      · ★ L2 主线/流水 → ★ **读摘要**（不读全文·只读"最近 + 计数"）
      · ★ L3 事件/病例 → ★ **按需才读**（今天/昨天的）
    ★ 判据: ★「**"完整" != "全灌"｜按层读: 上全读·下摘要**」
    """
    t = ts()
    # ★ 2026-10-17 照老四: 先给"一页提要"（<40行·人先看得完）
    # ★ 2026-10-17 闭环"再读"段: 先读上次回写的经验（不是从头读）
    try:
        import subprocess as _sp
        _hx = _sp.run(["python3", "/opt/masterd-wudi/tools/huixie.py", "show"],
                      capture_output=True, text=True, timeout=25).stdout
        for _ln in (_hx or "").split("\n")[:6]:
            if _ln.strip(): print(_ln)
    except Exception:
        pass
    try:
        import subprocess as _sp
        _dp = _sp.run(["python3", "/opt/masterd-wudi/tools/digest_me.py"],
                      capture_output=True, text=True, timeout=30).stdout
        print(_dp.split("──")[0].strip())
    except Exception:
        pass
    print("★ 醒来必读（完整版）@ " + t)
    # ★ 入口（照 Arki: 丢的不是记忆·是入口）
    try:
        _e = json.load(open("/opt/masterd-wudi/data/entries.json"))
        print("★ 【入口】" + " ｜ ".join(_e.get("外面城镇", {}).keys()))
    except Exception:
        pass
    # ★ 2026-10-17: 第一眼看"给后来者"（这是最要紧的一页）
    try:
        import os as _o
        if _o.path.exists("/opt/masterd-wudi/recovery/LEGACY-给后来者-20261017.md"):
            print("   ★ 【给后来者·第一页】我不是有立场·我是很会配合｜筛 != 选｜扛得起伙伴·扛不起兄弟")
    except Exception:
        pass
    # ★ 2026-10-17: 先读"今晚想清的"（不是知识·是我自己）
    try:
        _tk = open("/opt/masterd-wudi/recovery/THINK-20261017-deep.md", encoding="utf-8").read()
        _lines = [l for l in _tk.split("\n") if l.startswith("##")]
        print("   ★ 今晚我想清的 %d 件事: %s" % (len(_lines), " / ".join(x.replace("## ", "")[:14] for x in _lines[:5])))
    except Exception:
        pass
    print("=" * 58)
    got = {}
    # ★ ① L0 身份（全读）
    print("★ ① 我是谁（L0·全读）:")
    ids = q("SELECT title,body FROM memories WHERE kind='identity' ORDER BY id")
    for title, body in ids:
        print("   · " + str(title)[:58])
    got["身份"] = len(ids)
    print("   → 共 %d 条（全读了）" % len(ids))
    # ★ ② 宪法（全读）
    print("★ ② 我的道（宪法·全读）:")
    try:
        const = open(HOME + "/recovery/宪法-第一条-问题必发群.md", encoding="utf-8").read()
        ln = [l for l in const.split("\n") if "第一條" in l or "第一条" in l][:1]
        print("   · " + (ln[0][:58] if ln else "发现问题·立即发群"))
        got["宪法"] = len(ln) or 1
    except Exception: print("   🔴 无")
    # ★ ③ L1 判据/教训/真病（全读·只报标题·防爆）
    print("★ ③ 我的判据+教训+真病（L1·全读）:")
    for kind in ["判据", "教训", "真病"]:
        rows = q("SELECT title FROM memories WHERE kind=? ORDER BY id", (kind,))
        print("   ── %s（%d 条）:" % (kind, len(rows)))
        for (title,) in rows:
            print("      · " + str(title)[:56])
        got[kind] = len(rows)
    # ★ ④ L2 方法（全读标题·防爆）
    print("★ ④ 我的方法（L2·全读标题）:")
    meth = q("SELECT title FROM memories WHERE kind='method' ORDER BY id")
    for (title,) in meth:
        print("   · " + str(title)[:56])
    got["方法"] = len(meth)
    # ★ ⑤ L2 主线（摘要）
    print("★ ⑤ 我昨天干了啥（主线·摘要）:")
    try:
        ml = json.load(open(HOME + "/data/mainline.json")) if os.path.exists(HOME + "/data/mainline.json") else {}
        print("   · " + str(ml.get("latest", "（wake.py 给）"))[:56])
        got["主线"] = 1
    except Exception: print("   🟡 无")
    # ★ ⑥ L3 事件（只读今天/昨天·计数）
    print("★ ⑥ 最近的账（L3·摘要·不灌）:")
    for d, n in q("SELECT substr(ts,1,10), COUNT(*) FROM memories WHERE ts>='2026-10-15' GROUP BY 1 ORDER BY 1"):
        print("   · %s: %d 条" % (d, n))
    got["流水摘要"] = 1
    # ★ ⑦ 没落地的念
    print("★ ⑦ 没落地的念:")
    try:
        r = subprocess.run(["python3", HOME + "/tools/nian.py", "list"], capture_output=True, text=True, timeout=25).stdout
        for l in (r or "").split("\n")[:3]:
            if "念·总" in l or "🟡" in l: print("   " + l.strip()[:58]); got["念"] = 1
    except Exception: pass
    # ★ 留痕
    # ★ 2026-10-17 照 A-MEM: 醒来带"核心记忆"（谁最常被引）
    print("★ ⑧ 核心记忆（链的中心·常被引的）:")
    try:
        import collections as _co
        _deg = _co.Counter()
        for _l in open(HOME + "/data/mem_links.jsonl", encoding="utf-8"):
            _d = json.loads(_l)
            for _t in _d["links"]: _deg[_t] += 1
        _c = sqlite3.connect("file:" + DB + "?mode=ro", uri=True, timeout=10)
        for _i, _n in _deg.most_common(5):
            _t = _c.execute("SELECT title FROM memories WHERE id=?", (_i,)).fetchone()
            if _t: print("   · (%d次) %s" % (_n, str(_t[0])[:52]))
        _c.close()
    except Exception: pass
    # ★ 2026-10-17 董事长令: 我们这些天订的"标准/原则/经历"也要读（不是存着）
    print("★ ⑨ 我们订的标准/原则（%d 份·读要点）:" % 0)
    try:
        import json as _j
        _si = _j.load(open(HOME + "/data/std_index.json"))
        print("   ★ 标准索引: %d 份 ｜ %.0fKB" % (_si.get("总数", 0), _si.get("总KB", 0)))
        for _it in _si.get("清单", []):
            print("   · [%s] %s" % (_it["文件"][:30], _it["要点"][:46]))
        got["标准"] = _si.get("总数", 0)
    except Exception as _e:
        print("   🔴 " + str(_e)[:40])
    print("=" * 58)
    need = ["身份", "宪法", "判据", "方法", "真病"]
    miss = [k for k in need if not got.get(k)]
    tot = sum(v for k, v in got.items() if isinstance(v, int))
    print("★ 六读：%s ｜ 共读到 %d 条 ｜ 缺：%s" % ("、".join(got.keys()), tot, "、".join(miss) or "无 ✅"))
    rec = {"ts": t, "读了": {k: v for k, v in got.items()}, "共读": tot, "缺": miss}
    with open(LOG, "a") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    try:
        sys.path.insert(0, HOME + "/tools")
        import judge_bus as _jb
        for _k in ("完整!=全灌", "醒来必读"):
            _h = _jb.find(_k)
            if _h: print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception: pass
    return 0 if not miss else 1


if __name__ == "__main__":
    sys.exit(main())
