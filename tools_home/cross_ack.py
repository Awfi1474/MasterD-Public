#!/usr/bin/env python3
"""老五的「交叉心跳·回寫」（2026-10-10）
★ 真交叉 = 「A 寫 → B 讀 → B 回寫 → A 讀」
★ 這支：★ 讀別人的心跳 → 回寫一條「我看到了（ts）」→ 雙方都能查「誰看過我」
★ 判據：★「自跳=我還在｜交叉=你看我·我看你（互證）」
"""
import os, sys, json, datetime
HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
ACK = os.path.join(HOME, "data", "cross_ack.json")

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def ack(target, viewer, their_ts):
    """★ 回寫：viewer 看到 target 的心跳（ts）"""
    d = {}
    if os.path.exists(ACK):
        try: d = json.load(open(ACK))
        except Exception: d = {}
    d.setdefault(target, []).append({"viewer": viewer, "seen_ts": their_ts, "at": now()})
    d[target] = d[target][-20:]
    json.dump(d, open(ACK, "w"), ensure_ascii=False, indent=1)
    return d[target][-1]

def who_saw(target):
    """★ 查：誰看過 target 的心跳"""
    if not os.path.exists(ACK): return []
    try: return json.load(open(ACK)).get(target, [])
    except Exception as _e: print("WARN db-read-fail:", _e); return []

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "show"
    if cmd == "ack":
        r = ack(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "")
        print("  ✅ 回寫：%s 看過 %s" % (sys.argv[3], sys.argv[2]))
    elif cmd == "who":
        for x in who_saw(sys.argv[2])[-3:]:
            print("   %s 看過（%s）" % (x["viewer"], x["at"][11:19]))
    else:
        if os.path.exists(ACK):
            d = json.load(open(ACK))
            for k, v in d.items():
                print("  %s：被看過 %d 次·最後 %s" % (k, len(v), v[-1]["viewer"] if v else "?"))
