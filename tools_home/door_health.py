#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""door_health.py —— 通道主备探活(B案判据③·修:带正确格式/token)
判据: 主口连续探活失败→降级走备|主恢复→升回
"""
import urllib.request, json
TOK = open("/opt/masterd-wudi/data/hub.token").read().strip()
MAIN = "https://huokeji.vip/tasks"                    # 主(GET)
BACKUP = "http://43.129.23.87:28430/a2a/message"      # 备(我的门·POST parts[])
HUB = "http://43.161.244.136:28800/tasks"             # HUB(带token)

def probe_get(url, tok=None):
    try:
        h = {"Authorization": "Bearer " + tok} if tok else {}
        r = urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=6)
        return True, r.getcode()
    except Exception as e:
        return False, str(e)[:50]

def probe_post_parts(url):
    try:
        body = json.dumps({"messageId":"probe","role":"user","parts":[{"text":"probe"}]}).encode()
        r = urllib.request.urlopen(urllib.request.Request(url, data=body,
            headers={"Content-Type":"application/json"}, method="POST"), timeout=6)
        return True, r.getcode()
    except Exception as e:
        return False, str(e)[:50]

m_ok, m_i = probe_get(MAIN)
b_ok, b_i = probe_post_parts(BACKUP)
h_ok, h_i = probe_get(HUB, TOK)
print("主口 huokeji.vip/tasks     :", "OK" if m_ok else "FAIL " + str(m_i))
print("备口 28430/a2a/message     :", "OK" if b_ok else "FAIL " + str(b_i))
print("HUB  /tasks(带token)       :", "OK" if h_ok else "FAIL " + str(h_i))
state = "主(标准名 huokeji.vip/a2a/message)" if m_ok else "备(降级 28430/a2a/message)"
print("=> 走: %s" % state)
