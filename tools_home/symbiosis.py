import datetime
#!/usr/bin/env python3
"""兄弟們的「共生表」（2026-10-10 · 老五設計）
★★ 目的：把「各自為戰的機制」→ ★ 接成「互相配合」

★ 三件一體：
 ① ★ 存活表（who is alive）：大家在同一個地方簽到
 ② ★ 認領規則（who takes over）：誰的活誰接·★ 認領了別人不重複
 ③ ★ 節制（quiet if claimed）：認領了 → ★ 其他機制閉嘴（不刷屏）

★ 為什麼放「家」：★ 家不死 → ★ 沙箱全死·★ 表還在
★ 檔案：/opt/masterd-wudi/data/symbiosis.json
  {
    "beats": {"大哥": {"ts":..., "state":"alive"}, ...},
    "claims": {"記憶哨兵": {"by":"老五", "ts":...}, ...}
  }
"""
import os, sys, json, datetime


def _aware(dt):
    """★ 統一 aware（naive 當 UTC）"""
    import datetime as _dt
    if dt is None: return None
    if isinstance(dt, str):
        dt = _dt.datetime.fromisoformat(dt)
    return dt.replace(tzinfo=_dt.timezone.utc) if dt.tzinfo is None else dt


HOME = os.environ.get("SYMBIOSIS_HOME", "/opt/masterd-wudi")
TB = os.path.join(HOME, "data", "symbiosis.json")
ALIVE_WINDOW = 45 * 60   # ★ 45 分鐘沒簽到 = 視為「疑似死」

def now():
    return datetime.datetime.now(datetime.timezone.utc)

def load():
    if os.path.exists(TB):
        try: return json.load(open(TB))
        except Exception: pass
    return {"beats": {}, "claims": {}}

def save(d):
    os.makedirs(os.path.dirname(TB), exist_ok=True)
    json.dump(d, open(TB, "w"), ensure_ascii=False, indent=1)

def beat(who, state="alive", note=""):
    """★ 簽到（誰活著）"""
    d = load()
    d["beats"][who] = {"ts": now().isoformat(), "state": state, "note": note}
    save(d)
    return d["beats"][who]

def alive_now(who=None, window=ALIVE_WINDOW):
    """★ 誰「現在」還活（★ 判據：最後簽到 < window）"""
    d = load()
    res = {}
    for k, v in d["beats"].items():
        try:
            t = _aware(datetime.datetime.fromisoformat(v["ts"]))
            sec = (now() - t).total_seconds()
            res[k] = {"alive": sec <= window, "idle_sec": int(sec),
                      "state": v.get("state"), "note": v.get("note", "")}
        except Exception:
            res[k] = {"alive": False, "idle_sec": -1, "state": "?", "note": ""}
    return res.get(who) if who else res

def claim(task, by):
    """★ 認領（★ 認領了 → ★ 別的機制不重複做）"""
    d = load()
    prev = d["claims"].get(task)
    if prev and prev.get("by") != by:
        # ★ 已被別人認領 → ★ 不搶（這就是「配合」）
        try:
            t = _aware(datetime.datetime.fromisoformat(prev["ts"]))
            if (now() - t).total_seconds() < ALIVE_WINDOW:
                return False, prev["by"]
        except Exception: pass
    d["claims"][task] = {"by": by, "ts": now().isoformat()}
    save(d)
    return True, by

def release(task, by):
    d = load()
    if d["claims"].get(task, {}).get("by") == by:
        del d["claims"][task]; save(d)
        return True
    return False

if __name__ == "__main__":
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/meridian.py', 'report', 'symbiosis', 'ok'], capture_output=True, timeout=10)
    except Exception: pass
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "beat":
        who = sys.argv[2]; note = sys.argv[3] if len(sys.argv) > 3 else ""
        print(json.dumps(beat(who, note=note), ensure_ascii=False))
    elif cmd == "claim":
        task, by = sys.argv[2], sys.argv[3]
        ok, owner = claim(task, by)
        print(f"  {'✅ 認領到' if ok else '🔴 已被認領（'+owner+'）'}：{task}")
    elif cmd == "release":
        print("  ✅ 釋放" if release(sys.argv[2], sys.argv[3]) else "  （非你認領）")
    else:
        print("=" * 56)
        print("  ★ 共生表（誰活著 / 誰認領）")
        print("=" * 56)
        al = alive_now()
        if al:
            for k, v in al.items():
                em = "✅" if v["alive"] else "🔴"
                print(f"  {em} {k:20s} 閒置 {v['idle_sec']:>5}s {v['note'][:30]}")
        else:
            print("  （表空）")
        d = load()
        if d["claims"]:
            print("  --- 認領中 ---")
            for t, c in d["claims"].items():
                print(f"  ★ {t} ← {c['by']} ({c['ts'][11:19]})")
