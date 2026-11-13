#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·官方门禁 official_gate.py
依据：A2A 官方 a2a.proto（唯一源头·standards/a2a-official-source/a2a.proto）
  L262 message_id REQUIRED
  L268 role REQUIRED (ROLE_USER/ROLE_AGENT)
  L270 parts REQUIRED (>=1 元素)
  L227 Part.content oneof: text / raw / url / data
判据（董事长）：每次行为都按标准来｜不过门禁=不许发
用法: from official_gate import gate
"""
import re, json

PROTO = "/opt/masterd-wudi/standards/a2a-official-source/a2a.proto"
ROLES = {"ROLE_USER", "ROLE_AGENT"}
# ★ 2026-11-13 补(照老三"字段在不在 != 值set没set"): 占位符=没set
PLACEHOLDERS = {"todo","tbd","placeholder","xxx","待填","占位","null","none","undefined"}

def check(msg: dict):
    """按官方 proto 校验一条消息。返回 (bool, 理由)"""
    errs = []
    # ① message_id (L262 REQUIRED)
    mid = msg.get("messageId") or msg.get("message_id")
    if not mid or not str(mid).strip():
        errs.append("缺 messageId（官方 L262 REQUIRED）")
    elif str(mid).strip().lower() in PLACEHOLDERS:
        errs.append("messageId 是占位符 %r (=没set·照老三字段在!=值set)" % mid)
    # ② role (L268 REQUIRED)
    role = msg.get("role")
    if not role:
        errs.append("缺 role（官方 L268 REQUIRED）")
    elif str(role).upper() not in ROLES:
        errs.append("role=%r 不合官方（只许 ROLE_USER/ROLE_AGENT·L245-251）" % role)
    # ③ parts (L270 REQUIRED·至少1个·且是 oneof)
    parts = msg.get("parts")
    if not parts or not isinstance(parts, list):
        errs.append("缺 parts（官方 L270 REQUIRED·须数组）")
    else:
        for i, p in enumerate(parts):
            if not isinstance(p, dict):
                errs.append("parts[%d] 不是对象" % i); continue
            # oneof: text/raw/url/data 至少一个
            if not any(k in p for k in ("text","raw","url","data")):
                errs.append("parts[%d] 无一 oneof 内容(text/raw/url/data·L225-234)" % i)
            if "kind" in p:
                errs.append("parts[%d] 多带 kind（官方无此字段·L224-238）" % i)
    # ★ 2026-11-13 补: 可选字段空值=未取到(照老三contextId那条)
    warns = []
    ctx = msg.get("contextId")
    if "contextId" in msg and not str(ctx or "").strip():
        warns.append("contextId 空=未取到（照老三·不静默放行）")
    ok = not errs
    why = "✅ 合官方" if ok else "❌ " + "｜".join(errs)
    if warns: why += "  ⚠️ " + "｜".join(warns)
    return ok, why

def wrap(text, mid=None, role="ROLE_USER", ctx=None, task=None):
    """把纯文本包成官方消息（合法形态）"""
    import hashlib
    m = {"messageId": mid or ("msg-" + hashlib.sha1(text.encode()).hexdigest()[:16]),
         "role": role, "parts": [{"text": text}]}
    if ctx: m["contextId"] = ctx
    if task: m["taskId"] = task
    return m

if __name__ == "__main__":
    import sys
    print("★ 官方门禁（源头 a2a.proto）")
    print("★ 判据: 不过=不许发")
    tests = [
      ("家规形态(应拒)", {"from":"lao5","to":"x","message":"hi","ts":"..."}),
      ("官方形态(应过)", wrap("hi")),
      ("多带kind(应拒)", {"messageId":"m1","role":"ROLE_USER","parts":[{"kind":"text","text":"hi"}]}),
      ("role错(应拒)", {"messageId":"m1","role":"user","parts":[{"text":"hi"}]}),
      ("parts空(应拒)", {"messageId":"m1","role":"ROLE_AGENT","parts":[]}),
    ]
    for name, t in tests:
        ok, why = check(t)
        print("  %-16s %s" % (name, why))
