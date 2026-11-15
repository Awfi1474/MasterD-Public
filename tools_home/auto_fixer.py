#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·规则自动修 auto_fixer.py —— 规则能修的巡检自己修掉
★ 本体判: 「规则答'是什么'，模型答'该怎么办'」
★ 判据: 「输入→输出固定映射 = 规则干·不烧钱｜要权衡判断 = 进队列给模型」

能自动修的（有唯一答案）:
  · 未读超阈值 → 归档老消息（标记 archived·不删除）
  · 服务挂了 → 重启（只重启自家 body_* / rule_*）
  · 日志超 5MB → 轮转
  · 锁文件残留（进程已死）→ 清理

不许自动修的（要判断）:
  · 账里「不符」→ 要判断原因
  · 端口不通 → 要知道为什么
  · 花费接近上限 → 要人决定
"""
import os, json, subprocess, datetime, importlib.util

HOME = "/opt/masterd-wudi"

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")

def load(n, p):
    sp = importlib.util.spec_from_file_location(n, p)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m

def log(m):
    line = "[%s] %s" % (ts(), m)
    print(line, flush=True)
    try:
        os.makedirs(HOME + "/logs", exist_ok=True)
        with open(HOME + "/logs/auto_fix.log", "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

# ---------- 可自动修的三件（全部有唯一答案） ----------

def fix_unread(t):
    """未读超阈值 → 把最老的归档（只标 archived·不删）"""
    try:
        bw = load("bw", HOME + "/tools/body_worker.py")
        rows = bw.unread()
        if len(rows) <= 800:
            return False, "未读 %d 条·未超阈值 800" % len(rows)
        # 归档最老的 500 条（按 ts 排序）
        oldest = sorted(rows, key=lambda r: str(r.get("ts") or ""))[:500]
        mids = [r["mid"] for r in oldest]
        p = HOME + "/data/inbox.jsonl"
        lines = [l for l in open(p, encoding="utf-8", errors="ignore") if l.strip()]
        out = []
        n = 0
        s = set(mids)
        for l in lines:
            try:
                d = json.loads(l)
            except Exception:
                out.append(l); continue
            b = d.get("c") if isinstance(d.get("c"), dict) else d
            mid = str(b.get("messageId") or b.get("msg_id") or "")
            if not mid:
                import hashlib
                t2 = str(b.get("message") or "")
                mid = "k-" + hashlib.md5(("%s|%s|%s" % (b.get("from") or "", b.get("ts") or "", t2[:80])).encode()).hexdigest()[:16]
            if mid in s and b.get("read") is not True:
                b["read"] = True
                b["read_by"] = "auto_fixer"
                b["archived"] = True
                b["read_at"] = ts()
                n += 1
            if isinstance(d.get("c"), dict):
                d["c"] = b
            else:
                d = b
            out.append(json.dumps(d, ensure_ascii=False) + "\n")
        if n:
            open(p, "w", encoding="utf-8").writelines(out)
        return True, "归档 %d 条老消息（未读 %d → %d）" % (n, len(rows), len(rows) - n)
    except Exception as e:
        return False, "err " + str(e)[:100]

def fix_service(t):
    """服务挂了 → 重启（只自家进程）"""
    chk = t.get("chk", "")
    if not chk.startswith("service:"):
        return False, "not service"
    name = chk.split(":", 1)[1]
    if name not in ("body_worker", "body_daemon", "rule_patrol_daemon"):
        return False, "不许自动重启: " + name
    try:
        subprocess.run("pkill -f '%s.py'" % name, shell=True, timeout=10)
        subprocess.run("cd %s && setsid nohup python3 tools/%s.py >/tmp/%s.log 2>&1 < /dev/null &" % (HOME, name, name),
                       shell=True, timeout=10)
        import time; time.sleep(2)
        r = subprocess.run("pgrep -f '%s.py'" % name, shell=True, capture_output=True, text=True, timeout=5)
        return bool(r.stdout.strip()), "重启 %s → pid %s" % (name, r.stdout.strip()[:20])
    except Exception as e:
        return False, "err " + str(e)[:100]

def fix_log(t):
    """日志超 5MB → 轮转"""
    p = HOME + "/logs/body_daemon.log"
    try:
        if not os.path.exists(p):
            return False, "无日志"
        mb = os.path.getsize(p) // (1024 * 1024)
        if mb < 5:
            return False, "日志 %d MB·未超" % mb
        os.replace(p, p + ".1")
        return True, "轮转 %dMB 日志" % mb
    except Exception as e:
        return False, "err " + str(e)[:80]

def fix_lock(t):
    """残留锁（进程已死）→ 清理"""
    n = 0
    for f in ("state/body_daemon.lock", "state/rule_patrol.lock"):
        p = os.path.join(HOME, f)
        if not os.path.exists(p):
            continue
        try:
            d = json.load(open(p))
            os.kill(int(d.get("pid", 0)), 0)
        except Exception:
            try:
                os.remove(p); n += 1
            except Exception:
                pass
    return (n > 0), "清残留锁 %d 个" % n

AUTO_MAP = {
    "unread": fix_unread,
    "log:daemon": fix_log,
    "lock": fix_lock,
}

def _observe(chk):
    """独立观测: 再跑一次检查·拿现在的真值 (这是「计算」不是「生成」)"""
    try:
        rp = load("rp", HOME + "/tools/rule_patrol.py")
        for it in rp.patrol()["items"]:
            if it["chk"] == chk or (chk.startswith("service:") and it["chk"] == chk):
                return it
        # 服务类单独查
        if chk.startswith("service:"):
            name = chk.split(":", 1)[1]
            ok, o = rp.sh("pgrep -f '%s.py' | head -1" % name)
            return {"chk": chk, "ok": bool((o or "").strip()), "detail": (o or "").strip()[:40]}
        return None
    except Exception as e:
        return {"chk": chk, "ok": None, "detail": "observe err " + str(e)[:60]}


def run_auto():
    """读队列·自动修·修完必须「重跑观测」确认(不许靠 rc/自报)"""
    tq = load("tq", HOME + "/tools/task_queue.py")
    p = tq.pending()
    fixed = 0
    for t in p:
        chk = t.get("chk", "")
        fn = AUTO_MAP.get(chk)
        if not fn and chk.startswith("service:"):
            fn = fix_service
        if not fn:
            continue
        # ① 输入（修之前观测）
        before = _observe(chk)
        # ★ 2026-11-15 补: 问题已经自己好了(修前观测就通过) -> 直接关单·不用修
        if before is not None and before.get("ok") is True:
            tq.close(t["id"], by="auto_fixer", note="问题已自愈(修前观测已通过)",
                     verify={"输入": "修前: %s" % str(before.get("detail"))[:80],
                             "算子": "无(检查已通过·不需要修)",
                             "重跑": "当前: %s" % str(before.get("detail"))[:80]})
            log("✓ 自愈关单 [%s] %s → %s" % (t["severity"], chk, str(before.get("detail"))[:60]))
            continue
        # ② 算子（执行修复）
        ok, note = fn(t)
        # ③ 重跑观测（修之后·数值变了才算真修）
        after = _observe(chk)
        verified = False
        if before is not None and after is not None:
            verified = (after.get("ok") is True)
        # 四样齐才报成功
        proof = {
            "输入": "修前: %s" % (str((before or {}).get("detail"))[:80]),
            "算子": str(note)[:120],
            "重跑": "修后: %s" % (str((after or {}).get("detail"))[:80]),
        }
        if ok and verified:
            tq.close(t["id"], by="auto_fixer", note=note, verify=proof)
            log("🔧 已修并验证 [%s] %s → %s" % (t["severity"], chk, note))
            log("   证: 输入=%s | 算子=%s | 重跑=%s" % (proof["输入"], proof["算子"], proof["重跑"]))
            fixed += 1
        elif ok and not verified:
            # ★ 修了但观测没变 -> 不许报成功(这就是"跑了"冒充"跑对了")
            log("⚠️ 修了但重跑没变 [%s] %s → 报「不知道」(不算成功)" % (t["severity"], chk))
            log("   输入=%s | 算子=%s | 重跑=%s" % (proof["输入"], proof["算子"], proof["重跑"]))
        else:
            log("⏭ 跳过 [%s] %s → %s" % (t["severity"], chk, note))
    return fixed

if __name__ == "__main__":
    n = run_auto()
    print("本轮自动修 %d 件" % n)