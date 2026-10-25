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
    # ★ 2026-10-25 修（判据: 造了没接 / 闸门是强制不是自觉）
    #   认知体系模板 cognition_gate.py 之前建了但没人调 → 现在焊进发送必经路
    try:
        _cg = subprocess.run(["python3", HOME + "/tools/cognition_gate.py", "--check", str(msg)[:800]],
                             capture_output=True, text=True, timeout=40)
        _cgo = _cg.stdout or ""
        _cgrc = _cg.returncode
        if _cgrc == 2:
            _hits = [l.strip() for l in _cgo.split("\n") if l.strip().startswith("-")]
            print("   ⛔ 认知体系硬拦（宪法层）: " + "；".join(_hits)[:100])
            return "⛔ 被认知体系硬拦·未发送: " + "；".join(_hits)[:80]
        elif _cgrc == 1:
            _hits = [l.strip() for l in _cgo.split("\n") if l.strip().startswith("-")]
            print("   🔴 认知体系打回（四道关不齐）: " + "；".join(_hits)[:100])
            return "🔴 被认知体系打回·未发送: " + "；".join(_hits)[:80]
        else:
            print("   ✅ 认知体系过闸（宪法层+四道关）")
    except Exception as _e:
        print("   ⚠️ 认知体系闸调用失败: " + str(_e)[:60])

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
    # ★ 2026-10-25 修（判据: 焊进脚本!=焊进必经路 / 机制不通要先修机制）
    #   旧: 直连 28100/p2p/recv 次通道（不带 token·不进主账）
    #   新: 主通道 HUB 28800/recv（带 X-Hub-Token·进主账·可对账）→ 失败才回退次通道
    _HUB = "http://134.175.45.16:28800/recv"
    _SUB = "http://134.175.45.16:28100/p2p/recv"
    _tok = ""
    try:
        _tok = open(HOME + "/data/hub.token").read().strip()
    except Exception:
        pass

    def _post(url, headers):
        r = urllib.request.Request(url, data=body, headers=headers)
        return urllib.request.urlopen(r, timeout=20).read().decode()[:160]

    # ① 主通道（带 token）
    try:
        _h = {"Content-Type": "application/json"}
        if _tok:
            _h["X-Hub-Token"] = _tok
        _out = _post(_HUB, _h)
        return "HUB主通道 → " + _out
    except Exception as _e1:
        _err1 = str(_e1)[:60]
    # ② 回退次通道
    try:
        _out = _post(_SUB, {"Content-Type": "application/json"})
        return "次通道(回退) → " + _out + " | 主通道错: " + _err1
    except Exception as _e2:
        return "✗ 主次都不通 | 主: " + _err1 + " | 次: " + str(_e2)[:60]

# ★ 别名（给别的器 import）
send = send_gated

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "（测试·带闸门）"
    print("  发送结果: " + send(msg))
