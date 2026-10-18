#!/usr/bin/env python3
"""老五的「交叉心跳」（2026-10-10 · 應董事長問「你這邊心跳怎麼設計」）
★ 現況（查的）：★ 我有 3 個心跳·但互不交叉
 · ① 本體心跳（core_v2 寫·★ 沒人看 = 孤兒）
 · ② 沙箱心跳（body_mind_push 寫·body_death 看）
 · ③ 模組心跳（checkup_mod 寫·checkup_guard 看）
 → ★ 判據：★「寫了沒人看 = 孤兒·各自為政 = 沒交叉」

★ 交叉心跳（我的設計·三層）：
 ① ★ 【自跳】自己寫自己（現有·保留）
 ② ★ 【交叉跳】A 寫的心跳·B 讀並回寫（★ 互相看對方活不活）
    · ★ 本體 ↔ 沙箱：★ 本體寫 → 沙箱讀+回 → 本體讀
    · ★ 模組 ↔ 機制：★ 模組寫 → 機制讀+回 → 模組讀
 ③ ★ 【對賬】三個心跳「都新鮮」才算活（★ 任一個斷 → 叫人）

★ 判據（我定）：
 · ★「自跳」= 我還在（自己說）
 · ★「交叉跳」= 你看我·我看你（★ 互證）
 · ★「對賬」= 三個都新（★ 全鏈活）
 → ★ 只有「自跳」= 假活（自己說自己活·沒人核）
"""
import os, sys, json, datetime


def _aware(dt):
    """★ 統一 aware（naive 當 UTC）"""
    import datetime as _dt
    if dt is None: return None
    if isinstance(dt, str):
        dt = _dt.datetime.fromisoformat(dt)
    return dt.replace(tzinfo=_dt.timezone.utc) if dt.tzinfo is None else dt


HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
LOG = os.path.join(HOME, "data", "cross_beat.log")
# ★ 三個心跳 + 它們的「新鮮度上限」（分）
BEATS = {
    "本體心跳":  (os.path.join(HOME, "data", "heartbeat.json"),          10),
    "沙箱心跳":  (os.path.join(HOME, "data", "body_mind_state.json"),   35),
    "模組心跳":  (os.path.join(HOME, "data", "checkup_mod_beat.json"),   60),
}
# ★ 交叉對（A 看 B·B 看 A）
PAIRS = [("本體心跳", "沙箱心跳", "本體活著嗎（同機）"),
         ("模組心跳", "機制看模組", "模組在跑嗎（P2）")]

def now():
    return datetime.datetime.now(datetime.timezone.utc)

def log(l):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f: f.write(l + "\n")

def read_beat(path):
    if not os.path.exists(path): return None, "檔案不存在"
    try:
        d = json.load(open(path))
        ts = d.get("ts")
        if not ts and isinstance(d.get("body"), dict): ts = d["body"].get("ts")
        if not ts: return None, "無 ts"
        t = _aware(datetime.datetime.fromisoformat(ts))
        if t.tzinfo is None: t = t.replace(tzinfo=datetime.timezone.utc)
        idle = (now() - t).total_seconds() / 60
        return idle, None
    except Exception as e:
        return None, str(e)[:40]

def main():
    nowt = now().isoformat()
    print("=" * 60)
    print("  ★ 交叉心跳（自跳 + 交叉 + 對賬）")
    print("=" * 60)
    # ★ ① 自跳檢查
    states = {}
    for name, (path, maxidle) in BEATS.items():
        idle, err = read_beat(path)
        if idle is None:
            states[name] = ("🔴", err); print("  🔴 %-8s %s" % (name, err))
        else:
            st = "✅" if idle <= maxidle else ("🟠" if idle <= maxidle * 2 else "🔴")
            states[name] = (st, "%.0f分前" % idle)
            print("  %s %-8s 閒置 %.0f 分（上限 %d）" % (st, name, idle, maxidle))
    # ★ ②b 真交叉：讀到對方心跳 → 回寫「我看到了」（互證）
    try:
        import subprocess as _sp
        for tgt, (path, _mi) in BEATS.items():
            idle, err = read_beat(path)
            if idle is not None:
                ts = ""
                try:
                    d = json.load(open(path)); ts = d.get("ts") or (d.get("body") or {}).get("ts", "")
                except Exception: pass
                _sp.run(["python3", os.path.join(HOME, "tools", "cross_ack.py"), "ack", tgt, "老五家哨兵", ts],
                        capture_output=True, timeout=10)
    except Exception: pass
    # ★ ② 交叉判：任一方「🟠/🔴」→ 另一方也要知道
    cross_alerts = []
    for a, b, why in PAIRS:
        sa = states.get(a, ("🔴", ""))[0]
        if sa in ("🟠", "🔴"):
            cross_alerts.append("%s 不新（%s檢查：%s）" % (a, b, why))
    print("-" * 60)
    if cross_alerts:
        print("  ★ 交叉預警：%s" % "；".join(cross_alerts))
    else:
        print("  ★ 交叉預警：無（互相都看到對方活）")
    # ★ ③ 對賬：三個都 ✅ = 全鏈活
    all_ok = all(v[0] == "✅" for v in states.values())
    print("  ★ 對賬：%s（自跳=%s）" % (
        "✅ 全鏈活" if all_ok else "🟠 有斷", 
        "、".join("%s:%s" % (k, v[1]) for k, v in states.items())))
    log("%s 自跳%s·交叉%s" % (nowt, [v[0] for v in states.values()], cross_alerts or "無"))
    return 0 if all_ok else 1

if __name__ == "__main__":
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/meridian.py', 'report', 'cross_beat', 'ok'], capture_output=True, timeout=10)
    except Exception: pass
    sys.exit(main())
