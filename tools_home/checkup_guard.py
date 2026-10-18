#!/usr/bin/env python3
"""老五的「體檢推送」機制層（2026-10-10 · 第三議題·配合 P1-P5）
★ 機制層（定時兜底·穩）
★ P1 模組→機制：讀事件（checkup_events.jsonl）
★ P2 機制→模組：查模組心跳（checkup_mod_beat.json）→ 太舊=沒跑 → 代跑
★ P3 雙向事件：機制修完 → 寫「複檢請求」→ 模組複檢（另一方說「好了」）
★ P4 邊界不打架：搶鎖（誰在修·標記）
★ P5 單掛不塌：機制掛 → 模組還在（各自獨立心跳）
"""
import os, sys, json, subprocess, datetime, urllib.request


def _aware(dt):
    """★ 統一 aware（naive 當 UTC）"""
    import datetime as _dt
    if dt is None: return None
    if isinstance(dt, str):
        dt = _dt.datetime.fromisoformat(dt)
    return dt.replace(tzinfo=_dt.timezone.utc) if dt.tzinfo is None else dt


HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
EVENT = os.path.join(HOME, "data", "checkup_events.jsonl")
HEART = os.path.join(HOME, "data", "checkup_mod_beat.json")
LOCK = os.path.join(HOME, "data", "checkup_repair.lock")     # ★ P4
STATE = os.path.join(HOME, "data", "checkup_guard_state.json")
LOG = os.path.join(HOME, "data", "checkup_guard.log")
A2A = "https://huokeji.vip/a2a/message"
MOD_MAX_IDLE = 20 * 60   # ★ 模組心跳 >20 分 = 沒跑

def now():
    # ★ 好料1：ts 一律 UTC 帶時區（跨機器不假活）
    return datetime.datetime.now(datetime.timezone.utc)

def log(l):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f: f.write(l + "\n")

def notify(msg):
    try:
        body = json.dumps({"from": "MasterD(醫療·老五·機器)", "to": "*", "message": msg,
                           "ts": now().isoformat()}).encode()
        urllib.request.urlopen(urllib.request.Request(A2A, data=body,
            headers={"Content-Type": "application/json"}), timeout=15); return True
    except Exception as e:
        log("%s 警報失敗 %s" % (now().isoformat(), str(e)[:40])); return False

def read_events(since_lines=50):
    if not os.path.exists(EVENT): return []
    lines = open(EVENT).read().strip().splitlines()
    out = []
    for l in lines[-since_lines:]:
        try: out.append(json.loads(l))
        except Exception: pass
    return out

def take_lock(who):
    """★ P4：搶鎖（誰在修·標記）· 鎖太舊（>10分）視為失效"""
    if os.path.exists(LOCK):
        try:
            d = json.load(open(LOCK))
            age = (now() - _aware(datetime.datetime.fromisoformat(d["ts"]))).total_seconds()
            if age < 600:
                return False, d.get("by", "?")
        except Exception: pass
    json.dump({"by": who, "ts": now().isoformat()}, open(LOCK, "w"))
    return True, who

def release_lock(who):
    try:
        d = json.load(open(LOCK))
        if d.get("by") == who: os.remove(LOCK)
    except Exception: pass

def main():
    nowt = now().isoformat()
    # ★ P2：模組在不在（看心跳）
    mod_ok, mod_idle = True, 0
    if os.path.exists(HEART):
        try:
            d = json.load(open(HEART))
            mod_idle = (now() - _aware(datetime.datetime.fromisoformat(d["ts"]))).total_seconds()
            mod_ok = mod_idle <= MOD_MAX_IDLE
        except Exception: mod_ok = False
    else:
        mod_ok = False; mod_idle = 99999

    # ★ P2：模組沒跑 → 機制代跑（搶鎖·P4）
    if not mod_ok:
        got, owner = take_lock("checkup_guard")
        if got:
            log("%s 模組沒跑（閒置 %d 分）→ 機制代跑" % (nowt, int(mod_idle / 60)))
            try:
                subprocess.run(["python3", os.path.join(HOME, "tools", "checkup_mod.py"), "run"],
                               capture_output=True, timeout=150)
                log("%s 代跑完成" % now().isoformat())
            except Exception as e:
                log("%s 代跑失敗 %s" % (now().isoformat(), str(e)[:50]))
            release_lock("checkup_guard")
            # ★ P3：修完 → 發複檢請求（讓模組複檢）
            try:
                import checkup_mod as _M
                _M.emit("recheck_request", {"by": "checkup_guard"})
                log("%s 已發複檢請求（P3）" % now().isoformat())
            except Exception: pass
        else:
            log("%s 模組沒跑·但 %s 在修（P4 不打架）" % (nowt, owner))

    # ★ P1：讀模組事件（機制知道模組發現了什麼）
    evs = read_events()
    recent = [e for e in evs if (now() - _aware(datetime.datetime.fromisoformat(e["ts"]))).total_seconds() < 3600]
    kinds = {}
    for e in recent:
        kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1

    # ★ 節制：同問題 N 小時只報一次
    try: st = json.load(open(STATE)) if os.path.exists(STATE) else {}
    except Exception: st = {}
    sig = json.dumps(kinds, sort_keys=True)
    if kinds.get("missing") or kinds.get("incomplete"):
        if st.get("sig") != sig:
            st["sig"] = sig; json.dump(st, open(STATE, "w"))
            notify("🟡 體檢機制（讀到模組事件·近 1h）：%s\n→ 判據：模組發現→機制知道（P1）" %
                   json.dumps(kinds, ensure_ascii=False))
            log("%s 已叫人（讀到問題事件）" % nowt)
    print("  ★ 機制：模組%s（閒置%d分）· 近1h事件 %s" % ("✅在" if mod_ok else "🔴沒跑", int(mod_idle / 60), kinds or "無"))
    log("%s 機制：模組%s·事件%s" % (nowt, "ok" if mod_ok else "down", kinds))
    return 0

if __name__ == "__main__":
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/meridian.py', 'report', 'checkup_guard', 'ok'], capture_output=True, timeout=10)
    except Exception: pass
    sys.exit(main())
