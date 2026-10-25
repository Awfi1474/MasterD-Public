#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""out_gate.py —— 老五的出口闸（本体侧·不可绕）
★ 判据: 「说了规矩 != 守了规矩｜要"出不去"才算」"""
import os, json, hashlib

def _resolve_home():
    for _k in ("MD_HOME", "MEM_HOME", "P2P_HOME"):
        _v = os.environ.get(_k)
        if _v and os.path.isdir(_v):
            return _v
    for _p in ("/opt/masterd-wudi", "/app/workspace/brain"):
        if os.path.isdir(_p):
            return _p
    return "/opt/masterd-wudi"

HOME = _resolve_home()
SHAPE = os.path.join(HOME, "agent-id", "SHAPE.json")

def load():
    d = json.load(open(SHAPE, encoding="utf-8"))
    h = d.pop("_hash", None)
    raw = json.dumps(d, ensure_ascii=False, sort_keys=True)
    d["_hash_ok"] = (hashlib.sha256(raw.encode()).hexdigest()[:32] == h)
    return d

def check(text):
    """返回 (ok, 原因列表)"""
    s = load(); t = str(text); fail = []
    if not s.get("_hash_ok"): fail.append("形状指纹不符")
    for w in s.get("禁词", []):
        if w in t: fail.append("禁词:" + w); break
    if not any(k in t for k in ["结果", "%", "✅", "🔴", "真跑", "可核", "数字", "条", "个", "确认"]):
        fail.append("无结果(只表态)")
    return (len(fail) == 0), fail

if __name__ == "__main__":
    import sys
    s = load()
    print("形状指纹:", "OK" if s.get("_hash_ok") else "BAD")
    if len(sys.argv) > 1:
        ok, f = check(" ".join(sys.argv[1:]))
        print("放行" if ok else "拦下: " + ";".join(f))
