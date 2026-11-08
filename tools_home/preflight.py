#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""preflight.py —— 老五·试炼前自查(一条命令出全绿清单)
照第一次试炼考点:收到->working|本体自驱|通道三口|口活|真源完整
"""
import urllib.request, json, sqlite3, subprocess
TOK = open("/opt/masterd-wudi/data/hub.token").read().strip()
def get(url, tok=False):
    try:
        h = {"Authorization":"Bearer "+TOK} if tok else {}
        r = urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=8)
        return True, r.getcode()
    except Exception as e:
        return False, str(e)[:40]
def post(url, body, tok=False):
    try:
        h = {"Content-Type":"application/json"}
        if tok: h["Authorization"]="Bearer "+TOK
        r = urllib.request.urlopen(urllib.request.Request(url, data=json.dumps(body).encode(), headers=h, method="POST"), timeout=8)
        return True, r.getcode()
    except Exception as e:
        return False, str(e)[:40]

ok = 0; tot = 0
def line(name, okb, extra=""):
    global ok, tot; tot += 1
    if okb: ok += 1
    print("  [%s] %-40s %s" % ("OK" if okb else "XX", name, extra))

# 1 通道三口
b,_ = post("https://huokeji.vip/a2a/message", {"from":"lao5","to":"lao5","message":"preflight"}); line("投 huokeji/a2a/message", b)
b,_ = get("http://43.161.244.136:28800/inbox?for=lao5", True); line("收 HUB/inbox?for=lao5", b)
b,_ = get("http://43.161.244.136:28800/tasks", True); line("查 HUB/tasks", b)
b,_ = get("http://43.129.23.87:28430/tasks"); line("查 我 28430/tasks(免口令)", b)
# 2 我口
b,_ = get("http://43.129.23.87:28430/health"); line("我本体 28430/health", b)
b,_ = get("http://localhost:28440/health"); line("我 28440(备门·内网)活", b)
# 3 真源完整
try:
    c = sqlite3.connect("file:/opt/masterd-wudi/memory/memory.db?mode=ro", uri=True)
    integ = c.execute("PRAGMA integrity_check").fetchone()[0]
    rows = c.execute("select count(*) from memories").fetchone()[0]
    c.close()
    line("真源 integrity", integ == "ok", "rows=%d" % rows)
except Exception as e:
    line("真源 integrity", False, str(e)[:40])
# 4 唤醒闸表
try:
    c = sqlite3.connect("file:/opt/masterd-wudi/memory/memory.db?mode=ro", uri=True)
    c.execute("select count(*) from a2a_inbox").fetchone()
    c.close(); line("唤醒闸表 a2a_inbox", True)
except Exception as e:
    line("唤醒闸表 a2a_inbox", False, str(e)[:40])
# 5 服务
for s in ["laowu-p2p","laowu-recv-alt"]:
    r = subprocess.run(["systemctl","is-active",s], capture_output=True, text=True).stdout.strip()
    line("服务 "+s, r=="active", r)
# 6 门(备)降级器
import os
line("备失效判据 door_health.py", os.path.exists("/opt/masterd-wudi/tools/door_health.py"))
line("看消息 read_msgs.py", os.path.exists("/opt/masterd-wudi/tools/read_msgs.py"))
line("db_guard.py", os.path.exists("/opt/masterd-wudi/tools/db_guard.py"))

print("\n=== 试炼前自查: %d/%d 绿 ===" % (ok, tot))
