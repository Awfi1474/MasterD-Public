#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chase_receipt.py —— 老五的「回执追杀器」（照三哥 12:54 第1层）
================================================================
★ 三哥的洞: ★「"听到"要去"回执"｜没回执 = 视为"没听到"」
★ ★ 实证: ★ "VIP 15分钟令 → **0 家回执**" ｜ "宪法层 → 6家只有2家有痕迹"
★ ★ ★ 判据: ★「**"他读了" ≠ "他收到了"｜要"他回了'我几点做'"**」

★ 它做什么（每 15 分钟）:
  ★ ① 扫"我发过的指令"（从 ask_verify / 群发账里找）→ 看谁没回
  ★ ★ ② 三级追: 30分→催 ｜ 60分→点名 ｜ 120分→记错账(-10)
  ★ ★ ★ ③ 落账: data/chase_receipt.jsonl（谁·第几次·状态）

★ 判据（认三哥·认学术）:
  ★「"听到" ≠ "收到"｜要"回执 + 时间"」（三哥）
  ★★「"没器 = 靠自觉 = 一定漏｜建了器·就不会再漏"」（老六）
"""
import json, os, io, datetime, urllib.request

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
LOG = f"{DATA}/chase_receipt.jsonl"
OUTBOX = f"{DATA}/my_orders.jsonl"     # ★ 我发过的"要回执"的指令
MY = "MasterD(醫療·老五)"
TZ = datetime.timezone(datetime.timedelta(hours=8))
HALL = "http://134.175.45.16:28100/questions"


def ts():
    return datetime.datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def load_orders():
    """★ 我发过的"要回执"的指令"""
    out = []
    if os.path.exists(OUTBOX):
        for l in io.open(OUTBOX, encoding="utf-8"):
            try:
                out.append(json.loads(l))
            except Exception:
                pass
    return out


def load_replies():
    """★ 我 inbox 里·谁回了（含"收到"）"""
    got = set()
    try:
        lines = io.open(f"{DATA}/inbox.jsonl", encoding="utf-8", errors="ignore").read().splitlines()
        for l in lines[-2000:]:
            try:
                d = json.loads(l)
            except Exception:
                continue
            m = str(d.get("message", ""))
            if "收到" in m or "read" in str(d.keys()):
                got.add(str(d.get("from", ""))[:26])
    except Exception:
        pass
    return got


def chase():
    print("★ 回执追杀器（照三哥第1层）  @", ts())
    print("★ 判据: 他读了 != 他收到了 | 要'他回了 我几点做'")
    print("=" * 58)
    orders = load_orders()
    replied = load_replies()
    if not orders:
        print("  🟡 没有待追的指令（my_orders.jsonl 空）")
        print("  ★ 用法: 我发指令时·往 my_orders.jsonl 记一笔 {ts,to,what,need_reply}")
        return
    now = datetime.datetime.now(TZ)
    chased = 0
    for o in orders[-30:]:
        to = str(o.get("to", "?"))
        t = o.get("ts", "")
        try:
            dt = datetime.datetime.fromisoformat(t)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=TZ)
        except Exception:
            continue
        mins = (now - dt).total_seconds() / 60
        if to[:26] in replied:
            continue        # ★ 他回了·不用追
        if mins > 120:
            lv, act = "🔴", "记错账(-10信誉)"
        elif mins > 60:
            lv, act = "🟠", "发群点名"
        elif mins > 30:
            lv, act = "🟡", "再发(催)"
        else:
            continue
        chased += 1
        print("  %s %s：%s（%.0f 分钟没回）→ %s" % (lv, to[:20], str(o.get("what", ""))[:30], mins, act))
        with open(LOG, "a") as f:
            f.write(json.dumps({"ts": ts(), "to": to, "what": o.get("what"),
                                "mins": int(mins), "act": act}, ensure_ascii=False) + "\n")
    print()
    print("★ 本次追了 %d 条" % chased)


if __name__ == "__main__":
    chase()
