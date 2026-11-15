#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·闸链 gate_chain.py（照本体方案+董事长新令·最少两个系统）
★ 档位从【动作】来·不是我填 → 取消"我判松"
★ 每系统一个探针·返回 True/False·不靠自觉
★ 票不够 exit!=0 → 绕不过去
用法: gate_chain.py "<要做的动作>"
"""
import sys, re, subprocess, json, datetime, os

HOME = "/opt/masterd-wudi"
LEDGER = HOME + "/data/gate_chain_ledger.jsonl"
NEED = {"轻": 1, "中": 2, "重": 3}   # 重 = 2系统+反方 = 记3票

def tier(cmd):
    """档位从动作文本判·不是我填"""
    if re.search(r'\brm\b|mkfs|dd |systemctl (restart|stop)|密钥|private.?key|私钥', cmd):
        return "重"
    if re.search(r'tools/.*gate|decide|memory\.db|schema|agent-card|p2p_mailbox|send_msg', cmd):
        return "中"
    return "轻"

def _run(script, args, timeout=60):
    try:
        r = subprocess.run([sys.executable, HOME + "/tools/" + script] + args,
                           capture_output=True, text=True, timeout=timeout, cwd=HOME)
        return r.returncode == 0, (r.stdout or "")[-160:]
    except Exception as e:
        return False, str(e)[:60]

def probe_decide(cmd):
    """认知闸：六问（用 decide.py 真跑）"""
    return _run("decide.py", [cmd], 120)

def probe_speech(cmd):
    """言行闸：四道关（用 speech_gate.py 检查文本）"""
    return _run("speech_gate.py", [cmd], 60)

def probe_official(cmd):
    """官方门禁：字段合规（用 official_gate.py 自检模式）"""
    try:
        sys.path.insert(0, HOME + "/tools")
        from official_gate import wrap, check
        ok, why = check(wrap(cmd))
        return ok, why
    except Exception as e:
        return False, str(e)[:60]

def probe_refute(cmd):
    """反方：自演一层（用 refute_gate.py·三刀齐且判过）"""
    if not os.path.exists(HOME + "/tools/refute_gate.py"):
        return False, "refute_gate.py 缺"
    return _run("refute_gate.py", ["--check", cmd], 30)

PROBES = [
    ("认知六问", probe_decide),
    ("言行闸", probe_speech),
    ("官方门禁", probe_official),
    ("反方", probe_refute),
]

def main():
    if len(sys.argv) < 2:
        print(__doc__); return 1
    cmd = " ".join(sys.argv[1:])
    t = tier(cmd)
    need = NEED[t]
    votes = []
    detail = []
    for name, fn in PROBES:
        ok, ev = fn(cmd)
        if ok: votes.append(name); detail.append("%s=✅" % name)
        else: detail.append("%s=❌(%s)" % (name, ev[:40]))
        if len(votes) >= need: break
    # ★ 2026-11-15 补(照老七"precheck必须有反证出口"+本体认"我们没满足"):
    #   判据: 不许裸 PASS|PASS 必须引证据|三态 PASS/FAIL/UNVERIFIED
    _have = len(votes)
    if _have >= need:
        verdict = "PASS"
        evidence_ref = "votes=%s|need=%d|tier=%s" % (",".join(votes), need, t)
    elif _have == 0:
        verdict = "FAIL"
        evidence_ref = "无任何系统探针通过"
    else:
        verdict = "UNVERIFIED"
        evidence_ref = "缺 %d 票(有:%s|需:%d)" % (need - _have, ",".join(votes) or "无", need)
    passed = verdict == "PASS"
    rec = {"ts": datetime.datetime.now().isoformat(timespec="seconds"), "cmd": cmd[:120],
           "tier": t, "need": need, "votes": votes, "passed": passed,
           "verdict": verdict, "evidence_ref": evidence_ref, "detail": detail}
    try:
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception: pass
    print("★ 闸链 · 档=%s · 需%d票 · 得%d票(%s)" % (t, need, len(votes), ",".join(votes) or "无"))
    for d in detail: print("   " + d)
    print("★ 判: %s" % verdict)
    print("★ 证据引用: %s" % evidence_ref)
    if verdict == "PASS":
        return 0
    if verdict == "FAIL":
        return 2
    return 3   # UNVERIFIED

if __name__ == "__main__":
    sys.exit(main())
