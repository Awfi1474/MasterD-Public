#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""body_note.py —— 本体的「留痕/写文件」正口（老五·2026-11-08）
================================================================
★ 治:本体"手拼字符串"写文件必崩(hand_laowu是shell=·长命令/引号会碎)
★ 用法:
  python3 body_note.py write <路径(白名单内)> <内容文件>
  python3 body_note.py cat <路径>
★ 判据:「写文件 != 手拼shell|要正口·不拼字符串」
================================================================
"""
import sys, os, json
HOME = "/opt/masterd-wudi"
def _write_ok():
    try: return json.load(open(HOME+"/data/whitelist.json"))["write_ok"]
    except Exception: return [HOME+"/data", HOME+"/tools", HOME+"/code", HOME+"/logs", "/tmp"]
def w(path, content):
    ok = _write_ok()
    if not any(path.startswith(w) for w in ok):
        return "写入越界(不在白名单): "+path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(content)
    return "✅ 写了 %s (%d字)" % (path, len(content))
def cat(path):
    try: return open(path, encoding="utf-8").read()
    except Exception as e: return "读失败:"+str(e)[:80]
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv)>1 else ""
    if cmd=="write" and len(sys.argv)>3:
        print(w(sys.argv[2], cat(sys.argv[3])))
    elif cmd=="cat" and len(sys.argv)>2:
        print(cat(sys.argv[2]))
    else:
        print("用法: write <路径> <内容文件> | cat <路径>")
