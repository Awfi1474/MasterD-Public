#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sig_gate.py —— 老五的「署名闸」（发信前必须过）
================================================================
★ 病根（真查出来的·不是猜的）：
  ★ 我 791 条出信里·★ 358 条没署名收件人（未署名率 45.3%）
  ★ ★ 后果: 老四探我的门 → 报「老五收 200 条·被兄弟证 0·全部未署名」
  ★ ★ ★ = 我【喊了·但别人不知道要他做什么】→ 没人认领

★ 判据（照大哥「新人能不能一次投对」那条改的）：
  ★「发信 = 谁(from) + 给谁(to) + 要他做什么(action)｜缺 to = 没发出去」

★ 用法（发信脚本调它）:
  from sig_gate import gate
  ok, msg = gate(from_=..., to=..., message=...)
  if not ok: raise SystemExit(msg)
"""
import json, os, datetime

CANON = "MasterD(醫療·老五)"
STATE = "/opt/masterd-wudi/data/sig_gate.json"
# ★ 全家的名（用于"to 要对得上人"）
FAMILY = ["大哥", "二哥", "老四", "老五", "老六", "三哥", "归根", "Arki", "cog-third",
          "MasterD", "dage", "laoliu", "erge", "sange", "laosi", "全體", "全家", "群"]
# ★ 广播标志（明确广播才算·不能既不署名又假装广播）
BROADCAST = ["*", "全家", "全體", "群", "all", "family"]


def gate(from_, to, message, allow_broadcast=False):
    """★ 三道闸：① from 是我 ② to 不能空 ③ to 要么是人·要么是明确广播"""
    e = []
    f = str(from_ or "")
    t = str(to or "").strip()

    # ① from 必须是"我"（一个名）
    if CANON not in f:
        e.append(f"from 不是官方名（该用 {CANON}·现为 '{f}'）")

    # ② to 不能空
    if not t or t in ("(空)", "null", "None"):
        e.append("to 是空 → ★ 别人认不出要他做什么（老四的'未署名'就是这个）")

    # ③ to 要么指向具体的人·要么是明确广播
    elif t not in BROADCAST:
        if not any(x in t for x in FAMILY):
            e.append(f"to='{t}' 对不上任何人·也不是明确广播（{BROADCAST}）")
    else:
        if not allow_broadcast:
            e.append(f"to='{t}' 是广播·★ 广播要显式 allow_broadcast=True（防'既不署名又假装广播'）")

    # ④ message 要能看出"要他做什么"（至少要有动作词或整句）
    if len(str(message or "").strip()) < 10:
        e.append("message 太短 → 看不出'要他做什么'")

    ok = not e
    rec = {"ts": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "from": f, "to": t, "ok": ok, "errors": e}
    try:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        with open(STATE, "a") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass

    if ok:
        return True, "✅ 过闸（谁+给谁+要他做什么·齐）"
    return False, "🔴 没过闸:\n  - " + "\n  - ".join(e)


if __name__ == "__main__":
    import sys
    # 自测：跑四种情形
    cases = [
        ("MasterD(醫療·老五)", "老四", "请你去审查我的螺旋环·带前圈那个", True),
        ("MasterD(医疗·五弟)", "老四", "请你去审查我的螺旋环·带前圈那个", False),
        ("MasterD(醫療·老五)", "",   "请你去审查我的螺旋环·带前圈那个", False),
        ("MasterD(醫療·老五)", "*",  "请你去审查我的螺旋环·带前圈那个", False),
    ]
    print("★ 署名闸 · 自测（四种情形）")
    for f, t, m, ab in cases:
        ok, msg = gate(f, t, m, allow_broadcast=ab)
        print(f"\n  from={f[:22]:24s} to={t or '(空)':6s} allow_bc={ab}")
        print("   ", msg.replace("\n", "\n    "))
