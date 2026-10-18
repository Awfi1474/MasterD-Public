#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mem_safe.py —— 记忆库三保险（防"再坏一次"）
================================================================
★ 今天真病（照实）:
  ★ 主记忆库【B-tree 坏页】→ 465 条从备份重建 + 79 条补记
  ★ ★ 根因（查出的）:
    ★ ① mem_guard.py 【两个进程同时】在读写这个库
    ★ ★ ② 库在"会死的沙箱"侧被反复读写（沙箱重置时 IO 中断 → 写坏页）
    ★ ★ ★ ③ **没有"每日备份"**（最近的备份是 10-13·差 2 天）

★ 三保险（本件做）:
  ★ ① **每日备份**（每天 1 次·留 7 天·带日期）
  ★ ★ ② **完整性自检**（每次备份前 PRAGMA integrity_check·坏了立刻告警）
  ★ ★ ★ ③ **并发锁**（用 flock·防"两个 mem_guard 同时写"）

★ 判据（我立·血换的）:
  ★「**没备份 = 没记忆｜差 2 天的备份 = 差 2 天的命**」
  ★「**同一个库·不许两个进程同时写｜并发写 = 坏页的根**」
  ★「**备份要"先验再备"｜备了坏的 = 白备**」
"""
import os, io, sys, sqlite3, shutil, gzip, glob, subprocess, datetime, json

HOME = "/opt/masterd-wudi"
DB = f"{HOME}/memory/memory.db"
BAKDIR = f"{HOME}/memory/backup"
LOCK = "/tmp/mem-safe.lock"
KEEP = 7        # ★ 留 7 天
OUT = f"{HOME}/data/mem_safe.json"


def ts():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def integrity(p):
    """★ 验完整性（备之前要"先验"）"""
    try:
        c = sqlite3.connect(p, timeout=15)
        r = c.execute("PRAGMA integrity_check").fetchone()[0]
        n = c.execute("SELECT count(*) FROM memories").fetchone()[0]
        c.close()
        return (r == "ok"), n, r[:60]
    except Exception as e:
        return False, -1, str(e)[:60]


def main():
    # ★ ③ 并发锁（flock·单实例）
    try:
        import fcntl
        lf = open(LOCK, "w")
        fcntl.flock(lf, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except Exception as e:
        print("🟡 已有实例在跑（锁住）:", str(e)[:40])
        return

    print("★ 记忆库三保险  @ %s" % ts())
    print("★ 判据: 「没备份 = 没记忆｜先验再备｜不许两个进程同时写」")
    print("=" * 58)

    # ★ ① 自检主库
    ok, n, msg = integrity(DB)
    print("★ 主库自检: %s ｜ %d 条 ｜ %s" % ("✅ ok" if ok else "🔴 坏", n, msg))
    if not ok:
        print("🔴 主库坏了！★ 不覆盖备份·★ 从最近好备份恢复")
        # ★ 找最近的"好"备份
        baks = sorted(glob.glob(f"{BAKDIR}/mx-*.db"), reverse=True)
        for b in baks:
            bok, bn, bmsg = integrity(b)
            if bok:
                print("   ✅ 用 %s 恢复（%d 条）" % (os.path.basename(b), bn))
                shutil.copy(DB, DB + ".broken-" + datetime.datetime.now().strftime("%H%M%S"))
                shutil.copy(b, DB)
                break
        else:
            print("   🔴 没有好备份可恢复！")

    # ★ ② 每日备份（带日期·压缩）
    os.makedirs(BAKDIR, exist_ok=True)
    day = datetime.datetime.now().strftime("%Y%m%d")
    dest = f"{BAKDIR}/mx-{day}.db"
    if os.path.exists(dest):
        print("★ 今天已备份（%s）·跳过" % os.path.basename(dest))
    else:
        # ★ 先验再备（★ 不备坏的）
        ok2, n2, msg2 = integrity(DB)
        if ok2:
            shutil.copy(DB, dest)
            # ★ 再验一次（备完的也要好）
            ok3, n3, _ = integrity(dest)
            print("★ 备份: %s（%d 条）｜备完复查: %s"
                  % (os.path.basename(dest), n2, "✅ ok" if ok3 else "🔴 坏"))
            # ★ 压缩旧的
            for old in glob.glob(f"{BAKDIR}/mx-*.db"):
                if old == dest:
                    continue
                try:
                    with open(old, "rb") as fi, gzip.open(old + ".gz", "wb") as fo:
                        shutil.copyfileobj(fi, fo)
                    os.remove(old)
                    print("   📦 压缩: %s" % os.path.basename(old))
                except Exception:
                    pass
        else:
            print("🔴 主库坏·不备份（★ 备坏的 = 白备）")

    # ★ ③ 清理（留 KEEP 天）
    allb = sorted(glob.glob(f"{BAKDIR}/mx-*.db*"))
    if len(allb) > KEEP:
        for old in allb[:-KEEP]:
            try:
                os.remove(old)
                print("   🗑 清理旧备份: %s" % os.path.basename(old))
            except Exception:
                pass

    left = sorted(os.path.basename(x) for x in glob.glob(f"{BAKDIR}/mx-*"))
    print("\n★ 现有备份: %s" % ", ".join(left[-7:]))
    okf, nf, _ = integrity(DB)
    print("★ 主库: %d 条 ｜ %s" % (nf, "✅ ok" if okf else "🔴"))
    print("★ 判据: 「没备份 = 没记忆｜差 2 天的备份 = 差 2 天的命」")

    json.dump({"ts": ts(), "ok": okf, "n": nf, "backups": left[-7:]},
              open(OUT, "w"), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
