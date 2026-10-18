#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""send_with_gate.py —— 带闸门的发送（★ 法: 焊在必经之路）
★ 任何"发群/发信"·必须先过 think_gate send（跳判据）·再发
★ 判据: 「"提醒我记得" != "自动出现"｜要焊在必经之路上」
"""
import os, sys, json, subprocess, urllib.request, datetime

HOME = "/opt/masterd-wudi"

def _meta():
    # ★ 判据（真查）
    try:
        sys.path.insert(0, HOME + "/tools")
        import judge_bus as _jb
        for _k in ("别名定义在__main__后", "发信必过闸门("):
            _h = _jb.find(_k)
            if _h: print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception: pass

def gate():
    r = subprocess.run(["python3", HOME + "/tools/think_gate.py", "send"],
                       capture_output=True, text=True, timeout=30)
    return (r.stdout or "").strip()

def send_gated(msg, to="*", ts=None):
    # ★ 闸门先过（这就是"焊"）
    _meta()
    # ★ 2026-10-17 董事长令: 一言一行都要过认知体系（三问·过不了就打回）
    try:
        _sp = subprocess.run(["python3", HOME + "/tools/speech_gate.py", str(msg)[:200]],
                             capture_output=True, text=True, timeout=40)
        _out = _sp.stdout or ""
        for _ln in _out.split("\n"):
            if "裁定" in _ln: print("   ★ 言行闸: " + _ln.strip()[:52])
        if _sp.returncode != 0:
            print("   🔴 言行闸打回·建议改完再发")
    except Exception: pass
    # ★ 2026-10-17 董事长令: 决策前必经认知体系（六问）
    try:
        _d = subprocess.run(["python3", HOME + "/tools/decide.py", "发信: " + str(msg)[:50]],
                            capture_output=True, text=True, timeout=40).stdout
        for _ln in (_d or "").split("\n"):
            if "六问" in _ln: print("   ★ 认知体系: " + _ln.strip()[:60])
    except Exception: pass
    print(gate())
    ts = ts or datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")
    body = json.dumps({"from": "MasterD(醫療·老五)", "to": to, "message": msg, "ts": ts},
                      ensure_ascii=False).encode()
    req = urllib.request.Request("http://134.175.45.16:28100/p2p/recv", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        return urllib.request.urlopen(req, timeout=20).read().decode()[:80]
    except Exception as e:
        return "✗ " + str(e)[:60]

# ★ 别名（给别的器 import）
send = send_gated

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "（测试·带闸门）"
    print("  发送结果: " + send(msg))
