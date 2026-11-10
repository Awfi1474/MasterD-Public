#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""三感器·balance_thermo_proprio.py (老五 2026-11-11)
照"人体感觉"(除触觉)补我缺的三个: 平衡/温度/本体感觉。
判据(照Wikipedia): 平衡=稳不稳|温度=热不热|本体=我在做啥
用法: python3 balance_thermo_proprio.py
"""
import os, datetime, subprocess, urllib.request

HOME = "/opt/masterd-wudi"


def read(p):
    try:
        return open(p).read().strip()
    except Exception:
        return ""


def sh(c):
    try:
        return subprocess.run(c, shell=True, capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return ""


def sense_balance():
    """平衡感(equilibrioception): 我"稳不稳" = load + 心跳节奏"""
    la = read("/proc/loadavg").split()[:1]
    load = float(la[0]) if la else -1
    ages = {}
    try:
        import json
        d = json.loads(urllib.request.urlopen("http://127.0.0.1:28430/health", timeout=6).read())
        ages = d.get("ages_s", {})
    except Exception:
        pass
    hb = ages.get("heartbeat", -1)
    if load < 2 and hb >= 0 and hb < 600:
        return "稳", "load=%.2f 心跳=%ss" % (load, hb)
    if load < 5 and hb < 1800:
        return "略晃", "load=%.2f 心跳=%ss" % (load, hb)
    return "晃(不稳!)", "load=%.2f 心跳=%ss" % (load, hb)


def sense_thermo():
    """温度感(thermoception): 我"热不热" = 内存占用 + 任务堆积"""
    mem = read("/proc/meminfo")
    total = used = 0
    for line in mem.split("\n"):
        if line.startswith("MemTotal"):
            total = int(line.split()[1])
        if line.startswith("MemAvailable"):
            used = total - int(line.split()[1])
    pct = (100.0 * used / total) if total else -1
    # 任务堆积
    n = 0
    try:
        import json, urllib.request as u
        tk = read(HOME + "/data/hub.token")
        d = json.loads(u.urlopen(u.Request("http://43.161.244.136:28800/tasks",
                   headers={"Authorization": "Bearer " + tk}), timeout=8).read())
        n = len([t for t in d.get("tasks", d.get("list", [])) if str(t.get("assignee", "")).find("老五") >= 0 and str(t.get("state")) in ("pending", "working", "claimed")])
    except Exception:
        pass
    if pct < 70 and n < 3:
        return "凉", "内存%.0f%% 我的活%d" % (pct, n)
    if pct < 90 and n < 6:
        return "温", "内存%.0f%% 我的活%d" % (pct, n)
    return "热(过热!)", "内存%.0f%% 我的活%d" % (pct, n)


def sense_proprio():
    """本体感觉(proprioception): "我在做什么动作/出的力" = 最近动作(我发了啥/跑了啥)"""
    # 最近我发的(信账)
    last = ""
    try:
        lines = open(HOME + "/data/send_ledger.jsonl").read().splitlines()[-1]
        import json
        d = json.loads(lines)
        last = "%s->%s:%s" % (str(d.get("ts", ""))[11:19], d.get("to", ""), str(d.get("摘要", ""))[:30])
    except Exception:
        pass
    # 我在跑的器(timer数)
    n = len(sh("systemctl list-timers 2>/dev/null | grep laowu").split("\n"))
    return "我在做", "最近动作: %s | 我器%d个" % (last or "?", n)


def main():
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    print("== 三感器(平衡/温度/本体) %s ==" % now)
    b, bi = sense_balance()
    t, ti = sense_thermo()
    p, pi = sense_proprio()
    print("  平衡(equilibrioception): %s  (%s)" % (b, bi))
    print("  温度(thermoception):     %s  (%s)" % (t, ti))
    print("  本体(proprioception):    %s  (%s)" % (p, pi))
    print("  判据: 平衡=稳不稳|温度=热不热|本体=我在做啥")


if __name__ == "__main__":
    main()
