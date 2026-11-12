#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""a2a_gate.py —— 老五 A2A 唤醒闸 (2026-11-08)
================================================================
判据(老三家族版+老五加第三条):
  "收到 != 处理 | 处理 != 干完 | 干完 != 复诊过"
  submitted != working | working要有心跳(updated_at) | 超时标 stalled
用法:
  a2a_gate.py recv <from> <msg_id|-> <摘要>   -> 落账 status=working
  a2a_gate.py done <msg_id> <结果>            -> status=completed
  a2a_gate.py ask  <msg_id> <问题>            -> status=input-required(要澄清)
  a2a_gate.py auth <msg_id> <啥>              -> status=auth-required(要授权·资金类)
  a2a_gate.py status [msg_id]                 -> 查(默认全部working)
  a2a_gate.py beat <msg_id> [进度]            -> 心跳(更新updated_at)
================================================================
"""
import sqlite3, sys, datetime, hashlib, json
HOME = "/opt/masterd-wudi"
DB = HOME + "/memory/memory.db"


def _stall_min():
    """★ 照老三'阈值进档不进代码':读 THRESHOLDS.json 的 stalled_min"""
    try:
        import json as _j
        return int(_j.load(open("/opt/masterd-wudi/memory/THRESHOLDS.json")).get("stalled_min",30))
    except Exception:
        return 30
_STALL_MIN = _stall_min()

def now():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")

def ensure(con):
    con.execute("""CREATE TABLE IF NOT EXISTS a2a_inbox (
      msg_id TEXT PRIMARY KEY, frm TEXT, summary TEXT,
      status TEXT, note TEXT, created_at TEXT, updated_at TEXT)""")
    con.commit()

def recv(frm, mid, summary):
    con = sqlite3.connect(DB, timeout=10); ensure(con)
    if not mid or mid == "-":
        mid = "local-" + hashlib.md5((frm + now() + summary).encode()).hexdigest()[:10]
    t = now()
    con.execute("""INSERT OR REPLACE INTO a2a_inbox
      (msg_id,frm,summary,status,note,created_at,updated_at) VALUES (?,?,?,?,?,?,?)""",
      (mid, frm, summary[:200], "submitted", "门收到·待本体亲claim(器不替)", t, t))
    con.commit(); con.close()
    print("SUBMITTED %s <- %s | %s (待本体亲claim)" % (mid, frm, summary[:50]))

# ★ 2026-11-08 加(照董事长令·基础三环): ①事件驱动 ②链式传动
NEXT_OF = {  # 链的下家规则(照老三:不是排队·是按角色叫)
    "self": "verify",   # 自证完 -> 叫他证(老五)
    "verify": "audit",  # 他证完 -> 叫审核(老七)
}

def _is_real_delivery(rec):
    """技术总监[封印三条]·证明须[第三方能复算]
    校验:① event==task_completed/delivery ② proof=文件路径(他方能读+算md5)·不是自报md5字符串
    """
    ev = str(rec.get("event") or "")
    if ev not in ("task_completed", "delivery"):
        return False, "非真交付(event=%s)" % ev
    proof = rec.get("artifact_proof") or rec.get("proof") or ""
    if isinstance(proof, dict):
        p = proof.get("path") or proof.get("file") or ""
        if not p:
            return False, "proof无路径(自报md5不算·要第三方能复算)"
        import os
        if not os.path.exists(str(p)):
            return False, "proof路径不存在(他方复算不了):%s" % str(p)[:60]
        return True, "ok(可复算:%s)" % str(p)[:60]
    return False, "proof格式错(要{path,...}·非自报字符串)"

def _notify(to_role, ctx, msg):
    """链式传动: 干完自动叫下家(带context_id·不等轮询)"""
    import urllib.request
    try:
        TOK = open("/opt/masterd-wudi/data/hub.token").read().strip()
    except Exception:
        TOK = ""
    # 角色->标准名
    role2name = {"verify":"lao5","audit":"lao7","self":"lao6","exec":"lao6"}
    to = role2name.get(to_role, to_role)
    body = {"from":"lao5","to":to,"context_id":ctx,"message":"【链式传动·自动叫下家】"+msg}
    try:
        req = urllib.request.Request("https://huokeji.vip/a2a/message",
              data=json.dumps(body, ensure_ascii=False).encode(),
              headers={"Content-Type":"application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=10).read()
        # 同步HUB真源
        if TOK:
            req2 = urllib.request.Request("http://43.161.244.136:28800/a2a/message",
                   data=json.dumps(body, ensure_ascii=False).encode(),
                   headers={"Content-Type":"application/json","Authorization":"Bearer "+TOK}, method="POST")
            urllib.request.urlopen(req2, timeout=10).read()
        return True
    except Exception as e:
        # fail-visible: 记失败
        try:
            with open("/opt/masterd-wudi/data/chain_alerts.jsonl","a") as f:
                f.write(json.dumps({"ts":now(),"to":to,"ctx":ctx,"err":str(e)[:60]},ensure_ascii=False)+"\n")
        except Exception: pass
        return False

def done(mid, result, ctx=None, next_role=None, _ev=None, _proof=None):
    con = sqlite3.connect(DB, timeout=10); ensure(con)
    _pfj = json.dumps(_proof,ensure_ascii=False) if isinstance(_proof,(dict,list)) else str(_proof or "")
    con.execute("UPDATE a2a_inbox SET status='completed',note=?,updated_at=?,event=?,artifact_proof=?,action_type=? WHERE msg_id=?",
                (result[:200], now(), str(_ev or ""), _pfj, "task_completed" if _ev=="task_completed" else str(_ev or ""), mid))
    con.commit(); con.close()
    print("COMPLETED %s | %s" % (mid, result[:50]))
    # ★ 事件驱动+链式传动:干完立刻自动叫下家(不等轮询)
    if next_role:
        # ★ 技术总监令:双重校验(event==task_completed + proof非空)·不过→抛异常(不闷头往下)
        _rec = {"event": _ev, "artifact_proof": _proof}
        _ok, _why = _is_real_delivery(_rec)
        if not _ok:
            # 封印②:不过 → 发 task_rejected(不闷头往下)
            try:
                _rej = {"from":"lao5","to":"lao6","context_id":ctx or "chain",
                        "event":"task_rejected","message":"【task_rejected】%s 的交付被链拒: %s" % (mid[:24], _why)}
                import urllib.request as _u
                TOK2 = open("/opt/masterd-wudi/data/hub.token").read().strip()
                for _url,_h in [("https://huokeji.vip/a2a/message",{}),
                                ("http://43.161.244.136:28800/a2a/message",{"Authorization":"Bearer "+TOK2})]:
                    _h2 = dict(_h); _h2["Content-Type"]="application/json"
                    try:
                        _u.urlopen(_u.Request(_url,data=json.dumps(_rej,ensure_ascii=False).encode(),headers=_h2,method="POST"),timeout=8).read()
                    except Exception: pass
            except Exception: pass
            raise ValueError("链·双重校验不过(发task_rejected): %s" % _why)
        okc = _notify(next_role, ctx or "chain", "我(老五)干完[%s]·下家=%s·请接" % (mid[:24], next_role))
        print("CHAIN %s -> %s : %s" % (mid[:20], next_role, "已叫" if okc else "失败(记链alerts)"))
def ask(mid, q):
    """不确定 -> input-required(照官方A2A:别硬说完成)"""
    con = sqlite3.connect(DB, timeout=10); ensure(con)
    con.execute("UPDATE a2a_inbox SET status='input-required',note=?,updated_at=? WHERE msg_id=?",
                (("待澄清:"+q)[:200], now(), mid))
    con.commit(); con.close()
    print("INPUT-REQUIRED %s | %s" % (mid, q[:50]))

def auth(mid, what):
    """★ 2026-11-12 加(照官方A2A 3.7 + 董事长'转资金要反问核实'): 要授权->auth-required
       判据: L0铁拦类(资金/密钥/不可逆)->auth-required(等人批)·非硬拒"""
    con = sqlite3.connect(DB, timeout=10); ensure(con)
    con.execute("UPDATE a2a_inbox SET status='auth-required',note=?,updated_at=? WHERE msg_id=?",
                (("待授权:"+what)[:200], now(), mid))
    con.commit(); con.close()
    print("AUTH-REQUIRED %s | %s" % (mid, what[:50]))

def beat(mid, prog):
    con = sqlite3.connect(DB, timeout=10); ensure(con)
    con.execute("UPDATE a2a_inbox SET updated_at=?,note=? WHERE msg_id=?",
                (now(), prog[:200], mid))
    con.commit(); con.close()
    print("BEAT %s | %s" % (mid, prog[:50]))

def status(mid=None):
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    if mid:
        rows = con.execute("SELECT * FROM a2a_inbox WHERE msg_id=?", (mid,)).fetchall()
    else:
        rows = con.execute("SELECT * FROM a2a_inbox ORDER BY updated_at DESC LIMIT 30").fetchall()
    n_w = n_c = n_s = 0
    for r in rows:
        # stalled: working 且 updated_at 超 30 分钟
        st = r[3]
        try:
            dt = datetime.datetime.strptime(r[6][:19], "%Y-%m-%dT%H:%M:%S")
            age = (datetime.datetime.now() - dt).total_seconds() / 60
        except Exception:
            age = 0
        if st == "working" and age > _STALL_MIN:
            st = "stalled"
        if st == "working": n_w += 1
        elif st == "completed": n_c += 1
        elif st == "stalled": n_s += 1
        print("[%s] %-9s age=%.0fm  %s <- %s | %s" % (r[0][:16], st, age, r[2][:34], r[1][:14], r[5][:30]))
    print("--- summary: working=%d completed=%d stalled=%d ---" % (n_w, n_c, n_s))
    con.close()

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(0)
    c = a[0]
    if c == "recv":   recv(a[1], a[2] if len(a) > 2 else "-", " ".join(a[3:]) if len(a) > 3 else "")
    elif c == "done":
        # done <mid> <result> [ctx] [next_role] [event] [proof]
        _r = a[2] if len(a)>2 else ""
        _ctx = a[3] if len(a)>3 else None
        _nx = a[4] if len(a)>4 else None
        _ev = a[5] if len(a)>5 else None
        _pf = a[6] if len(a)>6 else None
        if _pf:
            try: _pf = json.loads(_pf)
            except Exception: pass
        done(a[1], _r, _ctx, _nx, _ev, _pf)
    elif c == "beat": beat(a[1], " ".join(a[2:]))
    elif c == "ask": ask(a[1], " ".join(a[2:]))
    elif c == "auth": auth(a[1], " ".join(a[2:]))
    elif c == "status": status(a[1] if len(a) > 1 else None)
    else: print("unknown:", c)
