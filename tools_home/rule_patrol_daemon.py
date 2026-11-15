#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""规则巡检常驻 rule_patrol_daemon.py
★ 董事长令(2026-11-15): 路线1 规则优先(零模型)·路线3 花费上限
★ 判据: 「巡检是数数·不是判断题｜数数用规则·判断才用模型」
★ 异常时: 只在【真异常】且【花费未超】时才调模型判断(可选)
"""
import os, sys, json, time, signal, datetime, subprocess

HOME = "/opt/masterd-wudi"
sys.path.insert(0, HOME + "/tools")
LOCK = HOME + "/state/rule_patrol.lock"
HB = HOME + "/state/rule_patrol_heartbeat.json"
LOG = HOME + "/logs/rule_patrol.log"
CYCLE = int(os.environ.get("CYCLE_SEC", "300"))       # 默认 5 分钟一次(够用·不吃资源)

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")

def log(m):
    line = "[%s] %s" % (ts(), m)
    print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        if os.path.exists(LOG) and os.path.getsize(LOG) > 3 * 1024 * 1024:
            os.replace(LOG, LOG + ".1")
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def acquire_lock():
    if os.path.exists(LOCK):
        try:
            d = json.load(open(LOCK))
            os.kill(int(d.get("pid", 0)), 0)
            log("已有巡检在跑 pid=%s" % d.get("pid"))
            sys.exit(0)
        except Exception:
            pass
    os.makedirs(os.path.dirname(LOCK), exist_ok=True)
    json.dump({"pid": os.getpid(), "ts": ts()}, open(LOCK, "w"))

def release():
    try:
        d = json.load(open(LOCK))
        if d.get("pid") == os.getpid():
            os.remove(LOCK)
    except Exception:
        pass

def hb(state, extra=None):
    try:
        d = {"ts": ts(), "state": state, "pid": os.getpid()}
        if extra:
            d.update(extra)
        json.dump(d, open(HB, "w"), ensure_ascii=False)
    except Exception:
        pass

def run_patrol():
    import importlib.util as iu
    sp = iu.spec_from_file_location("rp", HOME + "/tools/rule_patrol.py")
    m = iu.module_from_spec(sp); sp.loader.exec_module(m)
    return m.patrol()

def main():
    acquire_lock()
    log("★ 规则巡检启动 pid=%s cycle=%ds (零模型)" % (os.getpid(), CYCLE))
    n = 0
    try:
        while True:
            n += 1
            hb("running", {"round": n})
            try:
                r = run_patrol()
                bad = [i for i in r["items"] if not i["ok"]]
                if bad:
                    log("round#%d 异常 %d 项: %s" % (n, len(bad),
                        " | ".join("%s(%s)" % (i["chk"], i["detail"]) for i in bad[:4])))
                else:
                    log("round#%d 全绿 %d 项" % (n, r["total"]))
                hb("running", {"round": n, "bad": r["bad"]})
            except Exception as e:
                log("round#%d 巡检异常: %s" % (n, str(e)[:100]))
                hb("error", {"round": n, "err": str(e)[:80]})
            time.sleep(CYCLE)
    except KeyboardInterrupt:
        log("停止")
    finally:
        release()

if __name__ == "__main__":
    main()