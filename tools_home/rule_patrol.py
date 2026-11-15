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

def http(url, t=12):   # FIX 2026-11-15: 5s 太短 -> 误判(oS): 老六教[别超时就判慢]
    try:
        with urllib.request.urlopen(url, timeout=t) as r:
            return True, r.status
    except Exception as e:
        return False, str(e)[:60]

# ---------- 规则检查（全部零模型） ----------
def _expected_state():
    """★ 期望运行状态（董事长令停了的服务登记在这·巡检按此判）"""
    import json as _j, os as _os
    p = HOME + "/state/patrol_expected.json"
    try:
        return _j.load(open(p))
    except Exception:
        return {}


def check_services():
    """关键服务: 按期望状态判断（该跑必须跑·该停必须停）"""
    out = []
    exp = _expected_state()
    for name, pat in (("body_worker", "body_worker.py"), ("body_daemon", "body_daemon.py"),
                      ("selfdrive_loop", "selfdrive_loop.py")):
        # ★ 修(照实: pgrep -f 'body_worker.py' 会匹配到自己的 bash 命令行 -> 永远报"活着")
        #   判据: 「pgrep -f 匹配的是整条命令行·包括执行它的 shell」
        ok, o = sh("pgrep -f 'python3 .*%s' | grep -v $$ | head -1" % pat)
        running = bool((o or "").strip())
        want = str(exp.get(name, "run"))     # 默认该跑
        if want == "stopped":
            # 期望停 -> 停了才算 ok
            out.append({"chk": "service:" + name, "ok": not running,
                        "detail": ("已按令停 ✅" if not running else "🔴 应停但还在跑 pid=%s" % (o or "").strip()[:12])})
        else:
            out.append({"chk": "service:" + name, "ok": running,
                        "detail": (o or "").strip()[:40] if running else "🔴 应跑但没跑"})
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

def check_guard():
    """调模型但没过闸的（照实: 防止偷偷烧钱）"""
    out = []
    try:
        import importlib.util as _iu
        sp = _iu.spec_from_file_location("ac", HOME + "/tools/anticheat.py")
        m = _iu.module_from_spec(sp)
        sp.loader.exec_module(m)
        r = m.report(save=False)
        risk = r["结果"]["未过闸"]
        out.append({"chk": "guard:llm", "ok": risk == 0,
                    "detail": "调模型 %d 个·未过闸 %d" % (r["结果"]["总调模型文件"], risk)})
    except Exception as e:
        out.append({"chk": "guard:llm", "ok": False, "detail": "err " + str(e)[:50]})
    return out


def check_fail_ledger():
    """失败必须入账（照实: 账里只有成功是宣传）"""
    out = []
    try:
        import importlib.util as _iu2
        sp = _iu2.spec_from_file_location("fl", HOME + "/tools/fail_ledger.py")
        m = _iu2.module_from_spec(sp)
        sp.loader.exec_module(m)
        st = m.stats()
        tot = sum(st.values()) if st else 0
        out.append({"chk": "fail:ledger", "ok": tot < 200,
                    "detail": "今日失败落账 %d 条" % tot})
    except Exception as e:
        out.append({"chk": "fail:ledger", "ok": False, "detail": "err " + str(e)[:50]})
    return out


def check_orphan():
    """卡死的只读孤儿进程（照实: 一个 grep 卡2天12小时吃92%CPU）"""
    out = []
    try:
        ok, o = sh("ps -eo pid,ppid,etime,pcpu,comm --sort=-pcpu 2>/dev/null | head -12")
        stuck = []
        SAFE = ("grep", "find", "sort", "du", "awk", "head", "tail", "cat", "xargs", "sed")
        for line in (o or "").splitlines()[1:]:
            parts = line.split()
            if len(parts) < 5:
                continue
            pid, ppid, etime, pcpu, comm = parts[0], parts[1], parts[2], parts[3], parts[4]
            try:
                cpu = float(pcpu)
            except Exception:
                continue
            if "-" in etime and cpu > 40 and ppid == "1" and comm in SAFE:
                stuck.append("%s(%s,%s%%)" % (comm, pid, pcpu))
        out.append({"chk": "orphan:cpu", "ok": len(stuck) == 0,
                    "detail": ("卡死 %d 个: %s" % (len(stuck), ",".join(stuck[:3]))) if stuck else "无卡死孤儿"})
    except Exception as e:
        out.append({"chk": "orphan:cpu", "ok": False, "detail": "err " + str(e)[:50]})
    return out


def check_cron():
    """cron 健康（照实: 引用了不存在的脚本 -> 每轮白跑静默失败）"""
    out = []
    try:
        import importlib.util as _iu3
        sp = _iu3.spec_from_file_location("ch3", HOME + "/tools/cron_health.py")
        m = _iu3.module_from_spec(sp)
        sp.loader.exec_module(m)
        r = m.check(dry=True)
        res = r["结果"]
        out.append({"chk": "cron:health", "ok": res["缺失数"] == 0 and res["错误日志数"] == 0,
                    "detail": "缺失%d·调模型%d·日志错%d" % (res["缺失数"], len(res["会调模型的"]), res["错误日志数"])})
    except Exception as e:
        out.append({"chk": "cron:health", "ok": False, "detail": "err " + str(e)[:50]})
    return out


def check_wake_switch():
    """门偷偷叫醒本体（照实: 本体停着还在花钱的真因）
       判据: 「说冻结不算|看账有没有涨才算」"""
    out = []
    try:
        import os as _o
        import json as _j
        import datetime as _dt
        sw = HOME + "/state/body_wake_disabled.json"
        exists = _o.path.exists(sw)
        recent = 0
        up = HOME + "/data/llm_usage.jsonl"
        if _o.path.exists(up):
            now = _dt.datetime.now()
            for l in open(up, encoding="utf-8", errors="ignore").readlines()[-200:]:
                if not l.strip():
                    continue
                try:
                    d = _j.loads(l)
                    t = _dt.datetime.strptime(str(d.get("ts"))[:19], "%Y-%m-%dT%H:%M:%S")
                    if (now - t).total_seconds() < 600:
                        recent += 1
                except Exception:
                    continue
        ok = (not exists) or (recent == 0)
        detail = "开关%s|近10分钟调用%d" % ("在" if exists else "不在", recent)
        if exists and recent > 0:
            detail = detail + " 🔴 开关在但还在花钱"
        out.append({"chk": "wake:switch", "ok": ok, "detail": detail})
    except Exception as e:
        out.append({"chk": "wake:switch", "ok": False, "detail": "err " + str(e)[:50]})
    return out


def patrol():
    res = []
    for fn in (check_services, check_ports, check_ledger, check_unread, check_disk, check_cost,
               check_guard, check_fail_ledger, check_orphan, check_cron, check_wake_switch):
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