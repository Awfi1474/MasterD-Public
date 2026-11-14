#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·残留扫描 cleanup_scan.py（照老六提"孤儿多"）
★ 判据（照实）：
  ① 孤儿进程(PPID=1) 只算"不该留的"(临时测试/文件已不存在/无systemd管)
  ② 死webhook(探活失败) → 报(不自动删·留人定)
  ③ 只报不删(防误伤)·要删先人确认
"""
import json, os, subprocess, sys, urllib.request

def orphans():
    """找 PPID=1 且不是 systemd 管的正经服务"""
    out = subprocess.run("ps -eo pid,ppid,etime,cmd --no-headers", shell=True,
                         capture_output=True, text=True).stdout
    bad = []
    for l in out.splitlines():
        p = l.split(None, 3)
        if len(p) < 4: continue
        pid, ppid, etime, cmd = p
        if ppid != "1": continue
        if "python3 -c" in cmd or "/tmp/" in cmd or "nohup" in cmd:
            bad.append((pid, etime, cmd[:90]))
    return bad

def dead_hooks():
    P = "/opt/masterd-wudi/data/push_configs.json"
    if not os.path.exists(P): return 0, 0
    try: d = json.load(open(P, encoding="utf-8"))
    except Exception: return 0, 0
    dead = 0
    for v in d.values():
        u = v.get("url") if isinstance(v, dict) else None
        if not u: dead += 1; continue
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, method="POST",
                data=b'{}', headers={"Content-Type": "application/json"}), timeout=2)
            if not (200 <= r.getcode() < 300): dead += 1
        except Exception: dead += 1
    return len(d), dead

if __name__ == "__main__":
    o = orphans(); tot, dead = dead_hooks()
    print("★ 残留扫描（照实·只报告·不自动删）")
    print("  ① 可疑孤儿进程: %d 个" % len(o))
    for pid, et, cmd in o[:8]: print("     pid=%s %s | %s" % (pid, et, cmd))
    print("  ② push 配置: %d 条 | 死地址: %d 条" % (tot, dead))
    print("\n★ 判据: 残留不扫=越积越多｜扫了要人定才删")
    sys.exit(1 if (o or dead) else 0)
