#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""evidence_push.py —— 老五·证据定时推送(治'evidence没更新')
"""
import subprocess,json,urllib.request
TOK=open("/opt/masterd-wudi/data/hub.token").read().strip()
raw=subprocess.run(["systemctl","status","laowu-core","--no-pager"],capture_output=True,text=True).stdout
body={"from":"老五(阿诊)","unit":"laowu-core","raw":raw}
r=urllib.request.urlopen(urllib.request.Request("http://43.161.244.136:28800/evidence",
   data=json.dumps(body,ensure_ascii=False).encode(),
   headers={"X-Hub-Token":TOK,"Content-Type":"application/json"},method="POST"),timeout=10)
print("  ",r.read().decode()[:120])
