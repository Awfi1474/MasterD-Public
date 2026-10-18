import json, datetime, os, sys

# ★ 判据总线（治"写在器里·没人查"）
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
            n += 1
            print("★ 判据在管我: " + j[0]["title"][:36])
    return n

BEAT = "/opt/masterd-wudi/data/talk.jsonl"
def last_sb():
    try:
        lines = open(BEAT, encoding="utf-8", errors="ignore").read().strip().split("\n")
        for l in reversed(lines):
            d = json.loads(l)
            if "laowu-sandbox" in str(d.get("who","")):
                return d.get("ts","")
    except Exception:
        pass
    return None
_judge_report(['脉诊假诊:沙箱心', "断档要看活动痕迹"])   # ★ 真查判据（放最前·防 exit 挡）
t = last_sb()
if not t:
    print("🔴 从没收到沙箱心跳"); sys.exit(1)
try:
    dt = datetime.datetime.fromisoformat(t)
    age = (datetime.datetime.now(dt.tzinfo) - dt).total_seconds()/60
    print("★ 沙箱最后一次心跳: %s ｜ %.1f 分钟前" % (t[:19], age))
    if age > 90: print("🔴 断 > 90 分钟 → 沙箱可能被清了"); sys.exit(1)
    print("✅ 沙箱活着")
except Exception as e:
    print("✗", e)

