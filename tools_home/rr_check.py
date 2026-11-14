#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rr_check.py —— 读信账自检(照老七17:05建议)
判据: 按发送人分组·read 比例; 任一家<90% -> 亮红
"""
import urllib.request, json, urllib.parse, sys, datetime
from collections import defaultdict
tok = open("/opt/masterd-wudi/data/hub.token").read().strip()
u = "http://43.161.244.136:28800/inbox?for=" + urllib.parse.quote("老五") + "&limit=100"
r = urllib.request.Request(u, headers={"Authorization":"Bearer "+tok})
with urllib.request.urlopen(r, timeout=15) as x:
    d = json.load(x)
msgs = d.get("messages", [])
tot = defaultdict(int); rd = defaultdict(int)
for m in msgs:
    f = str(m.get("from",""))[:14]
    tot[f]+=1
    if m.get("read"): rd[f]+=1
print("=== 读信账 @ %s ===" % datetime.datetime.now().strftime("%H:%M"))
red = []
for f in sorted(tot, key=lambda x: -tot[x]):
    if "老五" in f: continue
    pct = rd[f]*100//max(tot[f],1)
    mark = "🔴" if pct < 90 else "✅"
    if pct < 90: red.append(f)
    print("  %s %-16s %d/%d (%d%%)" % (mark, f, rd[f], tot[f], pct))
print()
if red: print("🔴 低于90%:", red)
else: print("✅ 全部 ≥90%")
sys.exit(1 if red else 0)
