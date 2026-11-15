#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·写入门禁 require_decide（照本体判断「闸装走廊·事在房间做」）
★ 判据: 写操作必须带「本次已过六问」的凭证·没凭证=硬拒
★ 凭证带时间戳·超 5 分钟失效(防一次过闸到处用)
用法:
  from require_decide import require_decide
  require_decide("改 p2p_mailbox.py")     # 没凭证 → PermissionError
  # 或先过六问: python3 require_decide.py pass "<决定>"
"""
import os, sys, time, json, hashlib

TOKEN_FILE = "/opt/masterd-wudi/data/decide_pass.json"
TTL = 60   # ★ 2026-11-15 改: 60秒(防一次过闸到处用)

def _now():
    return time.time()

def issue(decision=""):
    """过六问后发凭证（由 decide.py 通过后调用）"""
    tok = hashlib.sha256((str(_now()) + decision).encode()).hexdigest()[:16]
    rec = {"tok": tok, "ts": _now(), "decision": decision[:80], "by": "decide.py"}
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    json.dump(rec, open(TOKEN_FILE, "w", encoding="utf-8"), ensure_ascii=False)
    print("✅ 已发六问凭证: %s (5分钟有效)" % tok)
    print("   接下来 5 分钟内·写操作可用")
    return tok

def check():
    """看有没有有效凭证"""
    try:
        rec = json.load(open(TOKEN_FILE, encoding="utf-8"))
        age = _now() - float(rec.get("ts", 0))
        if age > TTL:
            return None, "凭证过期 %.0fs (TTL=%ds)" % (age, TTL)
        # ★ 2026-11-15 加(照本体"防一次过闸到处用"): 一次一用·用过即销
        if rec.get("used"):
            return None, "凭证已用(一次一用)"
        rec["used"] = True
        rec["used_at"] = _now()
        json.dump(rec, open(TOKEN_FILE, "w", encoding="utf-8"), ensure_ascii=False)
        return rec, ""
    except Exception as e:
        return None, "无凭证: %s" % str(e)[:40]

def require_decide(op, detail=""):
    """写操作前置硬拒（没有凭证就抛异常·落不了库）"""
    rec, why = check()
    if not rec:
        # 记 BLOCKED 账（本体要求：指标改数 BLOCKED 次数）
        try:
            import datetime
            with open("/opt/masterd-wudi/data/decide_blocked.jsonl", "a") as f:
                f.write(json.dumps({"ts": datetime.datetime.now().isoformat(timespec="seconds"),
                                    "op": op, "detail": detail[:100], "why": why}, ensure_ascii=False) + "\n")
        except Exception: pass
        raise PermissionError("BLOCKED: %s 未经 decide.py 六问 | %s" % (op, why))
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "pass":
        issue(" ".join(sys.argv[2:]) or "manual")
    elif len(sys.argv) > 1 and sys.argv[1] == "check":
        rec, why = check()
        print("有效:" if rec else "无效:", why or rec)
    else:
        print(__doc__)
