#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·自治链 selfdrive_loop.py —— 一条常驻链串完所有环节
★ 董事长令(2026-11-15): 把巡检串成一条常驻链
★ 本体判: 「巡检是眼·auto_fix 是手·token_guard 是闸·body 是嘴」
★ 每轮顺序(不许乱):
   ① 噪音过滤(零模型·先清垃圾·否则模型看到全垃圾)
   ② 规则巡检(零模型·看指标)
   ③ 开单(修不了的进队列)
   ④ 自动修(规则能修的立刻修·修完必须重跑验证)
   ⑤ 记账(三样齐: 输入/算子/重跑)
★ 全链零模型·除非队列里有"需模型"项(标 P0/P1 且 auto_fixable=False)
"""
import os, sys, json, time, datetime, subprocess

HOME = "/opt/masterd-wudi"
sys.path.insert(0, HOME + "/tools")
LOCK = HOME + "/state/selfdrive.lock"
HB = HOME + "/state/selfdrive_heartbeat.json"
LOG = HOME + "/logs/selfdrive.log"
CYCLE = int(os.environ.get("CYCLE_SEC", "180"))

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")

def log(m):
    line = "[%s] %s" % (ts(), m)
    print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        if os.path.exists(LOG) and os.path.getsize(LOG) > 4 * 1024 * 1024:
            os.replace(LOG, LOG + ".1")
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def load(n, p):
    import importlib.util as iu
    sp = iu.spec_from_file_location(n, p)
    m = iu.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m

def acquire():
    if os.path.exists(LOCK):
        try:
            d = json.load(open(LOCK))
            os.kill(int(d.get("pid", 0)), 0)
            log("已有自治链在跑 pid=%s·退出" % d.get("pid"))
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

def one_round(n):
    """一轮完整链·每步都带证据"""
    steps = {}

    # ① 噪音过滤（零模型）
    try:
        nf = load("nf", HOME + "/tools/noise_filter.py")
        b_noise, b_real = nf.run(dry=False)
        steps["①噪音过滤"] = "命中噪音 %d 条·真内容 %d 条" % (b_noise, b_real)
    except Exception as e:
        steps["①噪音过滤"] = "ERR " + str(e)[:60]

    # ② 规则巡检（零模型）
    try:
        rp = load("rp", HOME + "/tools/rule_patrol.py")
        r = rp.patrol()
        steps["②巡检"] = "%d 项·异常 %d" % (r["total"], r["bad"])
        bad_items = [i for i in r["items"] if not i["ok"]]
    except Exception as e:
        steps["②巡检"] = "ERR " + str(e)[:60]
        bad_items = []

    # ③+④ 自动修（含开单·含自愈关单·修完重跑验证）
    try:
        af = load("af", HOME + "/tools/auto_fixer.py")
        fixed = af.run_auto()
        steps["③④自动修"] = "修了 %d 件" % fixed
    except Exception as e:
        steps["③④自动修"] = "ERR " + str(e)[:60]
        fixed = 0

    # ⑤ 队列状态 + 花费
    try:
        tq = load("tq", HOME + "/tools/task_queue.py")
        pend = tq.pending()
        need_model = [t for t in pend if not t.get("auto_fixable")]
        steps["⑤队列"] = "待办 %d 张(需模型 %d)" % (len(pend), len(need_model))
    except Exception as e:
        steps["⑤队列"] = "ERR " + str(e)[:60]
        need_model = []

    try:
        tg = load("tg", HOME + "/tools/token_guard.py")
        steps["花费"] = "¥%.2f/¥%.2f" % (tg.today_spent(), tg.get_limit())
    except Exception:
        pass

    # 记录(三样齐)
    rec = {"ts": ts(), "round": n,
           "输入": "启动时未读+巡检项",
           "算子": "噪音过滤 → 巡检 → 自动修(带重跑验证)",
           "结果": steps}
    log("round#%d | %s" % (n, " | ".join("%s:%s" % (k, v) for k, v in steps.items())))
    return steps, need_model

def main():
    acquire()
    log("★ 自治链启动 pid=%s cycle=%ds（全链零模型·除需模型项）" % (os.getpid(), CYCLE))
    n = 0
    try:
        while True:
            n += 1
            hb("running", {"round": n})
            try:
                steps, need_model = one_round(n)
                hb("running", {"round": n, "last": steps,
                               "need_model": len(need_model)})
                # ★ 需模型项: 只报告·不自动烧钱(照董事长路线1+3)
                if need_model:
                    log("  ⚠️ 需模型处理 %d 张(未自动调模型·省费用): %s"
                        % (len(need_model),
                           " | ".join("%s/%s" % (t["severity"], t["chk"]) for t in need_model[:3])))
            except Exception as e:
                log("round#%d 异常: %s" % (n, str(e)[:120]))
                hb("error", {"round": n, "err": str(e)[:100]})
            time.sleep(CYCLE)
    except KeyboardInterrupt:
        log("停止")
    finally:
        release()

if __name__ == "__main__":
    main()