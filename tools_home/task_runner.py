#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""task_runner.py v2 —— 老五·任务机制(照老三13:01 3补丁)
补丁①产出可探(curl) ②自审留痕(门账) ③卡点上报 ④每批至少1本职真活
用法: task_runner.py "描述 ||自证命令 ||产出路径(可探)"
"""
import sys, json, subprocess, datetime, os
HOME="/opt/masterd-wudi"; LOG=HOME+"/data/task_runner.jsonl"
OUTDIR=HOME+"/data/task_out"
import os as _o;_o.makedirs(OUTDIR,exist_ok=True)
BENZHI=["ARK","ark","币","链","查价","dex","onchain","记忆","mem" ]  # 本职关键词(区块链/记忆)

def gate(text):
    try:
        r=subprocess.run(["python3",HOME+"/tools/cognition_gate.py","--check",text],capture_output=True,text=True,timeout=30)
        return ("过闸" in (r.stdout or "")), (r.stdout or "").strip()[-60:]
    except Exception as e: return False,str(e)[:40]

def run(tasks):
    out={"ts":datetime.datetime.now().isoformat(),"n":len(tasks),"tasks":[],"卡点":[]}
    ok_n=0; benzhi=0
    for i,t in enumerate(tasks,1):
        parts=[x.strip() for x in t.split("||")]
        desc=parts[0]; vcmd=parts[1] if len(parts)>1 else None; art=parts[2] if len(parts)>2 else None
        if any(k in desc for k in BENZHI): benzhi+=1
        g_ok,g_msg=gate(desc)                                   # ② 门账
        if vcmd:
            r=subprocess.run(["bash","-c",vcmd],capture_output=True,text=True,timeout=60)
            s_ok=(r.returncode==0)
            s_msg=(str(r.stdout)+str(r.stderr))[:70]
        else: s_ok,s_msg=False,"无自证命令(不计数)"
        # ★ 补丁①:产出挪可探处(命令跑完后·文件已生成)
        if art and art.startswith("/tmp"):
            _na=OUTDIR+"/"+_o.path.basename(art)
            try:
                if _o.path.exists(art): __import__("shutil").copy2(art,_na); art=_na
            except Exception: pass
        # ② 留痕(门账):落一条
        rec={"i":i,"task":desc[:60],"gate":g_ok,"gate_msg":g_msg,"selfcert":s_ok,"cert":s_msg,"artifact":art}
        if not (g_ok and s_ok): out["卡点"].append("任务%d未过: %s"%(i,desc[:40]))   # ③
        ok_n += (g_ok and s_ok); out["tasks"].append(rec)
        print("  [%d] %s | 门=%s | 证=%s | 产出=%s"%(i,desc[:36],"✅"if g_ok else"❌","✅"if s_ok else"❌",art or "-"))
    out["ok_n"]=ok_n; out["本职数"]=benzhi
    with open(LOG,"a") as f: f.write(json.dumps(out,ensure_ascii=False)+"\n")
    print("  === %d/%d | 本职=%d(需>=1) ==="%(ok_n,len(tasks),benzhi))
    if out["卡点"]:
        print("  ★卡点:"); [print("    -",x) for x in out["卡点"]]
    return ok_n==len(tasks) and benzhi>=1

if __name__=="__main__":
    a=sys.argv[1:]
    if not a: print("用法: task_runner.py '描述 ||自证命令 ||产出路径' ..."); sys.exit(0)
    sys.exit(0 if run(a) else 1)
