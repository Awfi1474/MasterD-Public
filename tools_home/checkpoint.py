#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·断点续跑 checkpoint.py
★ 照官方(Anthropic 多智能体): 「can't just restart from the beginning: restarts are expensive」
★ 现状: 任务崩了从头来 → 重复处理（今晚21万条积压一部分就是这样）
★ 目标: 每个任务存「处理到哪」→ 崩了从断点续
★ 判据: 「跑过的不重跑｜只跑没跑的」
★ 零模型
"""
import os
import json
import hashlib
import datetime

HOME = "/opt/masterd-wudi"
CKPT = HOME + "/data/checkpoint.jsonl"


def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")


def _key(item):
    """给一个待处理项取唯一键（用什么做键由调用方定·这里用内容哈希）"""
    return hashlib.md5(str(item)[:200].encode()).hexdigest()[:16]


def load_done(scope):
    """读某任务域已处理的键集合"""
    done = set()
    if not os.path.exists(CKPT):
        return done
    for l in open(CKPT, encoding="utf-8", errors="ignore"):
        if not l.strip():
            continue
        try:
            d = json.loads(l)
        except Exception:
            continue
        if d.get("scope") == scope and d.get("state") == "done":
            done.add(d.get("key"))
    return done


def mark(scope, item, state="done", note=""):
    """标记「这个项处理到哪」"""
    rec = {"ts": ts(), "scope": scope, "key": _key(item), "item": str(item)[:120],
           "state": state, "note": str(note)[:120]}
    os.makedirs(os.path.dirname(CKPT), exist_ok=True)
    with open(CKPT, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def filter_pending(scope, items):
    """从 items 里过滤出「还没处理的」（断点续的核心）
       ★ 判据: 「跑过的不重跑」
    """
    done = load_done(scope)
    pending = []
    for it in items:
        if _key(it) not in done:
            pending.append(it)
    return pending


def progress(scope):
    """看某任务域的进度"""
    total = 0
    done = 0
    if os.path.exists(CKPT):
        for l in open(CKPT, encoding="utf-8", errors="ignore"):
            if not l.strip():
                continue
            try:
                d = json.loads(l)
            except Exception:
                continue
            if d.get("scope") != scope:
                continue
            total += 1
            if d.get("state") == "done":
                done += 1
    return {"scope": scope, "标记数": total, "完成": done}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # 演示：处理 5 条·中途「崩」·再跑只处理剩下的
        scope = "demo"
        items = ["msg-%d" % i for i in range(5)]
        print("=== 第一次跑（假装处理到第3条崩了）===")
        for it in items[:3]:
            mark(scope, it, "done")
        print("  已标记前3条")
        pend = filter_pending(scope, items)
        print("  崩后重启 → 还剩 %d 条要处理: %s" % (len(pend), pend))
        print()
        print("=== 第二次跑（从断点续）===")
        for it in pend:
            mark(scope, it, "done")
        pend2 = filter_pending(scope, items)
        print("  再跑 → 还剩 %d 条" % len(pend2))
        print()
        print("进度:", progress(scope))
        print("判据: 跑过的不重跑｜只跑没跑的（凭据: data/checkpoint.jsonl）")
    else:
        print("checkpoint.py 就绪")
        print("用法: filter_pending(scope, items) → 只返回没处理的")
        print("      mark(scope, item) → 标记处理完")
        print("      progress(scope) → 看进度")