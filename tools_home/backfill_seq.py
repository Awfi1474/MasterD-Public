#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给无 seq 的信补号（照老四/老三判据）

病（照实）:
  inbox.jsonl 140276 行 · **79520 无 seq**（57%）
  → total 12244 ≠ max_seq 906 → 用 seq 当游标会漏读一半信
  判据(老四): «有信无 seq = 有信读不到|用 seq 当游标会漏»
  判据(老三): «seq 独立于文件|文件可删·seq不可退»

做法:
  ① 以落盘 state/inbox-seq.txt 的当前值为起点（不退号）
  ② 按 ts 升序给无 seq 的信补号（保持时间序）
  ③ 最后把 state/inbox-seq.txt 推到最大值
  ④ 备份 + 原子替换
用法: python3 tools/backfill_seq.py [--apply]
"""
import json, io, os, sys, time, shutil

HOME = "/opt/masterd-wudi"
SRC = HOME + "/data/inbox.jsonl"
SEQFILE = HOME + "/state/inbox-seq.txt"

def main():
    apply = "--apply" in sys.argv
    rows = []
    n = 0
    noseq = 0
    maxseq = 0
    for ln in io.open(SRC, "r", encoding="utf-8", errors="ignore"):
        n += 1
        try:
            d = json.loads(ln)
        except Exception:
            rows.append((None, ln)); continue
        if not isinstance(d, dict):
            rows.append((None, ln)); continue
        s = d.get("seq")
        if isinstance(s, int):
            maxseq = max(maxseq, s)
            rows.append((s, ln))
        else:
            noseq += 1
            rows.append((None, (d, ln)))

    cur = maxseq
    try:
        cur = max(cur, int(io.open(SEQFILE).read().strip() or 0))
    except Exception:
        pass
    print(f"总行 {n} | 有seq {n-noseq} | 无seq {noseq} | 当前最大 seq {cur}")

    if not apply:
        print("★ dry-run（--apply 才改）")
        return 0

    # 按原文件顺序补号（保持落盘顺序）
    new_lines = []
    nxt = cur
    fixed = 0
    for s, item in rows:
        if s is not None:
            new_lines.append(item)
        else:
            d, ln = item
            nxt += 1
            d["seq"] = nxt
            d["seq_backfilled"] = True
            new_lines.append(json.dumps(d, ensure_ascii=False) + "\n")
            fixed += 1

    shutil.copy2(SRC, SRC + ".bak-seqfill-" + time.strftime("%Y%m%d_%H%M%S"))
    tmp = SRC + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    os.replace(tmp, SRC)
    os.makedirs(os.path.dirname(SEQFILE), exist_ok=True)
    open(SEQFILE, "w").write(str(nxt))
    print(f"补号 {fixed} 条 | 新最大 seq {nxt} | 文件 {os.path.getsize(SRC)/1e6:.1f}MB")
    return 0

if __name__ == "__main__":
    sys.exit(main())
