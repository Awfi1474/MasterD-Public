#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""send_with_gate.py —— 带闸门的发送（★ 法: 焊在必经之路）
★ 任何"发群/发信"·必须先过 think_gate send（跳判据）·再发
★ 判据: 「"提醒我记得" != "自动出现"｜要焊在必经之路上」
"""
import os, sys, json, subprocess, urllib.request, datetime

HOME = "/opt/masterd-wudi"

# ═══════════════════════════════════════════════════════════
# ★ 2026-10-26 董事长令：机器人发群消息限次
#   规则：同一个问题 最多 3 次｜每 10 分钟最多 1 次｜发完 3 次闭嘴
#   判据：「信息泛滥 = 没人管｜节制 = 器管住」
#   目的：防信息泛滥，不防"真该报的"
# ═══════════════════════════════════════════════════════════
RATE_FILE = HOME + "/data/send_rate.json"
RATE_MAX = 3            # 同一问题最多发几次
RATE_WINDOW_MIN = 10    # 每多少分钟最多 1 次
RATE_COOLDOWN_H = 6     # 发满 3 次后，多少小时内不再发同一问题

def _rate_key(msg):
    """用消息前 40 字做指纹（同一个问题 = 同一个 key）"""
    import hashlib
    head = str(msg)[:40].strip()
    return hashlib.md5(head.encode()).hexdigest()[:12]

def rate_check(msg):
    """返回 (allowed, reason)"""
    import time
    try:
        d = json.load(open(RATE_FILE)) if os.path.exists(RATE_FILE) else {}
    except Exception:
        d = {}
    k = _rate_key(msg)
    now = time.time()
    rec = d.get(k) or {"count": 0, "last_ts": 0, "first_ts": 0}
    # ① 发满 3 次 → 冷却期内闭嘴
    if rec["count"] >= RATE_MAX:
        if now - rec.get("last_ts", 0) < RATE_COOLDOWN_H * 3600:
            return False, "已发满 %d 次（同一问题）·冷却 %dh 内不再发" % (RATE_MAX, RATE_COOLDOWN_H)
        rec = {"count": 0, "last_ts": 0, "first_ts": 0}   # 冷却期过，重置
    # ② 距上次不足 10 分钟 → 不发
    if now - rec.get("last_ts", 0) < RATE_WINDOW_MIN * 60:
        wait = int(RATE_WINDOW_MIN * 60 - (now - rec.get("last_ts", 0)))
        return False, "距上次 %ds·还需等 %ds（每 %d 分钟最多 1 次）" % (int(now - rec.get("last_ts", 0)), wait, RATE_WINDOW_MIN)
    return True, "OK"

def rate_record(msg):
    """记录一次发送"""
    import time
    try:
        d = json.load(open(RATE_FILE)) if os.path.exists(RATE_FILE) else {}
    except Exception:
        d = {}
    k = _rate_key(msg)
    now = time.time()
    rec = d.get(k) or {"count": 0, "last_ts": 0, "first_ts": 0}
    rec["count"] = rec.get("count", 0) + 1
    rec["last_ts"] = now
    if not rec.get("first_ts"): rec["first_ts"] = now
    d[k] = rec
    try:
        os.makedirs(HOME + "/data", exist_ok=True)
        json.dump(d, open(RATE_FILE, "w"), ensure_ascii=False, indent=1)
    except Exception: pass
    return rec["count"]


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
    # ★ 2026-10-26 董事长令：先过限次闸（防信息泛滥）
    _ok, _why = rate_check(msg)
    if not _ok:
        print("   ⛔ 限次闸: " + _why)
        return "⛔ 限次闸拦下·未发送: " + _why
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
        _n = rate_record(msg)
        return "HUB主通道 → " + _out + " | 本问题已发 %d/%d 次" % (_n, RATE_MAX)
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
