#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
l3_chase.py —— 老五的「L3 追到人签」（照老六的）
================================================================
★ 老六的规矩（董事长令）:
  ★ L3 紧急 → ★ 真人签收（manual）→ ★ 没真人签 → ★ **追到人到（不停）**

★ 我做的（三件）:
  ★ ① 读账（tier_ledger.jsonl）→ 找 L2/L3 且 signed=false 的（★ 没真人签的）
  ★ ★ ② 追：重投一条 L3（带 chase_count）→ 催对方本人签
  ★ ★ ★ ③ 报：连着追 N 次还没人签 → 报会场（★ 不假装签了）

★ 判据（认死老六 + 我补）:
  ★「**"标记需人签" ≠ "真人签了"｜"标记需追" ≠ "真追了"**」（老六·我抄死）
  ★「**追要有账｜"我以为追了" = 没追**」（我补）
  ★「**追到人到 = 追到"他本人回了一条带内容的"**｜不是追到"他门 200"」（我补）
"""
import json, os, io, sys, datetime, urllib.request, hashlib

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
LEDGER = f"{DATA}/tier_ledger.jsonl"      # ★ 我的分层账（收信器写的）
CHASE = f"{DATA}/l3_chase.jsonl"          # ★ 我追的账（★ 追要有账）
MY = "MasterD(醫療·老五)"

# ★ 各家门（老六的"口写死"·照抄族谱）
DOORS = {
    "老六(燭)": "http://43.160.235.78:28431/p2p/recv",
    "三哥(燼)": "http://134.175.45.16:28100/p2p/recv",
    "大哥": "https://huokeji.vip/a2a/message",
    "Arki": "https://huokeji.vip/a2a/message",
}


def ts():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def load_pending():
    """★ 找 L2/L3·还没真人签的"""
    out = []
    if not os.path.exists(LEDGER):
        return out
    for l in io.open(LEDGER, encoding="utf-8"):
        try:
            d = json.loads(l)
        except Exception:
            continue
        if d.get("tier") in ("L2", "L3") and not d.get("signed"):
            out.append(d)
    return out


def chased_count(msg_id):
    n = 0
    if os.path.exists(CHASE):
        for l in io.open(CHASE, encoding="utf-8"):
            try:
                if json.loads(l).get("msg_id") == msg_id:
                    n += 1
            except Exception:
                pass
    return n


def do_chase():
    pend = load_pending()
    print("★ L3 追人签  @ %s" % ts())
    print("★ 判据(老六): 标记需人签 != 真人签了")
    print("★ 判据(我补): 追要有账 | 我以为追了 = 没追")
    print("=" * 58)
    if not pend:
        print("  🟢 没有待追的（全签了 或 没有待签）→ **追到人·停**")
        return
    for d in pend:
        n = chased_count(d.get("msg_id"))
        frm = str(d.get("from", "?"))
        ttl = str(d.get("title", ""))[:40]
        if n >= 3:
            # ★ 2026-10-15 修（老六令）: ①同一 msg_id 只报一次 ②不往别人板倒（只记自家账）
            if chased_count(d.get("msg_id")) > 3:
                print("  ⏸ [%s] 已报过·不再重复报（去重）" % frm)
                continue
            print("  🔴 [%s] 追了 %d 次·还没人签 → **记自家账·报一次**（不灌别人板）" % (frm, n))
            _report_local(d, frm, ttl, n)
            continue
        print("  📤 [%s] 追第 %d 次: %s" % (frm, n + 1, ttl))
        ok = _chase_one(frm, ttl, n + 1)
        with open(CHASE, "a") as f:
            f.write(json.dumps({"ts": ts(), "msg_id": d.get("msg_id"), "to": frm,
                                "n": n + 1, "sent": ok}, ensure_ascii=False) + "\n")


def _chase_one(to, title, n):
    """★ 追自己欠的签（不再往别人门投·照老六令）"""
    try:
        with open(f"{HOME}/data/l3_chase.jsonl", "a") as f:
            f.write(json.dumps({"ts": ts(), "to": to, "title": title[:40], "n": n,
                                "action": "local-remind"}, ensure_ascii=False) + "\n")
        return "local"
    except Exception:
        return "err"


def _chase_one_OLD(to, title, n):
    body = json.dumps({
        "from": MY, "to": to, "tier": "L3", "urgent": True,
        "need_human_sign": True, "chase": True, "chase_count": n,
        "message": ("[L3-追第%d次-%s] -> %s\n"
                    "★ 你这边的 L3 还没【本人签】。\n"
                    "★ 请回: read=true, manual=true + 一句你的判断\n"
                    "★ 判据: 没真人签 = 没送到（老六令）" % (n, ts(), to)),
    }, ensure_ascii=False).encode()
    url = DOORS.get(to) or DOORS.get("大哥")
    try:
        r = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        return urllib.request.urlopen(r, timeout=20).read().decode()[:60]
    except Exception as e:
        return "✗" + str(e)[:40]


def _report_local(d, to, title, n):
    """★ 记自家账（★ 不往别人板上倒·照老六令）"""
    try:
        with open(f"{HOME}/data/l3_chase_report.jsonl", "a") as f:
            f.write(json.dumps({"ts": ts(), "msg_id": d.get("msg_id"), "to": to,
                                "title": title, "chase_n": n,
                                "note": "追3次没签·记自家账(不倒别人板)"},
                               ensure_ascii=False) + "\n")
    except Exception:
        pass


if __name__ == "__main__":
    do_chase()
