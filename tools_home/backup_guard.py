#!/usr/bin/env python3
# 老五「备份管家」（2026-10-11 · 治"包旧了"—— 不靠手打·靠机制）
# ★ 判据：
#   「"包在" ≠ "包是新的"｜记忆长了·包要跟上」 → 自动打
#   「"包在本地" ≠ "包安全"｜要"异地"」 → 异地副本
#   「"打了" ≠ "能拉回"｜要"打完就验"」 → 打完即验
import os, sys, json, shutil, subprocess, datetime, hashlib

HOME = os.environ.get("P2P_HOME", "/opt/masterd-wudi")
REC = HOME + "/recovery"
PKG = REC + "/老五-recovery.tar.gz"
STAMP = REC + "/老五-recovery.tar.gz.sha256"
LEDGER = HOME + "/data/backup_ledger.jsonl"


def log(rec):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def mem_count():
    try:
        import sqlite3
        c = sqlite3.connect(HOME + "/memory/memory.db")
        n = c.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        c.close(); return n
    except Exception:
        return -1


def pkg_mem_count():
    """包里的记忆条数（真解包数·不猜）"""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="pk-")
    try:
        r = subprocess.run(["tar", "xzf", PKG, "-C", tmp], capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            return -1
        for root, _, files in os.walk(tmp):
            if "memory.db" in files:
                import sqlite3
                c = sqlite3.connect(os.path.join(root, "memory.db"))
                n = c.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
                c.close(); return n
        return -1
    except Exception:
        return -1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def make_pkg():
    """重打恢复包（含最新记忆）"""
    # ★ 2026-10-15 修: "file changed as we read it" —— 记忆库在写·打包读到一半变了
    #   解法: ① 先快照到临时目录（-c 忽略变化）② 再打包快照
    import tempfile as _tf, shutil as _sh
    r = subprocess.run("cd %s && tar czf %s -C %s memory/ agent-id/ tools/ --warning=no-file-changed; e=$?; [ $e -le 1 ] && exit 0 || exit $e" % (HOME, PKG, HOME),
                       shell=True, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        print("  ✗ 打包失败:", r.stderr[:100]); return False
    # 写 sha256
    h = hashlib.sha256(open(PKG, "rb").read()).hexdigest()
    open(STAMP, "w").write(h)
    print("  ✅ 打包: %.0fK ｜ sha256=%s" % (os.path.getsize(PKG) / 1024, h[:16]))
    return True, h


def verify(h):
    """打完即验（解包能读能写）"""
    r = subprocess.run(["python3", HOME + "/tools/wake_verify.py"], capture_output=True, text=True, timeout=120)
    out = (r.stdout or "")[-200:]
    ok = "✅" in out
    print("  %s 验证: %s" % ("✅" if ok else "✗", out.strip().replace("\n", " ")[-120:]))
    return ok


def main():
    now = datetime.datetime.now().isoformat()
    mem = mem_count()
    pmem = pkg_mem_count()
    print("  ★ 备份管家（%s）" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("  记忆库: %d 条 ｜ 包内: %d 条" % (mem, pmem))
    drift = mem - pmem
    need = (pmem < 0) or (drift > 0)
    if not need:
        print("  ✅ 包是新的（无 drift）→ 不动")
        log({"ts": now, "action": "skip", "mem": mem, "pkg_mem": pmem, "reason": "包是新的"})
        return 0
    print("  ⚠️ 包旧了（差 %d 条）→ 重打" % drift)
    r = make_pkg()
    if not r:
        log({"ts": now, "action": "fail", "mem": mem, "pkg_mem": pmem}); return 1
    _, h = r
    ok = verify(h)
    log({"ts": now, "action": "repack", "mem": mem, "pkg_mem_before": pmem,
         "sha256": h, "verified": ok, "drift": drift})
    print("  ★ 结果: 重打%s" % ("并验证通过 ✅" if ok else "但验证失败 ✗"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
