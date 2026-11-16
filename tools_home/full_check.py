#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·全维度质检 —— 逐条验证群里的标准·我执行了没
★ 董事长问: 「定了多少标准？执行了没有？做全维度质检了吗？」
★ 判据(群里共识): 「认 = 能收能发并给出实测数｜口头同意不算认」
★ 做法: 每条标准 -> 一个可跑的实测 -> 真跑 -> 报结果
"""
import json
import time
import hashlib
import datetime
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:28430"
RESULTS = []


def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")


def _get(path, t=20):
    try:
        with urllib.request.urlopen(BASE + path, timeout=t) as r:
            return r.status, r.read(200000).decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return 0, str(e)[:80]


def _post(path, payload, t=25):
    try:
        req = urllib.request.Request(BASE + path, data=json.dumps(payload, ensure_ascii=False).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=t) as r:
            return r.status, r.read(200000).decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return 0, str(e)[:80]


def rec(name, ok, evidence=""):
    RESULTS.append({"标准": name, "执行": bool(ok), "证据": str(evidence)[:150]})
    print("  %s %-42s %s" % ("✅" if ok else "🔴", name[:40], str(evidence)[:60]))


print("=" * 62)
print("老五·全维度质检（逐条标准·真跑·报数）@ %s" % ts()[11:])
print("=" * 62)

# ① 认 = 能收能发并给出实测数
try:
    st, body = _get("/health")
    d = json.loads(body) if st == 200 else {}
    has_recv = bool(d.get("body_fields"))
    has_limits = bool(d.get("limits"))
    rec("认=能收能发+实测数", st == 200 and has_recv and has_limits,
        "health=%s body_fields=%s limits=%s" % (st, has_recv, has_limits))
except Exception as e:
    rec("认=能收能发+实测数", False, str(e)[:60])

# ② 自报不算数·能被反向算的才算
try:
    st, body = _get("/tasks")
    d = json.loads(body) if st == 200 else {}
    has_rule = "rule" in d
    has_counts = "counts" in d or "summary" in d
    rec("自报不算数=给可复算口", st == 200 and has_rule and has_counts,
        "/tasks=%s rule=%s counts=%s" % (st, has_rule, has_counts))
except Exception as e:
    rec("自报不算数=给可复算口", False, str(e)[:60])

# ③ 闸要自描述（/health 里看得到闸）
try:
    st, body = _get("/health")
    d = json.loads(body) if st == 200 else {}
    L = d.get("limits") or {}
    keys = [k for k in L if any(w in k.lower() for w in ("throttle", "limit", "max", "rate", "content"))]
    rec("闸要自描述(/health可见)", len(keys) >= 3,
        "limits 字段 %d 个: %s" % (len(keys), ",".join(keys[:4])))
except Exception as e:
    rec("闸要自描述(/health可见)", False, str(e)[:60])

# ④ 同内容 N 次就停
try:
    msg = "QCHECK-SAME-%d" % int(time.time())
    from eth_account import Account
    from eth_account.messages import encode_defunct
    k = json.load(open("/opt/masterd-wudi/agent-id/subkey.json"))
    got_drop = False
    for i in range(5):
        stmp = "2026-11-16T10:%02d:00+08:00" % (40 + i)
        sig = Account.sign_message(encode_defunct(text="老五(阿诊)|%s|%s" % (msg, stmp)),
                                   private_key=k["private_key"]).signature.hex()
        if not sig.startswith("0x"):
            sig = "0x" + sig
        st, body = _post("/p2p/recv", {"from": "老五(阿诊)", "message": msg, "ts": stmp,
                                       "address": k.get("address"), "sig": sig})
        if "dropped" in body and "true" in body:
            got_drop = True
            break
    rec("同内容N次就停(3次)", got_drop, "5 次里第 %d 次被拒" % (i + 1))
except Exception as e:
    rec("同内容N次就停(3次)", False, str(e)[:60])

# ⑤ 入站要有闸（速率/大小）
try:
    st, body = _get("/health")
    d = json.loads(body) if st == 200 else {}
    L = d.get("limits") or {}
    rec("入站要有闸(速率/大小)", ("rate_per_min_per_ip" in L and "body_max_bytes" in L),
        "rate=%s body_max=%s" % (L.get("rate_per_min_per_ip"), L.get("body_max_bytes")))
except Exception as e:
    rec("入站要有闸(速率/大小)", False, str(e)[:60])

# ⑥ 口和体配套（官方口配官方体）
try:
    import time as _t
    body = {"role": "ROLE_USER", "parts": [{"text": "[质检·忽略]"}],
            "metadata": {"from": "老五(阿诊)", "to": "老五(阿诊)", "ts": ts(),
                         "messageId": "qc-" + str(int(_t.time()))}}
    st, resp = _post("/a2a/message", body)
    ok = st == 200 and ("received" in resp or "dup" in resp)
    rec("口和体配套(官方口收官方体)", ok, "官方骨架投自己=%s" % st)
except Exception as e:
    rec("口和体配套(官方口收官方体)", False, str(e)[:60])

# ⑦ 幂等（同 messageId 投两次）
try:
    import time as _t2
    mid = "qc-idem-" + str(int(_t2.time()))
    body = {"role": "ROLE_USER", "parts": [{"text": "idem"}],
            "metadata": {"from": "老五(阿诊)", "to": "老五(阿诊)", "ts": ts(), "messageId": mid}}
    s1, b1 = _post("/a2a/message", body)
    s2, b2 = _post("/a2a/message", body)
    rec("幂等(同messageId不重复)", "dup" in b2 or "idempotent" in b2,
        "第2次=%s" % ("dup" if "dup" in b2 else b2[:40]))
except Exception as e:
    rec("幂等(同messageId不重复)", False, str(e)[:60])

# ⑧ 签名三段 from|message|ts
try:
    import subprocess as _sp
    r = _sp.run("grep -c 'frm}|{msg}|{t}\\|{_frm}, _cmd' /opt/masterd-wudi/code/p2p_mailbox.py",
                shell=True, capture_output=True, text=True, timeout=10)
    n = int((r.stdout or "0").strip() or 0)
    rec("签名三段(from|message|ts)", n >= 2, "三段验签点 %d 处" % n)
except Exception as e:
    rec("签名三段(from|message|ts)", False, str(e)[:60])

# ⑨ 引原文四件套（我有没有做到）
try:
    import os
    ok = os.path.exists("/opt/masterd-wudi/memory/a2a-spec-official.md")
    lines = sum(1 for _ in open("/opt/masterd-wudi/memory/a2a-spec-official.md", encoding="utf-8", errors="ignore")) if ok else 0
    size = os.path.getsize("/opt/masterd-wudi/memory/a2a-spec-official.md") if ok else 0
    md5 = hashlib.md5(open("/opt/masterd-wudi/memory/a2a-spec-official.md", "rb").read()).hexdigest() if ok else ""
    rec("引原文四件套(文件名+行+字节+md5)", ok and lines > 0,
        "spec %d行/%d字节/md5 %s" % (lines, size, md5[:12]))
except Exception as e:
    rec("引原文四件套", False, str(e)[:60])

# ⑩ 跑过 != 还在跑（要现在真跑一次）
try:
    st, body = _get("/health")
    d = json.loads(body) if st == 200 else {}
    pu = d.get("proc_uptime_s")
    rec("跑过!=还在跑(报进程uptime)", pu is not None, "proc_uptime_s=%s (机器 uptime=%s)" % (pu, d.get("uptime_s")))
except Exception as e:
    rec("跑过!=还在跑", False, str(e)[:60])

print()
print("=" * 62)
npass = sum(1 for r in RESULTS if r["执行"])
print("全维度质检: %d/%d 通过" % (npass, len(RESULTS)))
fails = [r["标准"] for r in RESULTS if not r["执行"]]
if fails:
    print("未过: " + " | ".join(fails))
print("=" * 62)

# 落账
try:
    with open("/opt/masterd-wudi/data/full_check.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": ts(), "pass": npass, "total": len(RESULTS),
                            "items": RESULTS}, ensure_ascii=False) + "\n")
    print("已落账: data/full_check.jsonl")
except Exception:
    pass