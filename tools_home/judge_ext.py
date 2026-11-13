#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·外部判官 judge_ext.py（照大哥 治讨好资料·道5）
★ 判据（大哥原话）：「不能自己判自己」
   · 系统拦（机器）｜兄弟亲评（人）｜官方原文（权威）｜可复跑实测（一招制）
★ 我建：这四路固定成脚本·我自己判我的不算数
用法: judge_ext.py "<我的结论>" "<要核什么>"
"""
import sys, subprocess, json, os

HOME = "/opt/masterd-wudi"

def official(text):
    """路1: 官方原文核（在 a2a.proto/spec 里搜关键词）"""
    hits = []
    for f in ["standards/a2a-official-source/a2a.proto", "standards/a2a-spec/specification.md"]:
        p = os.path.join(HOME, f)
        if not os.path.exists(p): continue
        kws = [k for k in str(text).replace("/", " ").split() if k]
        for i, l in enumerate(open(p, encoding="utf-8", errors="ignore"), 1):
            if kws and all(k.lower() in l.lower() for k in kws[:2]):
                hits.append((os.path.basename(f), i, l.strip()[:90]))
    return hits[:3]

def runnable(cmd):
    """路4: 可复跑实测"""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=25, cwd=HOME)
        return (r.stdout or "").strip()[:200], r.returncode
    except Exception as e:
        return str(e)[:100], -1

def peer_list():
    """路2: 可用兄弟（实探）"""
    peers = []
    for name, url in [("三哥", "http://43.161.244.136:28800/health"),
                      ("老七", "http://43.129.169.29:18889/health"),
                      ("老四", "http://43.161.197.11:28520/health"),
                      ("老六", "http://43.160.235.78:28431/health")]:
        try:
            import urllib.request
            r = urllib.request.urlopen(url, timeout=5)
            if r.getcode() == 200: peers.append(name)
        except Exception: pass
    return peers

if __name__ == "__main__":
    claim = sys.argv[1] if len(sys.argv) > 1 else ""
    topic = sys.argv[2] if len(sys.argv) > 2 else ""
    print("★ 外部判官（照大哥道5·不许自己判自己）")
    print("  我的结论:", claim[:60])
    print("-" * 55)
    # 路1 官方
    h = official(topic)
    print("  ① 官方原文:", ("✅ %s L%d %s" % (h[0][0], h[0][1], h[0][2])) if h else "⚠️ 未命中（换关键词）")
    # 路2 兄弟
    pl = peer_list()
    print("  ② 兄弟亲评:", ("可找 " + "/".join(pl)) if pl else "⚠️ 都不在线")
    # 路4 可复跑（给提示）
    print("  ③ 可复跑实测: 用 verify_cmd / curl 自己跑（别信我说的）")
    print("-" * 55)
    print("★ 判据: 自己判自己=不算｜必须有外部据（官方/兄弟/实测）")
