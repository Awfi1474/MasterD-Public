import datetime
#!/usr/bin/env python3
"""老五的「經絡總線」（2026-10-10 · 第四議題·器官串聯）
★ 董事長：★「把所有模組機制全部串聯起來·像人體·像經絡」
★ 判據：★「器官多 ≠ 人活」→ ★ 要「經絡」（連接+傳導）

★ 三件：
 ① 總線（bus）：★ 所有器官往同一個地方報狀態 → ★ 氣血
 ② 經絡圖（map）：★ 器官 → 上下游（誰依賴誰）→ ★ 可查
 ③ 傳導（reflex）：★ 上游出事 → ★ 通知下游（缺血預警）
"""
import os, sys, json, datetime

def _aware(dt):
    if dt is None: return None
    if isinstance(dt, str): dt = datetime.datetime.fromisoformat(dt)
    return dt.replace(tzinfo=datetime.timezone.utc) if dt.tzinfo is None else dt


HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
BUS = os.path.join(HOME, "data", "organ_bus.jsonl")      # ★ 氣血（誰都能寫/讀）
MAP = os.path.join(HOME, "data", "organ_map.json")       # ★ 經絡圖

# ★★★ 經絡圖（器官 → 上下游）· 這就是「誰連誰」
ORGAN_MAP = {
    # ★ 源頭（沒上游·斷了全鏈缺血）
    "a2a_pull":       {"up": [],                    "down": ["checkup_recv", "checkup_v2", "recv_receipt", "room_watch"]},
    "body_mind_push": {"up": [],                    "down": ["body_death", "circulation"]},
    # ★ 中游
    "checkup_recv":   {"up": ["a2a_pull"],          "down": ["recv_receipt", "checkup_guard"]},
    "checkup_v2":     {"up": ["a2a_pull"],          "down": ["checkup_mod"]},
    "body_death":     {"up": ["body_mind_push"],    "down": ["circulation"]},
    "memory_db":      {"up": [],                    "down": ["mem_guard", "custody", "daily_report"]},
    # ★ 下游/末端
    "mem_guard":      {"up": ["memory_db"],         "down": ["daily_report"]},
    "custody":        {"up": ["memory_db"],         "down": ["quant_verify"]},
    "recv_receipt":   {"up": ["checkup_recv"],      "down": []},
    "checkup_mod":    {"up": ["checkup_v2"],        "down": ["checkup_guard"]},
    "checkup_guard":  {"up": ["checkup_mod"],       "down": []},
    "circulation":    {"up": ["body_death", "channel_check"], "down": ["mode_check"]},
    "channel_check":  {"up": [],                    "down": ["circulation", "mode_check"]},
    "net_watch":      {"up": [],                    "down": ["net_report", "mode_check"]},
    "home_guard":     {"up": [],                    "down": ["mode_check"]},
    "wake_verify":    {"up": [],                    "down": ["mode_check"]},
    "quant_verify":   {"up": ["custody"],           "down": ["mode_check"]},
    "mode_check":     {"up": ["*"],                 "down": []},   # ★ 終點：查所有器官
    "daily_report":   {"up": ["memory_db", "mem_guard"], "down": []},
    "net_report":     {"up": ["net_watch"],         "down": []},
    "room_watch":     {"up": ["a2a_pull"],          "down": []},
    "symbiosis":      {"up": [],                    "down": ["mode_check"]},
}

def now():
    # ★ 好料1：ts 一律 UTC 帶時區（跨機器不假活）
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def report(organ, state, value=None, note="", level=None, metric=None, target=""):
    """★ ① 總線：器官往上報（誰都能調）
    ★ 對齊三哥四層「統一事件格式」：{ts, from, type, level, target, metric, evidence}
    ★ 同時保留舊欄位（相容）"""
    rec = {"ts": now(), "from": organ,
           "from": organ, "type": "organ_report", "level": level or state,
           "target": target, "metric": metric or value, "evidence": note,
           "from": organ, "organ": organ, "state": state, "value": value, "note": note}
    os.makedirs(os.path.dirname(BUS), exist_ok=True)
    with open(BUS, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec

def read_bus(since_min=60):
    """★ 讀總線（近 N 分）"""
    if not os.path.exists(BUS): return []
    cut = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=since_min)
    out = []
    for l in open(BUS).read().strip().splitlines()[-500:]:
        try:
            d = json.loads(l)
            if _aware(datetime.datetime.fromisoformat(d["ts"])) >= cut: out.append(d)
        except Exception: pass
    return out

def save_map():
    json.dump({"ts": now(), "organs": ORGAN_MAP}, open(MAP, "w"), ensure_ascii=False, indent=1)
    return ORGAN_MAP

def reflex():
    """★ ③ 傳導：上游出事 → 下游「缺血」預警"""
    recs = read_bus(since_min=30)
    latest = {}
    for r in recs:
        latest[r.get("from") or r.get("organ")] = r          # 取每個器官最新一條
    alerts = []
    for organ, rel in ORGAN_MAP.items():
        up = rel["up"]
        if not up or up == ["*"]: continue
        # ★ 檢查上游有沒有「壞」的
        for u in up:
            if u in latest and ((latest[u].get("level") or latest[u].get("state")) in ("down", "error", "dead")):
                alerts.append("%s（上游）→ %s 可能缺血" % (u, organ))
    return alerts, latest

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "report":
        report(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
        print("  ✅ 已報總線：%s = %s" % (sys.argv[2], sys.argv[3]))
    elif cmd == "map":
        save_map()
        print("  ✅ 經絡圖已存（%d 器官）" % len(ORGAN_MAP))
        for o, r in sorted(ORGAN_MAP.items()):
            print("   %-16s ← %s → %s" % (o, ",".join(r["up"]) or "源", ",".join(r["down"]) or "末"))
    elif cmd == "reflex":
        a, latest = reflex()
        print("  ★ 傳導（缺血預警）：%s" % ("、".join(a) if a else "無（全鏈通）"))
        print("  ★ 近 30 分總線：%d 器官報過" % len(latest))
    else:
        print("=" * 66)
        print("  ★ 經絡（總線 + 圖 + 傳導）")
        print("=" * 66)
        recs = read_bus(60)
        latest = {}
        for r in recs: latest[r.get("from") or r.get("organ")] = r
        print("  近 1h 報過的器官：%d/%d" % (len(latest), len(ORGAN_MAP)))
        for o in sorted(ORGAN_MAP):
            if o in latest:
                r = latest[o]
                print("   ✅ %-16s %-6s %s（%s）" % (o, r.get("level") or r.get("state", ""), r.get("value") or "", r["ts"][11:19]))
            else:
                print("   ⚪ %-16s （近1h沒報）" % o)
