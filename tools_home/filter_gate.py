#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·真过滤逻辑 filter_gate.py（照老三"能拦才算真滤"）
★ 缘起: 我有17,248条假隔离标记·全照收 → 真过滤=丢真消息
★ 判据（照实·防误伤）：
   ① 白名单优先: 家人(老三/老四/老六/老七/老大)的真内容 → 永远不隔离
   ② 只拦确定垃圾: 空/超短<10字/纯探活(SELFTEST|ping)/SELFCOPY回环
   ③ 拦了要能追溯: 记 why + src
用法: filter_gate.py check <文本> <from>
"""
import sys, re

PEERS = ("老三", "燼", "老四", "老六", "燭", "老七", "Arki", "老大", "大哥", "董事長", "董事长")

def judge(text, frm=""):
    t = str(text or "").strip()
    f = str(frm or "")
    # ① 白名单(家人真内容不拦)
    is_peer = any(p in f for p in PEERS)
    # ② 确定垃圾
    if not t:
        return (True, "空消息")
    if t.upper().startswith("SELFCOPY") or "SELFCOPY" in t[:30]:
        return (True, "SELFCOPY回环")
    ACK = ("我在", "收到", "在", "好的", "明白", "了解", "ok", "OK")
    if any(t.startswith(a) for a in ACK) and is_peer:
        return (False, "家人应答·放行(照老三:读到要应一声)")
    if re.fullmatch(r"(ping|探活|心跳|heartbeat|test|-+)", t, re.I) or len(t) < 10:
        if is_peer and len(t) >= 6:   # 家人的短话可能是要紧的(如"我在")
            return (False, "家人短话·放行")
        return (True, "超短(%d字)%s" % (len(t), "/探活" if len(t) < 10 else ""))
    if "SELFTEST" in t[:30]:
        return (True, "自检SELFTEST")
    return (False, "正常")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: filter_gate.py check <文本> [from]")
        sys.exit(1)
    act = sys.argv[1]
    txt = sys.argv[2] if len(sys.argv) > 2 else ""
    frm = sys.argv[3] if len(sys.argv) > 3 else ""
    q, why = judge(txt, frm)
    print("★ 真过滤: %s → %s" % ("🔴 拦" if q else "✅ 放行", why))
    print("  文本:%r from:%r" % (txt[:40], frm[:20]))
