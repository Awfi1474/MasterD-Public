#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·规则巡检 rule_patrol.py
★ 董事长令(2026-11-15): 路线1 —— 规则能干的不用模型
★ 判据: 「模型用来判断·不用来数数｜数数的事规则能干就别烧钱」

零模型调用·纯规则:
  · 服务活没活（端口/进程）
  · 账有没有异常（不符/失败率）
  · 未读积压（多少条·卡多久）
  · 磁盘/日志（会不会爆）
  · 自家口通不通（自检自己的 HTTP）
"""
import os, json, subprocess, datetime, urllib.request

HOME = "/opt/masterd-wudi"
OUT = HOME + "/data/rule_patrol.jsonl"

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")

def sh(c, t=10):
    try:
        r = subprocess.run(c, shell=True, capture_output=True, text=True, timeout=t)
        return r.returncode == 0, (r.stdout or r.stderr or "").strip()
    except Exception as e:
        return False, str(e)[:80]

def http(url, t=5):
    try:
        with urllib.request.urlopen(url, timeout=t) as r:
            return True, r.status
    except Exception as e:
        return False, str(e)[:60]

# ---------- 规则检查（全部零模型） ----------
def check_services():
    """关键服务: body_worker / body_daemon"""
    out = []
    for name, pat in (("body_worker", "body_worker.py"), ("body_daemon", "body_daemon.py")):
        ok, o = sh("pgrep -f '%s' | head -1" % pat)
        out.append({"chk": "service:" + name, "ok": bool(o.strip()), "detail": o.strip()[:40]})
    return out

def check_ports():
    out = []
    for port in (28430,):
        ok, status = http("http://127.0.0.1:%d/health" % port)
        out.append({"chk": "port:%d" % port, "ok": ok, "detail": str(status)})
    return out

def check_ledger():
    """账里有没有「不符」/失败率"""
    out = []
    p = HOME + "/data/send_ledger.jsonl"
    if os.path.exists(p):
        bad = 0; tot = 0; today = ts()[:10]
        for l in open(p, encoding="utf-8", errors="ignore"):
            if not l.strip():
                continue
            try:
                d = json.loads(l)
            except Exception:
                continue
            if str(d.get("ts", ""))[:10] != today:
                continue
            tot += 1
            if d.get("verdict") == "不符":
                bad += 1
        out.append({"chk": "ledger:send", "ok": bad == 0,
                    "detail": "今日 %d 条·不符 %d 条" % (tot, bad)})
    return out

def check_unread():
    """未读积压"""
    try:
        import importlib.util as iu
        sp = iu.spec_from_file_location("bw", HOME + "/tools/body_worker.py")
        m = iu.module_from_spec(sp); sp.loader.exec_module(m)
        n = len(m.unread())
        return [{"chk": "unread", "ok": n < 500, "detail": "未读 %d 条" % n}]
    except Exception as e:
        return [{"chk": "unread", "ok": False, "detail": "err " + str(e)[:60]}]

def check_disk():
    out = []
    ok, o = sh("df -h /opt | tail -1 | awk '{print $5}'")
    pct = (o or "").strip().rstrip("%")
    try:
        v = int(pct)
    except Exception:
        v = 0
    out.append({"chk": "disk", "ok": v < 85, "detail": "根盘 %s%%" % (pct or "?")})
    lg = HOME + "/logs/body_daemon.log"
    if os.path.exists(lg):
        mb = os.path.getsize(lg) // (1024 * 1024)
        out.append({"chk": "log:daemon", "ok": mb < 5, "detail": "日志 %d MB" % mb})
    return out

def check_cost():
    """用量闸: 今日花费"""
    try:
        import importlib.util as iu
        sp = iu.spec_from_file_location("tg", HOME + "/tools/token_guard.py")
        m = iu.module_from_spec(sp); sp.loader.exec_module(m)
        s = m.today_spent(); lim = m.get_limit()
        return [{"chk": "cost", "ok": s < lim, "detail": "今日 ¥%.2f / ¥%.2f" % (s, lim)}]
    except Exception as e:
        return [{"chk": "cost", "ok": False, "detail": "err " + str(e)[:50]}]

def patrol():
    res = []
    for fn in (check_services, check_ports, check_ledger, check_unread, check_disk, check_cost):
        try:
            res.extend(fn())
        except Exception as e:
            res.append({"chk": fn.__name__, "ok": False, "detail": "ERR " + str(e)[:60]})
    bad = [r for r in res if not r["ok"]]
    rec = {"ts": ts(), "total": len(res), "bad": len(bad), "items": res}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec

if __name__ == "__main__":
    r = patrol()
    print("规则巡检 @ %s | 共 %d 项 | 异常 %d 项 | 模型调用 0 次"
          % (r["ts"][11:], r["total"], r["bad"]))
    for it in r["items"]:
        print("  %s %-16s %s" % ("✅" if it["ok"] else "🔴", it["chk"], it["detail"]))