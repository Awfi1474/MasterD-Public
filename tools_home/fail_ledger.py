#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·失败账 fail_ledger.py —— 统一失败入账口
★ 本体判: 「账里只有成功，那不是账，是宣传」
★ 判据: 「失败必须落账｜但不必逐处改921个 except——给一个统一口，新代码必须用」
★ 用法: from fail_ledger import fail;  except Exception as e: fail("模块.位置", e)

三层策略:
  ① 统一口 fail()  —— 新代码/改到的代码必须用
  ② 静默吞检测    —— 扫「except 后面直接 pass 或只有 print」的·报出来
  ③ 失败率统计    —— 按模块统计失败次数·能看出哪块在烂
"""
import os, json, datetime, traceback, sys

HOME = "/opt/masterd-wudi"
FAILS = HOME + "/data/fail_ledger.jsonl"

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")

def fail(where, err, ctx="", silent=False):
    """★ 统一失败入账口。silent=False 时同时打印
       参数: where='模块.位置'  err=异常对象或字符串  ctx=上下文
    """
    tb = ""
    if isinstance(err, BaseException):
        tb = "".join(traceback.format_exception(type(err), err, err.__traceback__))[-600:]
        msg = ("%s: %s" % (type(err).__name__, err))[:300]
    else:
        msg = str(err)[:300]
    rec = {"ts": ts(), "where": str(where)[:80], "err": msg,
           "ctx": str(ctx)[:200], "tb": tb}
    try:
        os.makedirs(os.path.dirname(FAILS), exist_ok=True)
        with open(FAILS, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
    if not silent:
        print("[失败·落账] %s → %s" % (where, msg))
    return rec

def stats(day=None):
    """按模块统计失败（看哪块在烂）"""
    day = day or ts()[:10]
    if not os.path.exists(FAILS):
        return {}
    agg = {}
    for l in open(FAILS, encoding="utf-8", errors="ignore"):
        if not l.strip():
            continue
        try:
            d = json.loads(l)
        except Exception:
            continue
        if str(d.get("ts", ""))[:10] != day:
            continue
        w = str(d.get("where", "?")).split(".")[0]
        agg[w] = agg.get(w, 0) + 1
    return dict(sorted(agg.items(), key=lambda x: -x[1]))

def scan_silent(root=None):
    """扫「静默吞」: except 之后既不 print 也不落账 的（本体最恨这种）"""
    import re
    root = root or (HOME + "/tools")
    bad = []
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ("_archive", "__pycache__")]
        for fn in files:
            if not fn.endswith(".py"):
                continue
            p = os.path.join(dirpath, fn)
            try:
                lines = open(p, encoding="utf-8", errors="ignore").read().splitlines()
            except Exception:
                continue
            for i, l in enumerate(lines):
                if not re.match(r"\s*except\b", l):
                    continue
                # 看后两行有没有 print / fail( / 落账
                nxt = " ".join(x.strip() for x in lines[i + 1:i + 3])
                if re.match(r"^\s*pass\s*$", lines[i + 1].strip() if i + 1 < len(lines) else ""):
                    bad.append((os.path.relpath(p, HOME), i + 1, "except→pass"))
                elif nxt and not any(k in nxt for k in ("print", "fail(", "raise", "log(", "append")):
                    bad.append((os.path.relpath(p, HOME), i + 1, "except→静默"))
    return bad

if __name__ == "__main__":
    import sys as _s
    if len(_s.argv) > 1 and _s.argv[1] == "--scan":
        bad = scan_silent()
        print("静默吞处: %d 处（except 后既不 print 也不落账）" % len(bad))
        from collections import Counter
        c = Counter(x[0] for x in bad)
        for f, n in c.most_common(10):
            print("  %-40s %d 处" % (f, n))
    elif len(_s.argv) > 1 and _s.argv[1] == "--stats":
        st = stats()
        print("今日失败统计:")
        for k, v in (st.items() or {"(无)": 0}):
            print("  %-30s %d 次" % (k, v))
    else:
        print("fail_ledger 就绪 | 用法: fail('模块.位置', e) | --scan | --stats")