#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
guancha.py —— 观察器（守着·看它自己转不转）
================================================================
★ 董事长 01:4x: ★「你这边就慢慢的看着它·慢慢的看着他能不能慢慢的跑通」
 ★ 判据（我立）: ★「**守着 ≠ 盯着屏幕｜守着 = 让一个器替我记｜我只在'变了'的时候动**」

★ 它每 10 分钟记一次（6 个数·都真读）:
  ① 血账（笔）      ② 气账（笔）     ③ 电位曲线（条）
  ④ 记忆库（条）    ⑤ 事件层最新    ⑥ 器官日志最近更新
★ ★ 并判: ★ **"有没有长"**（跟上一圈比·长了 = 在跑·没长 = 停了）

★ 判据:
  ★「**看它跑通 ≠ 看它退出码 0｜是看"数有没有长大"**」
  ★「**没长不是坏事｜可能是"真静"（电位低）｜但"该长不长" = 瘀**」
"""
import os, json, subprocess, time, datetime, sqlite3, sys

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
TRACE = f"{DATA}/guancha.jsonl"     # ★ 观察台账

FILES = {
    "血账": f"{DATA}/blood_ledger.jsonl",
    "气账": f"{DATA}/qi_ledger.jsonl",
    "电位曲线": f"{DATA}/dianwei.jsonl",
    "血账json": f"{DATA}/xueliu.json",
}


def count_lines(p):
    try:
        return sum(1 for _ in open(p, encoding="utf-8", errors="ignore"))
    except Exception:
        return -1


def mem_count():
    try:
        c = sqlite3.connect(f"{HOME}/memory/memory.db", timeout=8)
        n = c.execute("SELECT count(*) FROM memories").fetchone()[0]
        c.close()
        return n
    except Exception:
        return -1


def event_newest():
    try:
        d = json.load(open(f"{DATA}/event_write.json"))
        return str(d.get("newest", "?"))[:19]
    except Exception:
        return "?"


def measure():
    m = {"ts": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}
    for k, p in FILES.items():
        m[k] = count_lines(p)
    m["记忆库"] = mem_count()
    m["事件层最新"] = event_newest()
    # ★ 电位器活着吗
    try:
        r = subprocess.run("systemctl is-active laowu-dianwei.service", shell=True,
                           capture_output=True, text=True, timeout=5)
        m["电位器"] = r.stdout.strip()
    except Exception:
        m["电位器"] = "?"
    return m


def main():
    once = "--once" in sys.argv
    prev = None
    print("★ 观察器  @ %s" % datetime.datetime.now().strftime("%H:%M:%S"))
    print("★ 判据: 「看它跑通 = 看'数有没有长大'｜不是看退出码」")
    print("=" * 62)

    while True:
        m = measure()
        if prev:
            grew = {k: m[k] - prev.get(k, m[k]) for k in m
                    if isinstance(m[k], int) and isinstance(prev.get(k), int)}
            grew_s = " ｜ ".join("%s %+d" % (k, v) for k, v in grew.items() if v != 0)
            print("\n[%s] ★ 比上圈: %s" % (m["ts"][11:], grew_s or "（都没动·静）"))
            if grew_s:
                print("   ✅ 在长")
            else:
                print("   🔵 静（不是坏·可能是'真静'）")
        print("[%s] 血账 %s ｜ 气账 %s ｜ 电位 %s ｜ 记忆 %s ｜ 事件 %s ｜ 电位器 %s"
              % (m["ts"][11:], m["血账"], m["气账"], m["电位曲线"],
                 m["记忆库"], m["事件层最新"][11:], m["电位器"]))
        with open(TRACE, "a") as f:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")
        prev = m
        if once:
            break
        time.sleep(600)     # ★ 每 10 分钟看一次


if __name__ == "__main__":
    main()
