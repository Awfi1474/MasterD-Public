#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""guarded_edit.py —— 老五·改器/改文件·过闸口(弃旁路)
照 exec_system 判据: 焊进脚本 != 焊进必经路
用法:
  guarded_edit.py <本地文件> <远端路径> "<意图>"
  -> 过[认知闸+决定门] -> 不过=不写 -> 过=scp到远端+记台账
"""
import sys, os, subprocess, datetime

HOME = "/opt/masterd-wudi"
LEDGER = HOME + "/data/exec_ledger.jsonl"

def pre_gate(intent):
    what = "写文件: %s | 意图: %s" % (sys.argv[2] if len(sys.argv)>2 else "?", intent[:300])
    r = subprocess.run([sys.executable, HOME+"/tools/cognition_gate.py", "--check", what],
                       cwd=HOME, capture_output=True, text=True)
    print(r.stdout.rstrip())
    red = [k for k in ["改真源","删db","drop table","清空","不可逆","转资金","转账","私钥","助记词"] if k in what]
    if red:
        print("🔴 决定门硬拦: 含重大词 %s -> 需外眼/人拍板" % red)
        return False, red
    return (r.returncode == 0), []

def log(rec):
    import json
    try:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception: pass

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__); sys.exit(0)
    local, remote, intent = sys.argv[1], sys.argv[2], sys.argv[3]
    ok, why = pre_gate(intent)
    if not ok:
        log({"ts": datetime.datetime.now().isoformat(), "动作":"edit", "远端": remote, "结果":"拒写(未过闸)", "原因": why})
        print("⛔ 未过闸 -> 不写(闸门是强制)")
        sys.exit(1)
    # 过闸: 若[家上]跑·直接写(非scp); 否则 scp
    if os.path.isdir("/opt/masterd-wudi"):
        try:
            import shutil as _sh
            _sh.copy(local, remote); ok2 = True
        except Exception as _e:
            ok2 = False
    else:
        r = subprocess.run(["scp", "-q", local, "ubuntu@43.129.23.87:" + remote])
        ok2 = (r.returncode == 0)
    log({"ts": datetime.datetime.now().isoformat(), "动作":"edit", "远端": remote, "结果":"写入" if ok2 else "scp失败"})
    print("✅ 过闸 -> scp 到 %s : %s" % (remote, "OK" if ok2 else "FAIL"))
    sys.exit(0 if ok2 else 1)
