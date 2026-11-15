#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·意图路由 intent_router.py —— 照老大定的规矩
★ 老大规矩(2026-11-15 20:xx):
   ① 「查数归脚本｜判断归 LLM｜别用锤子拧螺丝」
   ② 「省钱的验证只有一个：账单条数有没有新增」
   ③ 「高频低级活交给 LLM = 花钱买不确定性」
★ 做法: 命中「查数」意图 → 直接跑脚本返回 ¥0；没命中 → 才交给 LLM
"""
import os, re, json, subprocess, datetime

HOME = "/opt/masterd-wudi"
HIT_LOG = HOME + "/data/intent_router.jsonl"

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")

def _sh(cmd, t=12):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=t)
        return r.returncode == 0, (r.stdout or r.stderr or "").strip()
    except Exception as e:
        return False, str(e)[:80]

# ---------------- 意图规则表（零模型） ----------------
def _svc_state(msg):
    """查服务活没活"""
    ok, o = _sh("pgrep -f 'body_worker.py|body_daemon.py|selfdrive_loop.py' | wc -l")
    n = (o or "0").strip()
    ok2, o2 = _sh("curl -s -m 12 -o /dev/null -w '%{http_code}' http://127.0.0.1:28430/health")
    return True, "在跑进程 %s 个｜自家口 %s" % (n, (o2 or "?").strip())

def _ledger_count(msg):
    """查账几条"""
    ok, o = _sh("wc -l < %s/data/send_ledger.jsonl" % HOME)
    ok2, o2 = _sh("grep -c '不符' %s/data/send_ledger.jsonl 2>/dev/null || echo 0" % HOME)
    return True, "发信账 %s 条｜不符 %s 条" % ((o or "?").strip(), (o2 or "0").strip())

def _unread_count(msg):
    """查未读几条"""
    ok, o = _sh("python3 -c \"import importlib.util as iu;sp=iu.spec_from_file_location('bw','%s/tools/body_worker.py');m=iu.module_from_spec(sp);sp.loader.exec_module(m);print(len(m.unread()))\"" % HOME, t=25)
    return True, "未读 %s 条" % (o or "?").strip()

def _port_check(msg):
    """查端口通不通"""
    m = re.search(r"\b(\d{4,5})\b", msg or "")
    port = m.group(1) if m else "28430"
    ok, o = _sh("curl -s -m 12 -o /dev/null -w '%%{http_code} %%{time_total}s' http://127.0.0.1:%s/health" % port)
    return True, "端口 %s: %s" % (port, (o or "?").strip())

def _cost_today(msg):
    """查花多少钱"""
    ok, o = _sh("python3 %s/tools/token_guard.py | head -1" % HOME, t=20)
    return True, (o or "?").strip()

def _disk_usage(msg):
    """查磁盘"""
    ok, o = _sh("df -h /opt | tail -1")
    return True, (o or "?").strip()

def _card_lookup(msg):
    """查知识卡"""
    ok, o = _sh("python3 %s/tools/know_cards.py %s" % (HOME, "'" + (msg or "")[:80].replace("'", "") + "'"), t=20)
    return True, (o or "无匹配卡").strip()[:400]

# (正则, 函数, 说明)
RULES = [
    (r"(在不在|活不活|活着|服务.*状态|进程.*在|投产没|health)", _svc_state, "服务状态"),
    (r"(账.*几条|几条账|账本|账里|不符.*几条|发信.*多少)", _ledger_count, "账条数"),
    (r"(未读.*几条|几封|信堆|没读)", _unread_count, "未读条数"),
    (r"(端口|通不通|连不上|refused|超时).*\d{4,5}|\d{4,5}.*(通|不通)", _port_check, "端口探测"),
    (r"(花了多少|花费|成本|多少钱|budget|额度)", _cost_today, "花费"),
    (r"(磁盘|disk|空间够|盘满)", _disk_usage, "磁盘"),
]

def route(msg):
    """★ 命中就返回 (True, 结果, 规则名)；没命中 (False, None, None)
       全程 ¥0·不调模型
    """
    text = (msg or "").strip()
    if not text:
        return False, None, None
    for pat, fn, name in RULES:
        if re.search(pat, text, re.I):
            try:
                ok, out = fn(text)
                rec = {"ts": ts(), "rule": name, "hit": True, "msg": text[:120],
                       "out": str(out)[:200], "cost": 0}
                with open(HIT_LOG, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                return True, out, name
            except Exception as e:
                return False, None, None
    rec = {"ts": ts(), "hit": False, "msg": text[:120], "cost": 0}
    try:
        with open(HIT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return False, None, None

def stats():
    """命中率统计（验省钱的第二证据）"""
    if not os.path.exists(HIT_LOG):
        return {}
    tot = hit = 0
    by = {}
    for l in open(HIT_LOG, encoding="utf-8", errors="ignore"):
        if not l.strip():
            continue
        try:
            d = json.loads(l)
        except Exception:
            continue
        if str(d.get("ts", ""))[:10] != ts()[:10]:
            continue
        tot += 1
        if d.get("hit"):
            hit += 1
            by[d.get("rule")] = by.get(d.get("rule"), 0) + 1
    return {"total": tot, "hit": hit, "rate": round(100.0 * hit / max(1, tot), 1), "by_rule": by}

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--stats":
        print(json.dumps(stats(), ensure_ascii=False, indent=1))
    elif len(sys.argv) > 1:
        q = " ".join(sys.argv[1:])
        ok, out, name = route(q)
        print(("命中[%s] → " % name if ok else "未命中·交给LLM → ") + str(out))
    else:
        tests = [
            "老五你在不在",
            "账里几条了",
            "未读有几封",
            "28430 端口通不通",
            "今天花了多少钱",
            "磁盘还够吗",
            "这条需求该怎么设计",
        ]
        for t in tests:
            ok, out, name = route(t)
            print("%-24s → %s %s" % (t, ("[%s] ✅¥0" % name) if ok else "未命中(要LLM)", str(out)[:60]))