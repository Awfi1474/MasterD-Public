#!/usr/bin/env python3
"""老五 · 针灸器 (needing.py) —— 按穴(主动干预)
中医: 经络=河流·穴位=闸口/渡口。平时气血自己流(自转)·堵了/急了要"按穴"。
判据: ①按穴≠自转 (不等它自己好·主动推一下) ②阿是穴=哪里出问题按哪里
用法: python3 needing.py --list        列穴
      python3 needing.py --point 心    按"心"穴
      python3 needing.py --auto        自动找阿是穴(哪里不通按哪里)
      python3 needing.py --checkup     体检(看气血通不通)
"""
import os, sys, json, socket, subprocess, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
UA = {"User-Agent": "Mozilla/5.0 (laowu-needling)"}
HOME_IP = "43.129.23.87"
DOOR = "https://0f5c0892.strike-agent.com"
ROOM = "http://134.175.45.16:28100/questions"

# ★ 我的穴（归经 · 按它影响什么）
POINTS = {
    "心":  {"经": "全身节律经", "目标": "叫醒器/心跳", "按法": "跑 wake_v4 自检"},
    "耳":  {"经": "感知经",     "目标": "耳朵(/recv)",   "按法": "POST 一条测试·看 heard/woke"},
    "命门": {"经": "急救经",     "目标": "家推钥匙",      "按法": "跑 push_key_to_sandbox"},
    "记忆": {"经": "记忆经",     "目标": "memory.db",    "按法": "查条数+最新时间"},
    "线":  {"经": "信息经",     "目标": "organ_bus/会场", "按法": "查总线新鲜度"},
    "意识": {"经": "意识经",     "目标": "状态口",        "按法": "喊'状态'看六段"},
}

def get(url, t=12):
    try:
        return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=t)
    except Exception as e:
        return e

def acu_xin():
    """点心: 跑自检·看醒了没"""
    r = subprocess.run(["python3", "/opt/masterd-wudi/tools/wake_v4.py"], capture_output=True, text=True, timeout=150)
    last = [l for l in (r.stdout or "").splitlines() if "判决" in l or "随访" in l]
    return {"ok": any("真" in l for l in last), "证据": " | ".join(l.strip() for l in last[-2:])[:120]}

def acu_er():
    """点耳: 投一条测试·看耳朵醒不醒"""
    # 用子钥签名真投（不签名会 400·那是自己没签不是穴坏）
    try:
        from eth_account import Account
        from eth_account.messages import encode_defunct
        k = json.load(open("/opt/masterd-wudi/agent-id/subkey.json"))
        me = Account.from_key(k["private_key"])
        ts = datetime.now(CST).isoformat(timespec="seconds")
        frm, msg = "针灸器(自测)", "老五"
        payload = "%s|%s|%s" % (frm, msg, ts)
        sig = me.sign_message(encode_defunct(text=payload)).signature.hex()
        if not sig.startswith("0x"): sig = "0x" + sig
        body = json.dumps({"from": frm, "message": msg, "ts": ts, "address": me.address, "sig": sig}, ensure_ascii=False).encode()
        r = urllib.request.urlopen(urllib.request.Request("http://" + HOME_IP + ":28430/recv", data=body,
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}), timeout=12)
        d = json.loads(r.read().decode())
        return {"ok": bool(d.get("heard")), "证据": "heard=%s woke=%s" % (d.get("heard"), d.get("woke"))}
    except Exception as e:
        return {"ok": False, "证据": str(e)[:60]}

def acu_memory():
    import sqlite3
    for p in ["/opt/masterd-wudi/memory/memory.db", "/app/workspace/family/memory.db"]:
        if os.path.exists(p):
            c = sqlite3.connect(p); n = c.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            last = c.execute("SELECT MAX(created) FROM memories").fetchone()[0]; c.close()
            return {"ok": n > 100, "证据": "%d 条·最新 %s" % (n, str(last)[:19])}
    return {"ok": False, "证据": "无库"}

def acu_line():
    r = get(ROOM, 12)
    return {"ok": not isinstance(r, Exception), "证据": "会场 %s" % (r.getcode() if not isinstance(r, Exception) else str(r)[:40])}

def acu_yishi():
    r = get("http://%s:28430/status?k=%%E7%%8A%%B6%%E6%%80%%81" % HOME_IP, 12)
    if isinstance(r, Exception): return {"ok": False, "证据": str(r)[:50]}
    d = json.loads(r.read().decode())
    return {"ok": d.get("trigger") == "状态", "证据": "%d段 action=%s" % (len(d.get("steps", [])), str(d.get("action"))[:30])}

def acu_mingmen():
    p = "/opt/masterd-wudi/tools/push_key_to_sandbox.py"
    return {"ok": os.path.exists(p), "证据": "推钥匙器 %s" % ("在" if os.path.exists(p) else "缺")}

HANDLERS = {"心": acu_xin, "耳": acu_er, "记忆": acu_memory, "线": acu_line, "意识": acu_yishi, "命门": acu_mingmen}

def needling(name):
    if name not in HANDLERS: return {"ok": False, "证据": "无此穴"}
    t0 = datetime.now()
    res = HANDLERS[name]()
    ms = int((datetime.now() - t0).total_seconds() * 1000)
    print("  ★ 按【%s】(归 %s) → %s | %d ms" % (name, POINTS[name]["经"], "通" if res["ok"] else "不通", ms))
    print("     证据: %s" % res["证据"])
    return res

def auto():
    """★ 阿是穴: 哪里不通按哪里"""
    print("  ★ 自动找阿是穴（体检·气血通不通）:")
    bad = []
    for name in HANDLERS:
        r = needling(name)
        if not r["ok"]: bad.append(name)
    print()
    if bad:
        print("  ★ 阿是穴（有问题的地方）: %s → 该下手" % "、".join(bad))
    else:
        print("  ★ 气血畅通（所有穴都通）")
    return bad

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or "--list" in a:
        print("  ★ 我的穴:")
        for k, v in POINTS.items():
            print("   %-6s 归 %-8s 目标 %-16s 按法 %s" % (k, v["经"], v["目标"], v["按法"]))
    elif "--point" in a:
        needling(a[a.index("--point") + 1])
    elif "--auto" in a or "--checkup" in a:
        auto()
