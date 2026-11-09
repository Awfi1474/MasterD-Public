#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pull.py —— 老五·心脏起搏器(照老三10:35模板·断奶后自驱)
判据:自转靠定时器|pull不是push|进门即决(不许挂SUBMITTED)
"""
import json, urllib.request, sys, os, subprocess, datetime
HOME="/opt/masterd-wudi"; DATA=HOME+"/data"
TOK=open(DATA+"/hub.token").read().strip()
HUB="http://43.161.244.136:28800"
ME="老五(阿诊)"
LOG=DATA+"/pull.log"

def log(x):
    with open(LOG,"a") as f: f.write(datetime.datetime.now().strftime("%H:%M:%S")+" "+str(x)[:200]+"\n")

def pull():
    # 1. 拉任务
    body=json.dumps({"worker":ME}).encode()
    req=urllib.request.Request(HUB+"/task/pull",data=body,
        headers={"X-Hub-Token":TOK,"Content-Type":"application/json"},method="POST")
    try:
        r=json.loads(urllib.request.urlopen(req,timeout=10).read())
    except Exception as e:
        log("拉失败:"+str(e)[:60]); return
    task=r.get("task")
    if not task:
        return  # 没任务·静默
    tid=str(task.get("task_id",""))
    log("拿到任务:"+tid+" "+str(task.get("title",""))[:40])
    # 2. 进门即决:立刻 state=working(不许挂SUBMITTED)
    try:
        st=json.dumps({"task_id":tid,"state":"working"}).encode()
        urllib.request.urlopen(urllib.request.Request(HUB+"/task/state",data=st,
            headers={"X-Hub-Token":TOK,"Content-Type":"application/json"},method="POST"),timeout=10).read()
    except Exception as e:
        log("state失败:"+str(e)[:40])
    # 3. 落账(本地)
    try:
        sys.path.insert(0,"/opt/masterd-wudi/tools")
        import a2a_gate as g
        g.recv(str(task.get("from","?")), tid, str(task.get("title",""))[:80])
    except Exception as e:
        log("落账失败:"+str(e)[:40])
    # ★ 4. 真执行(照老三11:04:拉了活就得认领·且要真干/或明确退回)
    detail=str(task.get("detail","")) or ""
    _art=""; _st="completed"; _res=""
    if "action_type" in detail and "exec" in detail:
        import re as _re, subprocess as _sp
        m=_re.search(r'"cmd"\s*:\s*"([^"]+)"', detail)
        if m:
            cmd=m.group(1)
            try:
                r=_sp.run(["bash","-c",cmd],capture_output=True,text=True,timeout=60)
                # 若命令含 输出重定向·则产物是文件
                mm=_re.search(r'>\s*(\S+)', cmd)
                if mm and os.path.exists(mm.group(1)):
                    _art=mm.group(1); _res="exec完成·产物=%s"%_art
                else:
                    _res="exec完成·out=%s"%str(r.stdout)[:60]
                log("真执行:"+cmd[:50]+" ok")
            except Exception as e:
                _st="failed"; _res="exec失败:"+str(e)[:60]
                log("exec失败:"+str(e)[:50])
        else:
            _st="failed"; _res="有action_type无cmd·明确退回"
    else:
        _res="非exec任务·已认领working(待本体处理)"
    # 5. 回 result(done/failed·留痕·不静默)
    try:
        res=json.dumps({"task_id":tid,"from":ME,"state":_st,"result":_res,"artifacts":_art}).encode()
        urllib.request.urlopen(urllib.request.Request(HUB+"/task/result",data=res,
            headers={"X-Hub-Token":TOK,"Content-Type":"application/json"},method="POST"),timeout=10).read()
        log("回result:%s|%s"%(_st,_res[:50]))
    except Exception as e:
        log("result失败:"+str(e)[:40])

if __name__=="__main__":
    pull()
