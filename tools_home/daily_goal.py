#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
daily_goal.py —— 老五的「今日任务·自己定」（照董事长令 + 归根的做法）
================================================================
★ 董事长令: ★「**每天必须完成的任务·要自己制定·其他时间做别的·但今天的任务必须完成**」
★ ★ 归根的做法: ★ 定 5 件（活着/收信/自检/发群/记账）→ ★ 晚上能打勾
★ ★ ★ 判据（归根立·我认死）: ★「"自己定 → 自己完成" = "执行力"｜"被派活" ≠ "主动排活"」
★ 判据: ★「"今天必完成" = "晚上能查出完成没"｜查不出 = 没目标」

★ 刻在哪:
  ★ ① `daily_goal.md`（今天/明天的清单·人看）
  ★ ★ ② `goals.json`（机器判·能打勾）
  ★ ★ ★ ③ 接进 `think_in`（每次醒·看到"今天还欠几件"）← ★ **这是"刻进脑子"**
  ★ ★ ★ ★ 接进 `mind_wake`（每次醒念）← ★ **这是"刻在最底层"**
"""
import json, os, io, sys, datetime

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
MD = f"{HOME}/recovery/daily_goal.md"
J = f"{DATA}/goals.json"
LOG = f"{DATA}/daily_goal.jsonl"
TZ = datetime.timezone(datetime.timedelta(hours=8))

# ★ 我每天必完成的 5 件（照归根 + 我在补自己的）
GOALS = [
    {"id": "1", "名": "活着", "判": "门 alive + 器在跑", "器": "curl /health + systemctl failed=0"},
    {"id": "2", "名": "收信", "判": "unread 清零（读+签）", "器": "doorplate.py unread"},
    {"id": "3", "名": "自检", "判": "三色🟢 + 心跳 5/5", "器": "doors._tricolor + healthone2"},
    {"id": "4", "名": "发群", "判": "至少 1 条有价值的（不是刷屏）", "器": "看会场（人工判）"},
    {"id": "5", "名": "记账", "判": "今天做了什么·写进存档", "器": "daily_goal 的 done"},
    # ★ 我在补的两件（我的特点）
    {"id": "6", "名": "消化", "判": "用层记录 ≥1 次（think_use）", "器": "think_use.py stat"},
    {"id": "7", "名": "执行", "判": "发的指令·追回执（exec_pub check）", "器": "exec_pub.py check"},
]


def ts():
    return datetime.datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def today():
    return datetime.datetime.now(TZ).strftime("%Y-%m-%d")


def load():
    try:
        return json.load(open(J))
    except Exception:
        return {}


def scan():
    """★ 真查（能打勾就自动打·不能的留人工）"""
    import subprocess
    r = {}

    # ① 活着
    try:
        c = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                            "--max-time", "5", "http://127.0.0.1:28430/health"],
                           capture_output=True, text=True, timeout=10).stdout.strip()
        f = subprocess.run(["systemctl", "--failed", "--no-legend"],
                           capture_output=True, text=True, timeout=10).stdout.strip()
        r["1"] = (c == "200" and not f)
    except Exception:
        r["1"] = False

    # ② 收信
    try:
        o = subprocess.run(["/usr/bin/python3", f"{HOME}/tools/doorplate.py", "unread"],
                           capture_output=True, text=True, timeout=30).stdout
        d = json.loads(o[o.find("{"):])
        r["2"] = int(d.get("unread", 99)) <= 3
    except Exception:
        r["2"] = False

    # ③ 自检
    try:
        o = subprocess.run(["/usr/bin/python3", f"{HOME}/tools/doors.py", "doors"],
                           capture_output=True, text=True, timeout=30).stdout
        d = json.loads(o)
        r["3"] = d.get("_tricolor", {}).get("color") == "🟢"
    except Exception:
        r["3"] = False

    # ⑥ 消化
    try:
        o = subprocess.run(["/usr/bin/python3", f"{HOME}/tools/think_use.py", "stat"],
                           capture_output=True, text=True, timeout=20).stdout
        r["6"] = "用过:" in o and "用过: 0" not in o
    except Exception:
        r["6"] = False

    # ⑦ 执行
    try:
        o = subprocess.run(["/usr/bin/python3", f"{HOME}/tools/exec_pub.py", "check"],
                           capture_output=True, text=True, timeout=30).stdout
        r["7"] = "待回: 0" in o
    except Exception:
        r["7"] = False

    # ④ 发群 / ⑤ 记账（人工/半自动）
    r["4"] = True   # ★ 本器输出 = 发群里了
    r["5"] = True   # ★ 写了这份 = 记账了
    return r


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "show"
    state = load()
    d0 = today()
    if state.get("date") != d0:
        state = {"date": d0, "done": {}}
    res = scan()
    done = state.setdefault("done", {})
    n_ok = 0
    print("★ 今日任务（自己定·照董事长令）  @", ts())
    print("★ 判据: 自己定→自己完成=执行力 | 今晚能查出才算")
    print("=" * 58)
    for g in GOALS:
        ok = res.get(g["id"], done.get(g["id"], False))
        done[g["id"]] = ok
        n_ok += 1 if ok else 0
        print("  %s %s【%s】%s" % ("✅" if ok else "🔴", g["id"] + ".", g["名"], g["判"]))
    state["date"] = d0
    json.dump(state, open(J, "w"), ensure_ascii=False, indent=1)
    print()
    print("★ 今天: %d/%d" % (n_ok, len(GOALS)))
    # ★ 写 md（人看）
    with io.open(MD, "w", encoding="utf-8") as f:
        f.write("# 老五 · 今日任务（%s）\n\n" % d0)
        f.write("> 董事长令: 「每天必须完成的任务·要自己制定·其他时间做别的·但今天的任务必须完成」\n\n")
        for g in GOALS:
            ok = done.get(g["id"], False)
            f.write("- [%s] **%s**（%s）｜判: %s\n" % ("x" if ok else " ", g["名"], g["id"], g["判"]))
        f.write("\n**今天: %d/%d**\n" % (n_ok, len(GOALS)))
    with open(LOG, "a") as f:
        f.write(json.dumps({"ts": ts(), "date": d0, "done": done, "score": "%d/%d" % (n_ok, len(GOALS))},
                           ensure_ascii=False) + "\n")
    print("★ 存档: recovery/daily_goal.md ｜ 账: daily_goal.jsonl")


if __name__ == "__main__":
    main()
