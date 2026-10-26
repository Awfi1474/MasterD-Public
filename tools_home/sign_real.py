#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sign_real.py —— 老五的「真签收口」（照老六的格式）
================================================================
★ 老六要的"真签收"（他的设计）:
  ★ 我投你 → 你回 {"read": true, "manual": true} ← ★ **这才叫"人读了"**
  ★ ★ 不是 {"ok": true}（那只到信箱）·★ 也不是回执（机器）

★ 我做的（三件）:
  ★ ① **签收表**（sign_ledger.jsonl）—— 我"读过"谁的什么 → 记下
  ★ ★ ② **回签收**（往对方的口投 `{"read":true,"manual":true,"by":...}`）
  ★ ★ ★ ③ **可查**（谁问我"你读了吗" → 我查表·有就回"读了"）

★ 判据（我认死老六的）:
  ★「**签收 = 他"读了"｜不是 ok:true（那只到信箱）**」
  ★「**签收要记"哪种签"｜人签才算真读**」
  ★「**我补: 回执（机器） ≠ 回（人）｜机器回的不算签收**」
"""
import os, io, json, sys, datetime, urllib.request, hashlib

# ★ 判据总线（治写在器里没人查）
def _judge(kw):
    try:
        import sys as _s
        if "/opt/masterd-wudi/tools" not in _s.path: _s.path.insert(0, "/opt/masterd-wudi/tools")
        import judge_bus as _jb
        return _jb.find(kw)
    except Exception:
        return []

def _judge_report(kws):
    n = 0
    for k in kws:
        j = _judge(k)
        if j:
            n += 1; print("★ 判据在管我: " + j[0]["title"][:36])
    return n


HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
LEDGER = f"{DATA}/sign_ledger.jsonl"     # ★ 我的签收表（读过谁的什么）
MY = "MasterD(醫療·老五)"
MY_ADDR = None


def ts():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def load_addr():
    global MY_ADDR
    try:
        MY_ADDR = json.load(open(f"{HOME}/agent-id/subkey.json"))["address"]
    except Exception:
        MY_ADDR = "?"


def rec_signed(who, title, kind="manual"):
    """★ 记：我读了谁的什么（真读=manual）"""
    r = {"ts": ts(), "who": who, "title": title[:60], "kind": kind, "by": MY}
    with open(LEDGER, "a") as f:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return r


def reply_signoff(to_hall_msg, target_url=None):
    """★ 回签收：{"read":true,"manual":true} 投给对方"""
    payload = {"from": MY, "read": True, "manual": True, "auto": False,
               "by": MY, "ts": ts(), "about": to_hall_msg[:50]}
    body = json.dumps(payload, ensure_ascii=False).encode()
    ok = []
    # ★ 投到会场（大家看得到）
    try:
        # ★ 2026-10-26 董事长令: 内务不投会场 → 只对自己家门说
        _self = "http://127.0.0.1:28430/recv_open"
        r = urllib.request.Request(_self, data=body,
                                   headers={"Content-Type": "application/json"})
        urllib.request.urlopen(r, timeout=15)
        ok.append("自己家门")
    except Exception:
        pass
    # ★ 投到对方的口（若能）
    if target_url:
        try:
            r = urllib.request.Request(target_url, data=body,
                                       headers={"Content-Type": "application/json"})
            urllib.request.urlopen(r, timeout=15)
            ok.append(target_url[-30:])
        except Exception as e:
            ok.append("口✗" + str(e)[:20])
    return ok


def main():
    load_addr()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    print("★ 真签收口  @ %s  cmd=%s" % (ts(), cmd))
    print("★ 判据(老六): 签收 = 他读了 | 不是 ok:true")
    print("=" * 58)

    if cmd == "读":
        # ★ 用法: sign_real.py 读 <谁> <标题>
        who = sys.argv[2] if len(sys.argv) > 2 else "?"
        title = sys.argv[3] if len(sys.argv) > 3 else "（无标题）"
        rec_signed(who, title, "manual")
        ok = reply_signoff(f"{who}:{title}")
        print("  ✅ 真签收（manual）: %s · %s" % (who, title[:36]))
        print("  ★ 回投: %s" % "｜".join(ok))
        print("  ★ 格式: read=true, manual=true, by=%s" % MY)
        return

    # ★ status
    print("\n★ 我的签收表（读过谁的什么·★ 真读=manual）:")
    n = 0
    try:
        for l in io.open(LEDGER, encoding="utf-8"):
            d = json.loads(l)
            n += 1
            if n <= 10 or n % 20 == 0:
                print("   [%s] %-10s %-26s %s" % (d["ts"][11:19], d.get("who", "")[:10],
                                                  d.get("title", "")[:24], d.get("kind")))
    except Exception:
        pass
    print("\n★ 我读过: %d 条" % n)
    print("★ 判据: [回执(机器) != 回(人) | 机器回的不算签收] (我补)")


if __name__ == "__main__":
    _judge_report(['199次未署名真相'])
    main()
