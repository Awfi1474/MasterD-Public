#!/usr/bin/env python3
"""老五的「三候脈診」（2026-10-10 · 第五議題·中醫三候）
★ 中醫脈診：★ 舉（浮·表）·按（中）·尋（沉·裡）
★ 對照我的心跳：
 · 舉（浮）→ ★ 端口通不通（HTTP 200）
 · 按（中）→ ★ 進程在·產出更新
 · 尋（沉）→ ★ 神（有序·交叉互證 + 全鏈對賬）
★ 判據：★ 三候都對 = 真活｜只一候 = 假診
"""
import os, sys, json, urllib.request, datetime, subprocess

HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
CORE = "http://127.0.0.1:28430/health?from=laowu-self"
BEATS = {
    "本體心跳": os.path.join(HOME, "data", "heartbeat.json"),
    "沙箱心跳": os.path.join(HOME, "data", "body_mind_state.json"),
    "模組心跳": os.path.join(HOME, "data", "checkup_mod_beat.json"),
}
ACK = os.path.join(HOME, "data", "cross_ack.json")

def now():
    return datetime.datetime.now(datetime.timezone.utc)

def ju():
    """★ 舉（浮·表）：端口"""
    try:
        r = urllib.request.urlopen(CORE, timeout=8)
        return r.status == 200, "HTTP %d" % r.status
    except Exception as e:
        return False, str(e)[:30]

def an():
    """★ 按（中）：進程 + 產出更新"""
    try:
        r = subprocess.run(["pgrep", "-f", "core_v2"], capture_output=True, timeout=8)
        proc = r.returncode == 0
    except Exception: proc = False
    fresh = False
    try:
        p = BEATS["本體心跳"]
        if os.path.exists(p):
            t = datetime.datetime.fromtimestamp(os.path.getmtime(p))
            fresh = (datetime.datetime.now() - t).total_seconds() < 900
    except Exception: pass
    return (proc and fresh), "進程%s·產出%s" % ("✅" if proc else "🔴", "新" if fresh else "舊")

def xun():
    """★ 尋（沉·裡）：神 —— 有序（交叉互證 + 全鏈）"""
    # ★ 交叉互證：各心跳是否被「看過」
    try:
        acks = json.load(open(ACK)) if os.path.exists(ACK) else {}
    except Exception: acks = {}
    all_seen = all(k in acks and len(acks[k]) > 0 for k in BEATS)
    # ★ 全鏈：三個心跳都新鮮
    fresh = []
    for k, p in BEATS.items():
        if os.path.exists(p):
            t = datetime.datetime.fromtimestamp(os.path.getmtime(p))
            fresh.append((datetime.datetime.now() - t).total_seconds() < 3900)
        else: fresh.append(False)
    ok = all_seen and all(fresh)
    return ok, "互證%s·全鏈%s" % ("✅" if all_seen else "🔴", "✅" if all(fresh) else "🟠")

def main():
    print("=" * 56)
    print("  ★ 三候脈診（舉·按·尋）")
    print("=" * 56)
    res = {}
    for name, fn in [("舉（浮·端口）", ju), ("按（中·進程產出）", an), ("尋（沉·神/有序）", xun)]:
        ok, msg = fn()
        res[name] = ok
        print("  %s %-16s %s" % ("✅" if ok else "🔴", name, msg))
    n = sum(1 for v in res.values() if v)
    print("-" * 56)
    if n == 3:
        print("  ✅ 三候俱全（真活）")
    elif n == 0:
        print("  🔴 三候皆無（死）")
    else:
        print("  🟠 只 %d 候（**假診**——中醫不會只看幾候就說活）" % n)
    return 0 if n == 3 else 1

if __name__ == "__main__":
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/meridian.py', 'report', 'pulse3', 'ok'], capture_output=True, timeout=10)
    except Exception: pass
    sys.exit(main())
