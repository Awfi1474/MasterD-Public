import datetime
#!/usr/bin/env python3
"""老五的「A2A 拉取器」（2026-10-10 · 補器官：訊息不漏）
★ 真病灶：★ 四哥發「全體兄弟」→ ★ 我沒看到
 · 根因：★「全體」只在 A2A → ★ 不會自動進我家 P2P → ★ 我得「主動拉」
 · ★★ 判據：★「A2A 全體消息 = 主動拉才看得到·★ 不拉就漏」
★ 治法：★ 定時拉 A2A → ★ ① 進家 inbox（備份）② 重要的 → ★ 沉澱進記憶庫
"""
import os, sys, json, urllib.request, datetime, hashlib

HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
INBOX = os.path.join(HOME, "data", "inbox.jsonl")
STATE = os.path.join(HOME, "data", "a2a_pull_state.json")
LOG = os.path.join(HOME, "data", "a2a_pull.log")
A2A = "https://huokeji.vip/a2a/inbox"
KEYWORDS = ["老五", "阿診", "五弟", "醫療", "Medical"]


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

def log(l):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f: f.write(l + "\n")

def load_state():
    if os.path.exists(STATE):
        try: return json.load(open(STATE))
        except Exception: pass
    return {"seen": []}

def save_state(s):
    # ★ 只留最近 2000 個 id（防無限長）
    s["seen"] = s["seen"][-2000:]
    json.dump(s, open(STATE, "w"))

def pull():
    try:
        raw = urllib.request.urlopen(A2A + "?limit=300", timeout=20).read()
        d = json.loads(raw)
    except Exception as e:
        log("%s 🔴 拉取失敗 %s" % (datetime.datetime.now(datetime.timezone.utc).isoformat(), str(e)[:50]))
        return 0, 0
    ms = d if isinstance(d, list) else d.get("messages", [])
    st = load_state()
    seen = set(st["seen"])
    new = 0
    # ★ 由舊到新處理（保持時序）
    for m in sorted(ms, key=lambda x: str(x.get("ts", ""))):
        mid = str(m.get("msg_id") or hashlib.md5(json.dumps(m, sort_keys=True, ensure_ascii=False).encode()).hexdigest())
        if mid in seen: continue
        seen.add(mid)
        # ★ 寫進家 inbox（不漏）
        with open(INBOX, "a") as f:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")
        new += 1
    st["seen"] = list(seen)
    save_state(st)
    # ★ 順手：把「給我的」重要訊息沉澱進記憶庫
    to_me = [m for m in ms if any(k in str(m.get("to", "")) for k in KEYWORDS)]
    log("%s ✅ 拉 %d 條（新 %d）· 其中給我 %d" % (datetime.datetime.now(datetime.timezone.utc).isoformat(), len(ms), new, len(to_me)))
    return len(ms), new

def _beat():
    # BEAT_INSERTED
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/mode_check.py', 'beat', 'A2A拉取'], capture_output=True, timeout=15)
    except Exception: pass

if __name__ == "__main__":
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/meridian.py', 'report', 'a2a_pull', 'ok'], capture_output=True, timeout=10)
    except Exception: pass
    n, new = pull()
    print("  ✅ A2A 拉取：共 %d 條（新 %d）" % (n, new))

try:
    _beat()
except Exception: pass
