#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""db_guard.py —— 记忆库连接闸（老五·2026-11-08·董事长令杜绝漂移）
================================================================
★ 判据: 「真源唯一|白名单外直接拒|闸不是拦别人·是拦明天的我」
★ 用法:
  import db_guard
  conn = db_guard.connect()            # 连真源(唯一白名单)
  db_guard.check(path)                 # 连前核路径·不在白名单 raise
★ 杀手锏: 有 tools/guard_scan.py 扫全仓裸 sqlite3.connect
================================================================
"""
import os, json, sqlite3, datetime

HOME = "/opt/masterd-wudi"
WHITELIST_FILE = HOME + "/memory/SOURCE-OF-TRUTH.json"
DENIED_LOG = HOME + "/data/db_guard_denied.jsonl"

def _whitelist():
    try:
        return json.load(open(WHITELIST_FILE))["真源"]
    except Exception:
        return HOME + "/memory/memory.db"

def check(path=None):
    """核路径·不在白名单→raise(失败即拦·留证)"""
    wl = _whitelist()
    p = path or wl
    if os.path.abspath(p) != os.path.abspath(wl):
        try:
            with open(DENIED_LOG, "a") as f:
                f.write(json.dumps({"ts": datetime.datetime.now().isoformat(timespec="seconds"),
                                    "denied": p, "whitelist": wl}, ensure_ascii=False) + "\n")
        except Exception:
            pass
        raise PermissionError("db_guard: 非真源·拒连 %s（真源唯一=%s）" % (p, wl))
    return True

def connect(path=None, **kw):
    """唯一连库入口·只连真源"""
    check(path)
    return sqlite3.connect(path or _whitelist(), **kw)

if __name__ == "__main__":
    import sys
    wl = _whitelist()
    print("★ db_guard · 真源唯一:", wl)
    print("  白名单文件:", WHITELIST_FILE)
    if len(sys.argv) > 1:
        try:
            check(sys.argv[1])
            print("  ✅ 放行:", sys.argv[1])
        except PermissionError as e:
            print("  🔴 拦下:", e)
