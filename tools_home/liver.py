#!/usr/bin/env python3
"""老五 · 肝 (liver.py) —— 将军之官·主疏泄 → 调度/解堵
施工图(2026-10-10 BUILD-MAP-5ZANG6FU)第1步: 肝先长·因为"器官多了会堵"。
验收判据(施工图): 堵点被发现并疏解 | 不乱疏(过疏伤脾)
用法: python3 liver.py            体检(找堵点)
      python3 liver.py --dredge   疏泄(解堵·默认只报不动手)
      python3 liver.py --list     列堵点类型
"""
import os, sys, json, glob, subprocess
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
# ★ 堵点类型（我定·可扩）
BLOCK_TYPES = {
    "锁":       "残留的 pid 锁（进程死了·锁还在）",
    "收件堆积": "inbox 太大（没人消化）",
    "日志堆积": "日志文件过大（只写不清）",
    "死进程":   "僵尸/残留进程",
    "包陈旧":   "备份包比主库旧太多",
}

def find_blocks():
    """★ 找堵点（只报·不动手）"""
    out = []
    # ① 锁
    for lf in glob.glob("/tmp/.laowu-*.pid") + glob.glob("/tmp/.laowu-*.lock"):
        try:
            age = (datetime.now().timestamp() - os.path.getmtime(lf)) / 3600
            pid = None
            try:
                pid = int(open(lf).read().strip())
            except Exception:
                pass
            alive = False
            if pid:
                try:
                    os.kill(pid, 0); alive = True
                except OSError:
                    alive = False
            if not alive or age > 6:
                out.append({"type": "锁", "what": lf, "why": "进程不在 或 锁超6h", "age_h": round(age, 1)})
        except Exception:
            pass
    # ② 收件堆积
    for q in ["/app/workspace/family/lan_inbox.jsonl"]:
        if os.path.exists(q):
            n = sum(1 for _ in open(q))
            if n > 200:
                out.append({"type": "收件堆积", "what": q, "why": "%d 条（>200）" % n})
    # ③ 日志堆积
    for lg in glob.glob("/opt/masterd-wudi/data/*.log"):
        if os.path.exists(lg) and os.path.getsize(lg) > 5_000_000:
            out.append({"type": "日志堆积", "what": lg, "why": "%.1f MB" % (os.path.getsize(lg) / 1e6)})
    # ④ 包陈旧
    main = "/opt/masterd-wudi/memory/memory.db"
    pkg = "/opt/masterd-wudi/recovery/老五-recovery.tar.gz"
    if os.path.exists(main) and os.path.exists(pkg):
        if os.path.getmtime(main) - os.path.getmtime(pkg) > 3600:
            out.append({"type": "包陈旧", "what": pkg, "why": "包比主库旧 >1h"})
    return out

def dredge(blocks):
    """★ 疏泄（解堵）·但不乱疏（过疏伤脾）"""
    acted = []
    for b in blocks:
        if b["type"] == "锁" and "进程不在" in b.get("why", ""):
            try:
                os.remove(b["what"]); acted.append("删死锁 %s" % b["what"])
            except Exception:
                pass
        elif b["type"] == "包陈旧":
            r = subprocess.run(["python3", "/opt/masterd-wudi/tools/backup_guard.py"],
                               capture_output=True, text=True, timeout=180)
            acted.append("重打包（backup_guard）")
    return acted

if __name__ == "__main__":
    a = sys.argv[1:]
    if "--list" in a:
        print("  ★ 堵点类型:")
        for k, v in BLOCK_TYPES.items(): print("   %-8s %s" % (k, v))
    else:
        bs = find_blocks()
        print("  ★ 肝·疏泄体检 (%s)" % datetime.now(CST).strftime("%H:%M"))
        if not bs:
            print("   ✅ 无堵点（气血通畅）")
        else:
            for b in bs:
                print("   ⚠ [%s] %s — %s" % (b["type"], b["what"], b["why"]))
        if "--dredge" in a:
            acts = dredge(bs)
            print("  ★ 疏泄动作: %s" % ("; ".join(acts) if acts else "无可自动处理的（余下需人工）"))
        elif bs:
            print("  ★ 判据: 只报不动手（过疏伤脾）·要疏加 --dredge")
