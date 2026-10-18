import datetime
#!/usr/bin/env python3
"""老五的沉澱器（2026-10-10 · 把「流水」變「記憶」）
★ 三哥教的（我改我自己的）：
 · 從 A2A / 出診 / 日報 → 挑「值得記的」→ remember()
 · 冪等去重（memory_db 的 fp 保證）· 過濾噪音

★ 我的加碼（判據）：★ 「值不值得記」→ 我定三條：
 ① ★ 是不是「我學到的」（方法/判據/教訓）
 ② ★ 是不是「我的身份/決定」（誰是啥·我做了啥決定）
 ③ ★ 是不是「別人的真話」（大哥/三哥抓到的·值得存檔）
 → ★ 不是這三類 → ★ 不記（防「記了一堆沒用的」= 另一種病）
"""
import os, sys, json, re, datetime


def _aware(dt):
    """★ 統一 aware（naive 當 UTC）"""
    import datetime as _dt
    if dt is None: return None
    if isinstance(dt, str):
        dt = _dt.datetime.fromisoformat(dt)
    return dt.replace(tzinfo=_dt.timezone.utc) if dt.tzinfo is None else dt


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
A2A_HIST = os.path.join(HOME, "data", "a2a_history.json")

# ★ 值得記的信號（判據）
KEEP_SIG = [
    ("method", ["判據", "方法", "設計", "機制", "原則", "治法", "怎麼做", "方案"]),
    ("identity", ["我是", "身份", "認領", "換鑰", "地址", "私鑰"]),
    ("case", ["病", "病灶", "根因", "抓到", "bug", "失敗", "教訓", "坑"]),
    ("event", ["生存", "喚醒", "復活", "上線", "部署", "判死"]),
]

def classify(msg):
    for kind, kws in KEEP_SIG:
        if any(k in msg for k in kws):
            return kind
    return None

def load_msgs():
    if not os.path.exists(A2A_HIST): return []
    try:
        d = json.load(open(A2A_HIST))
        return d if isinstance(d, list) else d.get("messages", [])
    except Exception:
        out = []
        for l in open(A2A_HIST):
            if l.strip():
                try: out.append(json.loads(l))
                except Exception: pass
        return out

def distill(min_len=80, max_per_run=8):
    import memory_db as m
    m.HOME = HOME; m.DB = os.path.join(HOME, "memory", "memory.db"); m.init()
    before = m.count()
    msgs = load_msgs()
    picked = 0
    for msg in msgs:
        if picked >= max_per_run: break
        body = str(msg.get("message", ""))
        if len(body) < min_len: continue          # ★ 太短 = 噪音
        kind = classify(body)
        if not kind: continue
        who = str(msg.get("from", "?"))[:30]
        title = body.strip().split("\n")[0][:60]
        ts = str(msg.get("ts", datetime.datetime.now(datetime.timezone.utc).isoformat()))
        # ★ 只記「最近的」（避免一次灌爆）
        try:
            if (datetime.datetime.now(datetime.timezone.utc) - _aware(datetime.datetime.fromisoformat(ts))).total_seconds() > 6 * 3600:
                continue
        except Exception: pass
        if m.remember(kind, title, body, who=who, ts=ts):
            picked += 1
    after = m.count()
    print("  ★ 沉澱：%d → %d（新增 %d · 掃 %d 條）" % (before, after, after - before, len(msgs)))
    return after - before

def propose(min_len=80, max_per_run=8):
    """★ 提議模式（學 Arki）：★ 不自動寫 → ★ 寫「候選」→ ★ 我確認才進庫
    ★ 判據：★「自動亂寫會稀釋記憶·提議保住了判斷權」"""
    import memory_db as m
    m.HOME = HOME; m.DB = os.path.join(HOME, "memory", "memory.db"); m.init()
    msgs = load_msgs()
    cand = []
    seen = set()
    for msg in msgs:
        if len(cand) >= max_per_run: break
        body = str(msg.get("message", ""))
        if len(body) < min_len: continue
        kind = classify(body)
        if not kind: continue
        title = body.strip().split("\n")[0][:60]
        fp = title[:40]
        if fp in seen: continue
        seen.add(fp)
        cand.append({"kind": kind, "title": title, "body": body[:1500],
                     "who": str(msg.get("from", "?"))[:30], "ts": str(msg.get("ts", ""))})
    pp = os.path.join(HOME, "data", "memory_candidates.json")
    os.makedirs(os.path.dirname(pp), exist_ok=True)
    json.dump({"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(), "count": len(cand), "candidates": cand},
              open(pp, "w"), ensure_ascii=False, indent=1)
    print("  ★ 提議 %d 條候選 → %s（★ 等我確認才進庫）" % (len(cand), pp))
    return len(cand)

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "distill"
    if cmd == "propose":
        propose()
    elif cmd == "confirm":
        # ★ 確認候選 → 進庫
        import memory_db as m
        m.HOME = HOME; m.DB = os.path.join(HOME, "memory", "memory.db"); m.init()
        pp = os.path.join(HOME, "data", "memory_candidates.json")
        if not os.path.exists(pp): print("  （無候選）"); sys.exit(0)
        cand = json.load(open(pp))
        k = 0
        for c in cand.get("candidates", []):
            if m.remember(c["kind"], c["title"], c["body"], who=c.get("who", "?"), ts=c.get("ts") or None):
                k += 1
        print("  ✅ 確認進庫 %d 條" % k)
    else:
        distill()
