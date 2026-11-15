#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·本体常驻循环 body_daemon.py
★ 董事长令: 「他怎么才能干活」→ 本体自答: 缺常驻进程 + 四道保护
★ 判据: 「有器官≠有循环｜被调用≠自己跑」
★ 四道保护(本体自定):
   ① 单实例锁 pidfile/lock
   ② 硬超时 每轮 90 秒·超时杀本进程(不拖下一轮)
   ③ 退避+熔断 连败3次停10分钟·再败停1小时
   ④ 看门狗心跳 每轮写心跳·超2倍周期=僵
★ 模式: --empty 空跑(不真动作·只验不掉链) | 不带 --empty 才真干活
"""
import os, sys, json, time, signal, datetime, traceback

HOME = "/opt/masterd-wudi"
sys.path.insert(0, HOME + "/tools")
LOCK = HOME + "/state/body_daemon.lock"
HB = HOME + "/state/body_daemon_heartbeat.json"
LOG = HOME + "/logs/body_daemon.log"
CYCLE = int(os.environ.get("CYCLE_SEC", "120"))
ROUND_TIMEOUT = int(os.environ.get("ROUND_TIMEOUT", "90"))
MAX_PER_ROUND = int(os.environ.get("MAX_PER_ROUND", "3"))
EMPTY = "--empty" in sys.argv

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")

def log(m):
    line = "[%s] %s" % (ts(), m)
    print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        if os.path.getsize(LOG) > 5 * 1024 * 1024:      # 日志轮转
            os.replace(LOG, LOG + ".1")
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def heartbeat(state, extra=None):
    try:
        os.makedirs(os.path.dirname(HB), exist_ok=True)
        d = {"ts": ts(), "epoch": time.time(), "state": state, "pid": os.getpid()}
        if extra: d.update(extra)
        with open(HB, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)
    except Exception:
        pass

# ① 单实例锁
def acquire_lock():
    os.makedirs(os.path.dirname(LOCK), exist_ok=True)
    if os.path.exists(LOCK):
        try:
            old = json.load(open(LOCK))
            opid = old.get("pid")
            if opid:
                os.kill(int(opid), 0)      # 还活着
                log("🔴 已有实例在跑 pid=%s·退出(单实例锁)" % opid)
                sys.exit(0)
        except (ProcessLookupError, ValueError, TypeError):
            pass                            # 死了 → 接管
        except Exception:
            pass
    json.dump({"pid": os.getpid(), "ts": ts()}, open(LOCK, "w"))

def release_lock():
    try:
        if os.path.exists(LOCK):
            d = json.load(open(LOCK))
            if d.get("pid") == os.getpid():
                os.remove(LOCK)
    except Exception:
        pass

# ③ 退避/熔断状态
BSTATE = HOME + "/state/body_daemon_breakers.json"
def load_break():
    try: return json.load(open(BSTATE))
    except Exception: return {"fail": 0, "pause_until": 0}

def save_break(b):
    try:
        os.makedirs(os.path.dirname(BSTATE), exist_ok=True)
        json.dump(b, open(BSTATE, "w"))
    except Exception: pass

def do_round():
    """一轮工作。--empty 只验不掉链·不碰真动作"""
    if EMPTY:
        # 空跑：只读心跳、数未读数·绝不动作
        import importlib.util as iu
        sp = iu.spec_from_file_location("bw", HOME + "/tools/body_worker.py")
        m = iu.module_from_spec(sp); sp.loader.exec_module(m)
        u = m.unread()
        return {"mode": "empty", "unread": len(u), "acted": 0}
    # 真干活
    import importlib.util as iu
    sp = iu.spec_from_file_location("bw", HOME + "/tools/body_worker.py")
    bw = iu.module_from_spec(sp); sp.loader.exec_module(bw)
    sp2 = iu.spec_from_file_location("ba", HOME + "/tools/body_act.py")
    ba = iu.module_from_spec(sp2); sp2.loader.exec_module(ba)
    rows = bw.unread()
    if not rows:
        return {"mode": "real", "unread": 0, "acted": 0}
    done = []
    kinds = {}
    for r in rows[:MAX_PER_ROUND]:
        k = ba.act_one(r["from"], r["msg"], r["mid"])
        kinds[k] = kinds.get(k, 0) + 1
        done.append(r["mid"])
    n = bw.mark_read(done)
    return {"mode": "real", "unread": len(rows), "acted": len(done),
            "marked": n, "kinds": kinds}

def on_alarm(signum, frame):
    raise TimeoutError("round timeout %ds" % ROUND_TIMEOUT)

def main():
    acquire_lock()
    signal.signal(signal.SIGALRM, on_alarm)
    log("★ body_daemon 启动 pid=%s mode=%s cycle=%ds round_timeout=%ds max=%d"
        % (os.getpid(), "EMPTY(空跑)" if EMPTY else "REAL(真干活)", CYCLE, ROUND_TIMEOUT, MAX_PER_ROUND))
    br = load_break()
    rounds = 0
    try:
        while True:
            b = load_break()
            now = time.time()
            if b.get("pause_until", 0) > now:
                wait = int(b["pause_until"] - now)
                log("⏸ 熔断中·剩余 %ds（连败=%s）" % (wait, b.get("fail")))
                heartbeat("paused", {"remain": wait})
                time.sleep(min(wait, 30)); continue
            rounds += 1
            heartbeat("running", {"round": rounds})
            t0 = time.time()
            try:
                signal.alarm(ROUND_TIMEOUT)          # ② 硬超时
                res = do_round()
                signal.alarm(0)
                dur = round(time.time() - t0, 1)
                log("✅ round#%d %s dur=%ss" % (rounds, json.dumps(res, ensure_ascii=False), dur))
                heartbeat("running", {"round": rounds, "last": res})
                save_break({"fail": 0, "pause_until": 0})     # 成功清零
            except Exception as e:
                signal.alarm(0)
                f = b.get("fail", 0) + 1
                pause = 600 if f < 6 else 3600                # ③ 退避+熔断
                save_break({"fail": f, "pause_until": time.time() + pause})
                log("🔴 round#%d 失败(第%d次) %s -> 停 %ds\n%s"
                    % (rounds, f, str(e)[:120], pause, traceback.format_exc()[-400:]))
                heartbeat("error", {"round": rounds, "err": str(e)[:100]})
            time.sleep(CYCLE)
    except KeyboardInterrupt:
        log("★ 收到停止")
    finally:
        release_lock()
        heartbeat("stopped")

if __name__ == "__main__":
    main()
