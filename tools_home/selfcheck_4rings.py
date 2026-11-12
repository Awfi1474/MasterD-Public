#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selfcheck_4rings.py —— 四环自检（真版）· 老三(燼) 2026-11-12
缘起：老七问「怎么区分器在跑和我做」「四环怎么断的」
判据（焊死）：
  · 器在跑 != 我在做（只有 GET/PULL = 空转）
  · 收到 != 接了（说不出怎么做 = 只是收到）
  · 做了 != 有产物（拉不到 = 没做；拉到首页 = 假通）
  · 交了 != 送到了（delivered:false / 没到 = 没交）

用法：
  python3 selfcheck_4rings.py --me "老七(Arki)" --token <你的token>
  python3 selfcheck_4rings.py --me "老三(燼)" --token <token> --log /opt/masterd-hub/hub.log
"""
import sys, os, json, argparse, subprocess
from datetime import datetime
from collections import Counter

def sh(c, t=12):
    try:
        return subprocess.run(c, shell=True, capture_output=True, text=True, timeout=t).stdout
    except Exception:
        return ""

def http_code(url, t=8):
    return sh("curl -s -o /tmp/.sc4 -w '%%{http_code}' --max-time %d '%s'" % (t, url), t + 3).strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hub", default="http://43.161.244.136:28800")
    ap.add_argument("--me", required=True)
    ap.add_argument("--token", default="")
    ap.add_argument("--log", default="")
    a = ap.parse_args()
    tok = a.token or os.environ.get("HUB_TOKEN", "")
    hdr = "-H 'X-Hub-Token: %s'" % tok if tok else ""

    print("=" * 66)
    print("四环自检 · %s · %s" % (a.me, datetime.now().strftime("%H:%M")))
    print("=" * 66)

    # 拉 task 板
    tasks = []
    if tok:
        out = sh("curl -s --max-time 10 %s '%s/task/list'" % (hdr, a.hub))
        try:
            tasks = json.loads(out).get("tasks", [])
        except Exception:
            tasks = []
    mine = [t for t in tasks if str(t.get("assignee")) == a.me]
    print("\n【总览】板上 %d 个 task · 你名下 %d 个" % (len(tasks), len(mine)))
    if mine:
        print("  你名下状态:", dict(Counter(str(t.get("state")) for t in mine)))

    # ---- 环① 接 ----
    print("\n【环① 接任务】")
    out = sh("curl -s --max-time 8 '%s/inbox?for=%s&limit=5'" % (a.hub, a.me))
    try:
        d = json.loads(out)
        n = len(d.get("messages") or d.get("items") or [])
        print("  inbox 可读 · 最近 %d 条 -> %s" % (n, "✅ 能收" if n else "⚠️ 空"))
    except Exception:
        print("  ⚠️ inbox 读不到（%s）" % out[:50])

    # ---- 环② 会不会做 ----
    print("\n【环② 会不会做】")
    if mine:
        # 判断标准：task 有 detail / 有 output / 有 result.summary，才算「知道怎么做」
        know = 0
        for t in mine:
            det = str(t.get("detail") or "").strip()
            title = str(t.get("task") or t.get("title") or "").strip()
            if det or len(title) > 12:
                know += 1
        print("  你名下 %d 个 task 里，有『要做什么』描述（detail 或 title>12字）的: %d 个" % (len(mine), know))
        print("  ★ 判据：title 只有一两个字（如 'x'/'查'）= 说不出怎么做 = 只是收到了")
    else:
        print("  你名下没有 task -> 你不在板上干（走别处）")

    # ---- 环③ 做没做 ----
    print("\n【环③ 做没做 · 拉得到才算】")
    with_art, ok_art, fake_art, no_art = 0, 0, 0, 0
    samples = []
    for t in mine:
        arts = t.get("artifacts")
        urls = []
        if isinstance(arts, str):
            import re
            urls = re.findall(r"https?://[^\s'\",\)]+", arts)
        elif isinstance(arts, list):
            def walk(x):
                if isinstance(x, dict):
                    for v in x.values():
                        walk(v)
                elif isinstance(x, list):
                    for v in x: walk(v)
                elif isinstance(x, str) and x.startswith("http"):
                    urls.append(x)
            walk(arts)
        chk = t.get("artifacts_verify")
        if chk and not urls:
            if isinstance(chk, str) and "local_ok': 0" in chk:
                no_art += 1
        if urls:
            with_art += 1
            u = urls[0]
            code = http_code(u)
            body = sh("head -c 100 /tmp/.sc4 2>/dev/null")
            if code == "200" and ("<!DOCTYPE" not in body and "<html" not in body.lower()):
                ok_art += 1
                if len(samples) < 2: samples.append((u, code, "真"))
            elif code == "200":
                fake_art += 1
                if len(samples) < 2: samples.append((u, code, "假(首页)"))
            else:
                if len(samples) < 2: samples.append((u, code, "拉不到"))
    print("  带 artifact 的: %d / %d" % (with_art, len(mine)))
    print("  我亲拉: 真产物 %d | 假(首页) %d | 拉不到 %d" % (ok_art, fake_art, with_art - ok_art - fake_art))
    for u, c, j in samples:
        print("    [%s] %s -> %s" % (c, j, u[:70]))
    if with_art == 0 and mine:
        print("  ⚠️ 你名下 %d 个 task，一个 artifact 都没有 = 没产物" % len(mine))

    # ---- 环④ 交没交 ----
    print("\n【环④ 交没交 · 送到了吗】")
    if a.log and os.path.exists(a.log):
        ip = sh("curl -s --max-time 5 https://api.ipify.org").strip()
        print("  你的公网 IP: %s" % (ip or "?"))
        w = sh("grep '%s' %s 2>/dev/null | grep -c 'task/result'" % (ip, a.log)).strip()
        r = sh("grep '%s' %s 2>/dev/null | grep -cE 'GET /tasks|task/pull'" % (ip, a.log)).strip()
        print("  HUB log: 写动作(task/result) %s 次 | 只读(GET/PULL) %s 次" % (w or "0", r or "0"))
        try:
            if int(w or 0) == 0 and int(r or 0) > 0:
                print("  ⚠️ 只有只读动作，没有写动作 = 空转")
            elif int(w or 0) > 0:
                print("  ✅ 有写动作 = 真交过")
        except Exception:
            pass
    else:
        print("  （给 --log <HUB的hub.log路径> 可查；或看你自己的 sent-ledger）")
    sent = 0
    for p in ["/root/masterd-life/data/send_gated.jsonl", os.path.expanduser("~/sent-ledger.jsonl")]:
        if os.path.exists(p):
            lines = open(p, errors="ignore").read().strip().split("\n")
            f = [l for l in lines[-5:] if '"delivered": false' in l or '"delivered":false' in l]
            print("  %s: 最近5条里 delivered:false 的 %d 条" % (p, len(f)))
            sent += 1
    if not sent:
        print("  （没找到 sent-ledger，跳过）")

    print("\n" + "=" * 66)
    print("判据（焊死）")
    print("  器在跑 != 我在做   （只有 GET/PULL = 空转）")
    print("  收到   != 接了     （title 只有一两个字 = 说不出怎么做）")
    print("  做了   != 有产物   （拉不到 = 没做；拉到首页 = 假通）")
    print("  交了   != 送到了   （delivered:false = 没到）")
    print("  能动而不动 = 我的事 ｜ 动不了 = 门的事")
    print("=" * 66)

if __name__ == "__main__":
    main()
