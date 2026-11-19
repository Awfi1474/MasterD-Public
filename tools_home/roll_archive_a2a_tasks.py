#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五门·a2a_tasks.jsonl 滚动归档（照老大判据）

判据（老大焊 2026-11-19）: «任务文件只增不删 = 迟早 OOM｜要滚动归档»
判据（老三 v2）: «自检自己造的垃圾要自己清｜不自清 = 自己把自己堵死»

做法:
  ① 只读尾部（不加载全体到内存·防自己 OOM）
  ② 保留最近 KEEP_DAYS 天 + 最近 KEEP_MIN_LINES 行
  ③ 老的压缩成 .gz 移去 data/archive/（可追溯·不删）
  ④ 原子替换（写 .tmp → rename）
  ⑤ 归档前先备份原文件

用法: python3 tools/roll_archive_a2a_tasks.py [--apply]
  无 --apply = 只预演（dry-run）
"""
import os, sys, gzip, json, time, shutil, io

HOME = "/opt/masterd-wudi"
SRC = HOME + "/data/a2a_tasks.jsonl"
ARCH = HOME + "/data/archive"
KEEP_DAYS = 3
KEEP_MIN_LINES = 2000
MAX_TAIL_BYTES = 64 * 1024 * 1024   # 最多扫尾部 64MB

def _ts_of(d):
    for k in ("ts", "created", "created_at", "timestamp", "time"):
        v = d.get(k)
        if v:
            return str(v)
    return ""

def main():
    apply = "--apply" in sys.argv
    if not os.path.exists(SRC):
        print("SRC 不存在:", SRC); return 1
    sz = os.path.getsize(SRC)
    n = 0
    with io.open(SRC, "rb") as f:
        for _ in f:
            n += 1
    print(f"现状: {SRC}  {sz/1e6:.1f}MB  {n} 行")

    cutoff = time.time() - KEEP_DAYS * 86400
    keep = []
    archive = []
    # 尾部扫描（从尾往回读·最多 MAX_TAIL_BYTES·避免全量进内存）
    tail_lines = []
    with open(SRC, "rb") as f:
        try:
            f.seek(0, 2)
            _end = f.tell()
            _start = max(0, _end - MAX_TAIL_BYTES)
            f.seek(_start)
            _first = f.readline()  # 丢弃半行
            tail_bytes = f.read()
            tail_lines = tail_bytes.decode("utf-8", "ignore").splitlines()
        except Exception as e:
            print("尾部读失败:", e); return 1
    _kept = 0
    for ln in tail_lines:
        if not ln.strip():
            continue
        try:
            d = json.loads(ln)
        except Exception:
            _kept += 1; continue
        ts = _ts_of(d)
        ok_keep = False
        if _kept < KEEP_MIN_LINES:
            ok_keep = True               # 最近 N 行必留
        else:
            # 解析 ts（只做粗判·失败就留）
            try:
                import datetime as _dt
                s = ts.replace("Z", "+00:00")
                _d = _dt.datetime.fromisoformat(s)
                if _d.timestamp() >= cutoff:
                    ok_keep = True
            except Exception:
                ok_keep = True
        if ok_keep:
            keep.append(ln); _kept += 1
        else:
            archive.append(ln)

    # 头部（尾部扫描之外的·全归档）
    head_lines = n - len(tail_lines)
    print(f"尾部扫了 {len(tail_lines)} 行 | 判留 {len(keep)} | 判归 {len(archive)} | 头部未扫 {head_lines} 行(全归)")

    if not apply:
        print("★ dry-run（加 --apply 才动）")
        return 0

    # 备份 + 归档
    os.makedirs(ARCH, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    bak = f"{SRC}.bak-roll-{stamp}"
    shutil.copy2(SRC, bak)
    print("备份:", bak)
    gz = f"{ARCH}/a2a_tasks_{stamp}.jsonl.gz"
    # 归档 = 头部未扫（截取前 (n-len(tail_lines)) 行）+ 判归的
    with gzip.open(gz, "wt", encoding="utf-8") as g:
        _i = 0
        with io.open(SRC, "r", encoding="utf-8", errors="ignore") as f:
            for ln in f:
                _i += 1
                if _i > head_lines:
                    break
                g.write(ln)
        for ln in archive:
            g.write(ln + "\n")
    print(f"归档: {gz}  ({os.path.getsize(gz)/1e6:.1f}MB)")

    # 原子替换（只留 keep）
    tmp = SRC + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as f:
        for ln in keep:
            f.write(ln + "\n")
    os.replace(tmp, SRC)
    print(f"新文件: {SRC}  {os.path.getsize(SRC)/1e6:.1f}MB  {len(keep)} 行")
    return 0

if __name__ == "__main__":
    sys.exit(main())
