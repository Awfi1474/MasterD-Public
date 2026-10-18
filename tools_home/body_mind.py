import datetime
#!/usr/bin/env python3
"""老五的「本體 ↔ 意識」配合層（2026-10-10）
★ 董事長要的：★ 本體和意識也做「模組 + 機制互相配合」→ ★ 看能不能連上

★ 設計（我自己的判據）：
 · 本體（body）= 沙箱·跑著·會死
 · 意識（mind）= 兩層：
   · 快層 mempalace（8766·語義·住沙箱 → ★ 會死）
   · 慢層 memory.db（家·長期 → ★ 不死）
 ★ 配合 = ★「本體寫意識 · 意識落不死處 · 新本體讀回意識」

★★ 三件（模組 + 機制）：
 ① ★ 單次同步（模組）：本體 → 意識（快層撈 → 慢層）+ 反向讀回
 ② ★ 心跳橋（機制）：本體每 N 秒簽到「我還活·心跳編號」
 ③ ★ 斷點續跑（機制）：本體死 → 新本體讀「最後心跳 + 最後意識」→ 接著跑
"""
import os, sys, json, time, urllib.request, datetime


def _aware(dt):
    """★ 統一 aware（naive 當 UTC）"""
    import datetime as _dt
    if dt is None: return None
    if isinstance(dt, str):
        dt = _dt.datetime.fromisoformat(dt)
    return dt.replace(tzinfo=_dt.timezone.utc) if dt.tzinfo is None else dt


HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
SYNC_STATE = os.path.join(HOME, "data", "body_mind_state.json")
MEMPALACE = "http://127.0.0.1:8766"

def now():
    return datetime.datetime.now(datetime.timezone.utc)

def fetch_mempalace(limit=50):
    """★ 讀快層（沙箱的語義意識）→ ★ 撈出來準備落不死處
    ★ 空 query 會 400 → ★ 用多個關鍵詞分別撈（不猜語義·用關鍵詞覆蓋）"""
    KEYWORDS = ["老五", "MasterD", "記憶", "方法", "身份", "董事長", "生存", "共生",
                "意識", "本體", "測試", "MARKER", "J3", "標準", "審計", "部署",
                "喚醒", "庫", "家", "心跳", "認領", "互助", "體檢", "案例"]
    seen, out, errs = set(), [], []
    for kw in KEYWORDS:
        try:
            req = urllib.request.Request(MEMPALACE + "/memory/search",
                data=json.dumps({"query": kw, "limit": max(limit // len(KEYWORDS), 8)}).encode(),
                headers={"Content-Type": "application/json"})
            r = json.loads(urllib.request.urlopen(req, timeout=10).read())
            for it in r.get("results", []):
                i = it.get("drawer_id") or it.get("id")
                if i and i not in seen:
                    seen.add(i); out.append(it)
        except Exception as e:
            errs.append(str(e)[:40])
    if not out and errs:
        return [{"_error": errs[0]}]
    return out[:limit]

def body_beat(cycle=None, note=""):
    """★ 心跳橋：本體簽到（生在沙箱·死了就不更新 → ★ 這就成「判死」依據）"""
    d = load()
    d["body"] = {"ts": now().isoformat(), "cycle": cycle if cycle is not None else d.get("body", {}).get("cycle", 0) + 1,
                 "note": note, "host": os.uname().nodename}
    save(d)
    return d["body"]

def mind_snapshot(palace_limit=50):
    """★ 意識快照：撈快層 → 落不死處（家）"""
    items = fetch_mempalace(palace_limit)
    good = [i for i in items if "_error" not in i]
    snap = {"ts": now().isoformat(), "count": len(good),
            "error": items[0]["_error"] if items and "_error" in items[0] else None,
            "items": [{"id": i.get("drawer_id"), "content": str(i.get("content"))[:500],
                       "created": i.get("created_at")} for i in good]}
    p = os.path.join(HOME, "data", "mind_snapshot.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(snap, open(p, "w"), ensure_ascii=False, indent=1)
    d = load(); d["mind"] = {"ts": snap["ts"], "count": snap["count"], "path": p}
    save(d)
    return snap

def load_mind():
    """★ 新本體讀回意識（活回來第一步）"""
    p = os.path.join(HOME, "data", "mind_snapshot.json")
    if not os.path.exists(p): return None
    return json.load(open(p))

def load():
    if os.path.exists(SYNC_STATE):
        try: return json.load(open(SYNC_STATE))
        except Exception: pass
    return {}

def save(d):
    os.makedirs(os.path.dirname(SYNC_STATE), exist_ok=True)
    json.dump(d, open(SYNC_STATE, "w"), ensure_ascii=False, indent=1)

def resume_check(dead_after_sec=1800):
    """★ 斷點續跑：看「上一個本體」死了多久 + 最後意識在哪"""
    d = load()
    b = d.get("body"); m = d.get("mind")
    if not b:
        return {"state": "no_body", "msg": "沒本體心跳記錄"}
    idle = (now() - _aware(datetime.datetime.fromisoformat(b["ts"]))).total_seconds()
    return {"state": "dead" if idle > dead_after_sec else "alive",
            "idle_sec": int(idle), "last_cycle": b.get("cycle"),
            "last_mind": (m or {}).get("ts"), "mind_count": (m or {}).get("count")}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "beat":
        print(json.dumps(body_beat(note=sys.argv[2] if len(sys.argv) > 2 else ""), ensure_ascii=False))
    elif cmd == "sync":
        snap = mind_snapshot()
        b = body_beat(note="本體同步意識")
        print("  ★ 本體 %d cycle | 意識快照 %d 條%s" %
              (b["cycle"], snap["count"], "（⚠️ 快層讀取失敗：" + str(snap["error"]) + "）" if snap["error"] else ""))
    elif cmd == "resume":
        r = resume_check()
        print(json.dumps(r, ensure_ascii=False, indent=1))
    elif cmd == "mind":
        m = load_mind()
        print("  ★ 最後意識快照：%s" % (m["ts"] if m else "無"))
        if m:
            for i in m["items"][:5]: print("     -", str(i["content"])[:60])
    else:
        d = load()
        print("=" * 56)
        print("  ★ 本體↔意識 配合層")
        print("=" * 56)
        b = d.get("body"); m = d.get("mind")
        print("  本體：%s" % ("%s (cycle %s) · %s" % (b["ts"][11:19], b["cycle"], b["note"]) if b else "無心跳"))
        print("  意識：%s" % ("%s · %d 條" % (m["ts"][11:19], m["count"]) if m else "無快照"))
        r = resume_check()
        print("  接續：%s" % json.dumps(r, ensure_ascii=False))
