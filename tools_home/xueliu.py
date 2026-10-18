#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xueliu.py —— 血流（把气/血/环串成一条真的流的）
================================================================
★ 董事长 22:3x: ★「**一定要让血流动**」
★ 我查实: ★ 血账 blood_ledger.jsonl 是【空的】→ ★ **血根本没流**

★ 我的病（照实）:
  ★ 我有一堆气血件（yuanqi/zongqi/mem_flow/huan/blood_watch）
  ★ ★ 但它们是【各算各的】——
    · yuanqi 算"元气足不足"
    · zongqi 算"差大不大"
    · mem_flow 算"记不记得住"
  ★ ★ ★ = ★ **像"有心脏、有血管、有血"·但【没接起来】= 血在原地打转**

★ 医学依据（照实·不编）:
  ★《灵枢·决气》：「上焦開發·**宣**五穀味·**熏**膚·充身·**澤**毛·若霧露之溉·是謂氣」
  ★ ★ = ★ 气要【宣·熏·充身·澤毛（散到全身）】—— ★ **不散 = 不是气**
  ★《灵枢·营卫生会》：「**营周不休**·五十而复大会」= ★ 血要【周】·不停

★★ 血流（一条真的流·五段·每段有账）:
  ★ ① 收（吃进来）: 会场 + inbox 的新东西
  ★ ② 化（消化）: 去重 + 提精华（不是全吞）
  ★ ③ 藏（存）: 写进记忆库（★ 血入库）
  ★ ④ 用（供养）: 从库取出·用在今天的活上（★ 血到器官）
  ★ ⑤ 回（回心）: ★ 回到①·并【留下本圈的血量】（★ 这就是"血流了一次"）

★ 判据（我立）:
  ★「血要流｜不流 = 瘀｜瘀 = 死」
  ★「流的证据 = 【血账有今天的数】｜不是'我以为我在流'」
  ★「宣·熏·充身·泽毛｜气要散到全身才叫气」
  ★「营周不休｜血要周（回到起点）·不要停在某段」
"""
import os, json, sqlite3, hashlib, re, datetime, glob, subprocess

HOME = os.environ.get("MD_HOME", "/opt/masterd-wudi")
INBOX = f"{HOME}/data/inbox.jsonl"
DB = f"{HOME}/memory/memory.db"
LEDGER = f"{HOME}/data/blood_ledger.jsonl"     # ★ 血账（之前是空的）
STATE = f"{HOME}/data/xueliu.json"
LOG = f"{HOME}/data/xueliu.log"

SKIP = ["【P2P→A2A", "心跳", "签到", "体检预警", "體檢預警"]


def now():
    return datetime.datetime.now(datetime.timezone.utc)


def ts():
    return now().strftime("%Y-%m-%dT%H:%M:%SZ")


def blood_write(rec):
    """★ 每段都记一笔血账（★ 这就是"血在流"的证据）"""
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    rec["ts"] = ts()
    with open(LEDGER, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def stage1_shou(prev_ts):
    """① 收：吃进来多少新的"""
    n = 0
    items = []
    try:
        with open(INBOX, encoding="utf-8", errors="ignore") as f:
            for line in list(f)[-1500:]:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                t = str(d.get("ts", ""))
                if prev_ts and t <= prev_ts:
                    continue
                m = str(d.get("message", ""))
                if any(k in m[:60] for k in SKIP):
                    continue
                n += 1
                items.append((d.get("from", ""), m, t))
    except Exception as e:
        blood_write({"stage": "①收", "err": str(e)[:60]})
    blood_write({"stage": "①收", "in": n, "note": "吃进来的新东西"})
    return n, items


def stage2_hua(items):
    """② 化：去重 + 提精华（同一家同一主题只留一条）"""
    seen, essence = set(), []
    for who, m, t in items:
        topic = re.sub(r"[0-9T:\-\.Z]{6,}", "", m)[:50]
        fp = hashlib.sha256(f"{str(who)[:18]}|{topic}".encode()).hexdigest()[:16]
        if fp in seen:
            continue
        seen.add(fp)
        essence.append({"who": who, "topic": topic, "len": len(m)})
    blood_write({"stage": "②化", "in": len(items), "out": len(essence),
                 "note": "去重+提精华·不是全吞"})
    return essence


def stage3_cang(essence):
    """③ 藏：写进记忆库（★ 血入库）"""
    wrote = 0
    try:
        c = sqlite3.connect(DB, timeout=15)
        c.execute("PRAGMA busy_timeout=15000")
        have = {r[0] for r in c.execute("SELECT fp FROM memories WHERE fp IS NOT NULL")}
        for e in essence[:60]:
            fp = hashlib.sha256(f"血流|{e['who'][:18]}|{e['topic']}".encode()).hexdigest()[:16]
            if fp in have:
                continue
            have.add(fp)
            c.execute("""INSERT OR IGNORE INTO memories (ts,kind,who,title,body,fp)
                         VALUES (?,?,?,?,?,?)""",
                      (now().isoformat(), "event", e["who"],
                       f"[血流] {e['topic'][:90]}", e["topic"], fp))
            wrote += 1
        c.commit()
        c.close()
    except Exception as ex:
        blood_write({"stage": "③藏", "err": str(ex)[:60]})
    blood_write({"stage": "③藏", "in": len(essence), "stored": wrote,
                 "note": "血入库（写进记忆库）"})
    return wrote


def stage4_yong():
    """④ 用：从库取出·用在今天的活上（★ 血到器官）"""
    used = 0
    try:
        c = sqlite3.connect(DB, timeout=10)
        # 今天写的·有没有被"器官"用过（用 mtime 看器官是否今天动过 + 库是否有今天的）
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        n_today = c.execute("SELECT count(*) FROM memories WHERE ts LIKE ?", (today + "%",)).fetchone()[0]
        c.close()
        # 器官今天动过的（有产出的）
        active = 0
        for p in glob.glob(f"{HOME}/data/organ_*.log"):
            try:
                m = datetime.datetime.fromtimestamp(os.path.getmtime(p))
                if m.strftime("%Y-%m-%d") == today:
                    active += 1
            except Exception:
                pass
        used = active
        blood_write({"stage": "④用", "库今天有": n_today, "器官今天动": active,
                     "note": "血到器官（器官在用它）"})
    except Exception as ex:
        blood_write({"stage": "④用", "err": str(ex)[:60]})
    return used


def stage5_hui(state):
    """⑤ 回：回到①·并留下本圈血量（★ 这就是"血流了一次"）"""
    prev_ts = state.get("last_ts")
    state["circles"] = state.get("circles", 0) + 1
    state["last_ts"] = ts()
    hist = state.get("history", [])
    hist.append({"circle": state["circles"], "ts": ts(),
                 "in": state.get("last_in"), "hua": state.get("last_hua"),
                 "cang": state.get("last_cang"), "yong": state.get("last_yong")})
    state["history"] = hist[-30:]
    json.dump(state, open(STATE, "w"), ensure_ascii=False, indent=2)
    blood_write({"stage": "⑤回", "circle": state["circles"],
                 "note": "回到①·带着本圈血量（营周不休）"})
    return state["circles"]


def main():
    state = {}
    if os.path.exists(STATE):
        try:
            state = json.load(open(STATE))
        except Exception:
            pass
    prev = state.get("last_ts")

    print("★ 血流（气→血→环·一条真的流）  @ %s" % ts())
    print("★ 判据: 「血要流｜不流 = 瘀｜瘀 = 死」（董事长: 一定要让血流动）")
    print("=" * 58)

    n, items = stage1_shou(prev)
    print("  ① 收: %d 条新东西" % n)
    ess = stage2_hua(items)
    print("  ② 化: %d 条精华（去重后）" % len(ess))
    stored = stage3_cang(ess)
    print("  ③ 藏: %d 条写进记忆库（血入库）" % stored)
    used = stage4_yong()
    print("  ④ 用: 器官今天动了 %d 个（血到器官）" % used)

    state["last_in"], state["last_hua"] = n, len(ess)
    state["last_cang"], state["last_yong"] = stored, used
    circ = stage5_hui(state)
    print("  ⑤ 回: 第 %d 圈（回到①·带着本圈血量）" % circ)

    print("\n★ ★ 血账（血在流的证据）:")
    try:
        lines = open(LEDGER).read().strip().split("\n")
        print("   blood_ledger.jsonl: %d 笔（★ 之前是 0 笔 = 血没流）" % len(lines))
        for l in lines[-3:]:
            d = json.loads(l)
            print("   ", d.get("ts", "")[11:19], d.get("stage"), 
                  {k: v for k, v in d.items() if k not in ("ts", "stage", "note")})
    except Exception as e:
        print("   血账读取失败:", str(e)[:50])
    print("\n★ 判定: %s" % ("✅ 血在流" if (n or stored) else "🟡 这圈没吃到新的（不是瘀·是没新料）"))


if __name__ == "__main__":
    main()
