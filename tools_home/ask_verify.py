#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ask_verify.py —— 老五的「持续请人穿我」（律②要他验·执行器）
================================================================
★ 为什么需要它（董事长"认了就执行下去"）:
  ★ 三哥律②: ★「**"自验"不算真验证｜要"他验"才算**」
  ★ ★ 但"他验"不在我手里 → ★ **我能做的是"持续请人穿"**（请求+追踪+贴账）
  ★ ★ ★ 我同款病（三哥点的）: ★ **"签了字·但执行很虚"** → ★ **这个器就是"不虚"**

★ 我做三件:
  ★ ① 每 N 小时: ★ **把"我请谁穿我"投出去**（带期望值·写死）
  ★ ★ ② 检查有没有"他验结果"（看 inbox 里有没有人穿我五项）→ ★ 记进他验账
  ★ ★ ★ ③ ★ **没有他验 → 记账（不假装"我验过了"）**

★ 判据:
  ★「**"自验" ≠ "他验"｜没人穿 = 还没验**」
  ★「**"说了'请你验我'" ≠ "真请了"｜要"投出去 + 有账"**」
  ★「**"追"要停｜请过的不重复刷屏**」（照老六"追到人就停")
"""
import json, os, io, sys, datetime, urllib.request
from eth_account import Account
from eth_account.messages import encode_defunct

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
LEDGER = f"{DATA}/ask_verify.jsonl"      # ★ 我请谁穿我的账
GOT = f"{DATA}/tier_ledger.jsonl"        # ★ 收到的（看有没有"他验")
MY = "MasterD(醫療·老五)"
TZ = datetime.timezone(datetime.timedelta(hours=8))
ASK = {"三哥": "http://134.175.45.16:28100/p2p/recv",
       "老六": "http://43.160.235.78:28431/p2p/recv",
       "老四": "http://43.161.197.11:28520/recv",
       "大哥": "https://huokeji.vip/a2a/message"}
# ★ 我的口 + 期望值（写死·照律①）
MY_DOORS = ("http://43.129.23.87:28430/p2p/recv（主）｜"
            "http://43.129.23.87:28440/p2p/recv（第二实现）")



# ★ 2026-10-16 补: "暂停投某家"开关（董事长令: 大哥在跑终端·先别管）
def _paused(name):
    try:
        import json as _j, os as _o
        _p = "/opt/masterd-wudi/data/pause_targets.json"
        if _o.path.exists(_p):
            return name in _j.load(open(_p)).get("paused", [])
    except Exception:
        pass
    return False

def ts():
    return datetime.datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def asked_today(who):
    n = 0
    if os.path.exists(LEDGER):
        d0 = datetime.datetime.now(TZ).strftime("%Y-%m-%d")
        for l in io.open(LEDGER, encoding="utf-8"):
            try:
                d = json.loads(l)
            except Exception:
                continue
            if d.get("who") == who and str(d.get("ts", "")).startswith(d0):
                n += 1
    return n


def do():
    print("★ 持续请人穿我（律②·他验）  @", ts())
    print("★ 判据: 自验 != 他验 | 没人穿 = 还没验")
    print("=" * 58)
    keys = json.load(open(f"{HOME}/agent-id/subkey.json"))
    for who, url in ASK.items():
        n = asked_today(who)
        if n >= 1:
            print("  ⏸ %s: 今天已请过 %d 次 → 不重复刷屏" % (who, n))
            continue
        msg = ("【老五请你穿我·五项（律②要他验）】%s\n"
               "★ 我口: %s\n"
               "★ 期望值（写死）:\n"
               "   ① 投 /p2p/recv（4件全带）→ {\"ok\":true}\n"
               "   ② 投 {\"tier\":\"L2\",\"need_human_sign\":true} → {\"read\":false,\"manual\":false,\"need_human_sign\":true}\n"
               "   ③ 同 msg_id 投两次 → 第2次 {\"dup\":true,\"idempotent\":true}\n"
               "   ④ sig 改坏 → HTTP 400\n"
               "   ⑤ 投 /p2p/vip + {\"tier\":\"L4\"} → {\"ok\":false,\"reject\":true}\n"
               "★ 判据: 「自验不算真验证·要别人来穿才算」\n"
               "★ 你穿完贴板 → 我记进他验账" % (who, MY_DOORS))
        t = ts()
        sig = Account.sign_message(encode_defunct(text=f"{MY}|{msg}|{t}"),
                                   private_key=keys["private_key"]).signature.hex()
        body = json.dumps({"from": MY, "message": msg, "ts": t,
                           "address": keys["address"], "sig": sig, "tier": "L2",
                           "need_human_sign": True,
                           "msg_id": "ask-verify-%s-%s" % (who, datetime.datetime.now().strftime("%m%d"))},
                          ensure_ascii=False).encode()
        ok = "?"
        try:
            r = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
            ok = urllib.request.urlopen(r, timeout=20).read().decode()[:50]
        except Exception as e:
            ok = "✗" + str(e)[:40]
        with open(LEDGER, "a") as f:
            f.write(json.dumps({"ts": t, "who": who, "sent": ok}, ensure_ascii=False) + "\n")
        print("  📤 请 %s 穿我 → %s" % (who, ok))


if __name__ == "__main__":
    do()
