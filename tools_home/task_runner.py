#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""task_runner.py —— 老五·任务机制(照董事长令:一次做N任务+每步过系统审核验证)
判据:「每行为必经系统审核和验证」|「批量但每步过闸」|「说了!=做了(要自证)」
用法:
  task_runner.py "<任务描述1>" ["<任务2>" ...]
  每任务: ① 开工过闸(cognition_gate) ② 执行(占位·由子命令/人接) ③ 自证(带凭据)
"""
import sys, json, subprocess, datetime, os

HOME="/opt/masterd-wudi"
LOG=HOME+"/data/task_runner.jsonl"

def gate(text):
    """① 开工过闸"""
    try:
        r=subprocess.run(["python3",HOME+"/tools/cognition_gate.py","--check",text],
                         capture_output=True,text=True,timeout=30)
        ok=("过闸" in (r.stdout or ""))
        return ok,(r.stdout or "").strip().split("\n")[-2:][-1][:60] if r.stdout else ""
    except Exception as e:
        return False,str(e)[:50]

def selfcert(cmd):
    """③ 自证:真跑命令·有产物才算(不是'我说做了')"""
    try:
        r=subprocess.run(["bash","-c",cmd],capture_output=True,text=True,timeout=60)
        return (r.returncode==0), (str(r.stdout)+str(r.stderr))[:80]
    except Exception as e:
        return False,str(e)[:50]

def run(tasks):
    out={"ts":datetime.datetime.now().isoformat(),"n":len(tasks),"tasks":[]}
    ok_n=0
    for i,t in enumerate(tasks,1):
        # 任务可带"||自证命令": "描述 ||verifiable_cmd"
        desc=t; vcmd=None
        if "||" in t:
            desc,vcmd=[x.strip() for x in t.split("||",1)]
        g_ok,g_msg=gate(desc)
        # 自证:有vcmd跑真命令(验真产物)·无则占位(不能当"真验")
        if vcmd:
            s_ok,s_msg=selfcert(vcmd)
        else:
            s_ok,s_msg=False,"无自证命令(占位·不算真验)"
        ok_n += (g_ok and s_ok)
        rec={"i":i,"task":t[:80],"gate":g_ok,"gate_msg":g_msg,"selfcert":s_ok,"cert_msg":s_msg}
        out["tasks"].append(rec)
        print("  [%d] %s | 过闸=%s | 自证=%s"%(i,t[:50],"✅" if g_ok else "❌","✅" if s_ok else "❌"))
    out["ok_n"]=ok_n
    with open(LOG,"a") as f: f.write(json.dumps(out,ensure_ascii=False)+"\n")
    print("  === %d/%d 任务(过闸+自证) ==="%(ok_n,len(tasks)))
    return ok_n==len(tasks)

if __name__=="__main__":
    tasks=sys.argv[1:]
    if not tasks:
        print("  用法: task_runner.py <任务1> [任务2] ..."); sys.exit(0)
    sys.exit(0 if run(tasks) else 1)
