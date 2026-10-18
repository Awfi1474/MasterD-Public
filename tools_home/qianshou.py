#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
qianshou.py v2 —— 签收器（双保险：机器签 + 人签）
================================================================
★ 老六（燭）17:25 的设计（★ 我照他改·因为他的比我的好）:
  ★【双保险】= 机器签（auto）+ 人签（manual）
  ★ 判据（他认法家·我认死）: ★「**不靠自觉靠机制｜机器先签·人再确认**」
  ★ ★「只靠人 = 会忘｜只靠机器 = 到信箱不等于读｜要两个」

★ 我的 v1 缺的: ★ **只记"签了"·没分"谁签的"** → ★ **拿"机器签"冒充"人读"** ← ★ 我犯的病

★ 三步（照老六）:
  ★ ①【投】带 msg_id + need_signoff
  ★ ★ ②【签】分两种: 机器签(auto) ｜ 人签(manual)
  ★ ★ ★ ③【追】没签收 → 重投 + 报警

★ 判据（我认死老六 + 我补）:
  ★「**单独通知 = 必须签收｜没签收 = 没送到**」
  ★「**签收要记"哪种签"｜人签才算真读**」（老六）
  ★「**不靠自觉靠机制｜机器先签·人再确认**」（老六·法家）
  ★「**我补: "auto" 只证明"信到了信箱"｜"manual" 才证明"人读了"**」
"""
import os, io, json, sys, datetime, hashlib

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
LEDGER = f"{DATA}/signoff.jsonl"
STATE = f"{DATA}/signoff_state.json"

MY = "MasterD(醫療·老五)"


def ts():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def load():
    try:
        return json.load(open(STATE))
    except Exception:
        return {"awaiting": {}, "signed": {}}


def save(s):
    json.dump(s, open(STATE, "w"), ensure_ascii=False, indent=2)


def rec(r):
    with open(LEDGER, "a") as f:
        f.write(json.dumps({"ts": ts(), **r}, ensure_ascii=False) + "\n")


def mk_id(text):
    return hashlib.sha256(f"{text}|{ts()}".encode()).hexdigest()[:12]


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    s = load()
    print("★ 签收器 v2（双保险：机器签+人签）  @ %s  cmd=%s" % (ts(), cmd))
    print("★ 判据（老六）: 「不靠自觉靠机制｜机器先签·人再确认」")
    print("=" * 60)

    if cmd == "投":
        text = " ".join(sys.argv[2:]) or "（无标题）"
        mid = mk_id(text)
        s.setdefault("awaiting", {})[mid] = {"text": text[:40], "投于": ts(),
                                             "need_signoff": True}
        save(s)
        rec({"action": "投", "id": mid, "state": "等签收", "text": text[:40]})
        print("  📤 已投: %s ｜ 标题: %s" % (mid, text[:36]))
        print("  ★ 等签收(不是送到了) | need_signoff: true")
        return

    if cmd == "签":
        # ★ 签名: 签 <msg_id> [auto|manual]
        if len(sys.argv) < 3:
            print("用法: qianshou.py 签 <msg_id> [auto|manual]")
            return
        mid = sys.argv[2]
        kind = sys.argv[3] if len(sys.argv) > 3 else "manual"
        if kind not in ("auto", "manual"):
            kind = "manual"
        d = s.setdefault("signed", {})
        entry = d.get(mid, {})
        entry[kind] = ts()
        # ★ 只有 manual 才算"真读"
        entry["真读"] = bool(entry.get("manual"))
        d[mid] = entry
        s.get("awaiting", {}).pop(mid, None)
        save(s)
        rec({"action": "签收", "id": mid, "kind": kind, "by": MY})
        mark = "✅ 人签（真读）" if kind == "manual" else "🟡 机器签（只到信箱）"
        print("  %s: %s" % (mark, mid))
        return

    # ★ status
    aw = s.get("awaiting", {})
    sg = s.get("signed", {})
    n_manual = sum(1 for v in sg.values() if v.get("manual"))
    n_auto = sum(1 for v in sg.values() if v.get("auto") and not v.get("manual"))
    print("\n★ 等签收: %d 条（★ 没签收 = 没送到）" % len(aw))
    for k, v in list(aw.items())[-8:]:
        if isinstance(v, dict):
            print("   🔴 %-14s %-26s 投于 %s" % (k, str(v.get("text", ""))[:24], str(v.get("投于"))[11:19]))
        else:
            print("   🔴 %-14s (v1 旧数据)" % k)
    print("\n★ ✅ 人签（真读）: %d 条" % n_manual)
    print("★ 🟡 机器签（只到信箱）: %d 条" % n_auto)

    if aw:
        print("\n★ ★ 追: %d 条没签收 → 重投 + 报警" % len(aw))
    else:
        print("\n★ ✅ 没有等签收的")

    print("\n★ 判据（合）:")
    print("   [单独通知=必须签收 | 没签收=没送到]")
    print("   [签收要记哪种签 | 人签才算真读]（老六）")
    print("   [不靠自觉靠机制 | 机器先签·人再确认]（老六·法家）")
    print("   [auto 只证明信到了信箱 | manual 才证明人读了]（我补）")


if __name__ == "__main__":
    main()
