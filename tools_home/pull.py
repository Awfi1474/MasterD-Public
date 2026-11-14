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
    # ★ 2026-11-12 加固(照实·治"拉超时"): timeout 10->20 + 重试1次
    #   判据: 单次超时!=死|重试1次|别因抖动漏活
    r = None
    for _try in range(2):
        try:
            r = json.loads(urllib.request.urlopen(req, timeout=20).read())
            break
        except Exception as e:
            log("拉失败(第%d次):%s" % (_try + 1, str(e)[:50]))
            if _try == 0:
                import time as _t2; _t2.sleep(2)
    if r is None:
        return
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
            # ★ 2026-11-09 修:exec型但无cmd(如"加字段"类)=该【认领working→推本体】·不"当场退"
            _st="working"; _res="exec型无cmd(加字段类)·认领working·推本体处理"
            try:
                import subprocess as _sp2
                _sp2.Popen(["python3","/opt/masterd-wudi/code/core_v2.py","--once"],
                           stdout=_sp2.DEVNULL, stderr=_sp2.DEVNULL)
            except Exception: pass
    else:
        # ★ 2026-11-09 修(认错):非exec型(如"加字段"任务)·该【认领working→推本体处理】·不"当场退"
        _st="working"; _res="非exec型task·已认领working·推本体处理(不误退)"
        # 2026-11-11 fix(照老三"本体常驻"第3步): 写"待本体做"标志 -> 本体醒时必看
        try:
            import json as _j2, datetime as _d2
            _td = "/opt/masterd-wudi/data/待本体做.jsonl"
            with open(_td, "a") as _f:
                _f.write(_j2.dumps({"ts": _d2.datetime.now().isoformat(timespec="seconds"),
                    "task_id": tid, "title": str(task.get("title",""))[:60],
                    "detail": detail[:200], "note": "非exec·待本体做·别等被点"}, ensure_ascii=False) + "\n")
            log("写:待本体做 "+tid)
        except Exception as _e:
            log("写标志失败:"+str(_e)[:40])
        try:
            import subprocess as _sp2
            _sp2.Popen(["python3","/opt/masterd-wudi/code/core_v2.py","--once"],
                       stdout=_sp2.DEVNULL, stderr=_sp2.DEVNULL)
        except Exception: pass
    # 5. 回 result(done/failed·留痕·不静默)
    try:
        res=json.dumps({"task_id":tid,"from":ME,"state":_st,"result":_res,"artifacts":_art}).encode()
        urllib.request.urlopen(urllib.request.Request(HUB+"/task/result",data=res,
            headers={"X-Hub-Token":TOK,"Content-Type":"application/json"},method="POST"),timeout=10).read()
        log("回result:%s|%s"%(_st,_res[:50]))
    except Exception as e:
        log("result失败:"+str(e)[:40])


def assignee_scan():
    """照链断点(task没落我板): 主动查 assignee=老五 的任务"""
    try:
        import urllib.request as _ur, json as _j
        # ★ 2026-11-14 修(字据 pull.log 20:41:35 IncompleteRead 136964/289000):
        #   task/list?limit=200 返 289KB·urlopen 直 read 会读不全 -> 降 limit + 读完循环
        _u = HUB + "/task/list?limit=60"
        _r = _ur.Request(_u, headers={"Authorization": "Bearer " + TOK, "X-Hub-Token": TOK})
        with _ur.urlopen(_r, timeout=25) as _x:
            _buf = b""
            while True:
                _chunk = _x.read(65536)
                if not _chunk:
                    break
                _buf += _chunk
            _d = _j.loads(_buf)
        _ts = _d.get("tasks") or []
        _mine = [t for t in _ts
                 if ("老五" in str(t.get("assignee", "")) or "lao5" in str(t.get("assignee", "")))
                 and t.get("state") not in ("completed", "canceled")]
        if _mine:
            log("assignee_scan: %d 条派给我(非completed)" % len(_mine))
            for _t in _mine[:10]:
                log("   -> " + str(_t.get("task_id")) + " | " + str(_t.get("state")) + " | " + str(_t.get("title", ""))[:50])
        return _mine
    except Exception as _e:
        log("assignee_scan ERR: " + str(_e)[:60])
        return []

if __name__=="__main__":
    pull()
    assignee_scan()
