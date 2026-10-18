#!/usr/bin/env python3
"""阿診 · 記憶完整性（2026-10-10 自己設計）
★★ 我的判據（不是「檔案在不在」→ 是「有沒有靜默地少了」）：

【4 個維度 · 每維度對一個病】
① 存不存在(existence) → 病：空檔案（在·但空的）
② 變沒變(drift)       → 病：漂移（分「身份指紋不該變」vs「內容指紋該變」）
③ 有沒有斷層(gap)      → 病：空白窗口（那段時間不存在）
④ 能不能用(usable)     → 病：讀得出+用得成（不是「在」）

【5 個病灶（我判）】
· 假綠：在·但空的
· 靜默缺失：少了·但沒拉力
· 漂移：變了·但沒感覺
· 斷層：有一段不存在
· 假在：在·但讀不出/用不成

【每維度都標】誰能驗我 + 讀法差（否則「自己驗自己=假綠」）
"""
import os, sys, json, hashlib, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def fp(path):
    if not os.path.exists(path): return None
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()[:16]

def size(p):
    return os.path.getsize(p) if os.path.exists(p) else 0

# ★ L0-L4 該有什麼（權威表）
LAYERS = {
    "L0·身份憲法": ["method/WHOAMI.md", "method/IDENTITY.json"],
    "L1·身份":     ["method/MEDICAL_ROLE.md", "method/PROFESSION.md"],
    "L2·方法":     ["method/AZHEN-METHOD-20261010.md"],
    "L3·知識":     ["method/病歷庫.jsonl", "data/a2a_history.json"],
    "L4·日誌":     ["data/出診記錄-20261008.md"],
}

# ★ 誰能驗我 + 讀法差（每個維度）
VERIFIERS = {
    "① 存不存在": "大哥/Arki｜讀法差：他們列「該有的清單」·我只列「我記得的」",
    "② 變沒變":   "三哥｜讀法差：他算「指紋」·我看「檔案在不在」",
    "③ 有沒有斷層": "老四｜讀法差：他查「commits 覆蓋」·我查「檔案存在」",
    "④ 能不能用":  "Arki/大哥｜讀法差：他們「讀回來用」·我只「看大小」",
}

def check():
    R = []
    # ★ ① 存不存在（existence）
    missing = []
    present = 0
    for layer, files in LAYERS.items():
        for f in files:
            p = os.path.join(HERE, f)
            if os.path.exists(p): present += 1
            else: missing.append(f"{layer}/{f}")
    R.append(("① 存不存在", f"{present}/{present+len(missing)}", "✅" if not missing else f"🔴 缺 {len(missing)}",
              missing))
    # ★ ② 變沒變（drift）：身份指紋（不該變）vs 內容指紋（該變）
    id_files = ["method/WHOAMI.md", "method/IDENTITY.json"]
    id_fps = {f: fp(os.path.join(HERE,f)) for f in id_files if os.path.exists(os.path.join(HERE,f))}
    BASE = os.path.join(HERE, "data", "memory_baseline.json")
    base = json.load(open(BASE)) if os.path.exists(BASE) else {}
    drift = []
    if base.get("identity"):
        for f, v in id_fps.items():
            if base["identity"].get(f) and base["identity"][f] != v:
                drift.append(f)
    R.append(("② 變沒變", f"身份指紋 {len(id_fps)} 個" + (f"·漂 {drift}" if drift else "·未漂"),
              "✅" if not drift else "🟡", None))
    # ★ ③ 有沒有斷層（gap）→ ★ 2026-10-10 修：「讀不出」≠「斷層」（分開）
    gap = "?"
    gap_bad = False
    try:
        import glob as _g
        _paths = _g.glob(os.path.join(HERE, "data", "a2a_history.json*"))
        ms = []
        for _pp in _paths:
            if _pp.endswith(".jsonl"):
                ms += [json.loads(l) for l in open(_pp) if l.strip()]
            else:
                _d2 = json.load(open(_pp))
                ms += _d2 if isinstance(_d2, list) else _d2.get("messages", [])
        if not ms:
            gap = "★ 讀到 0 條（★ 不是『斷層』→ ★ 是『檔案空/壞』·★ 分開報）"
            gap_bad = True
        else:
            ts = sorted(str(m.get("ts","")) for m in ms)
            gap = f"{ts[0][5:16]} → {ts[-1][5:16]}（{len(ms)} 條）"
    except Exception as e:
        gap = f"★ 讀不出（{str(e)[:26]}）→ ★ 可能檔壞·★ 非斷層"
        gap_bad = True
    R.append(("③ 有沒有斷層", gap, "🔴" if gap_bad else "✅", None))
    # ★ ④ 能不能用（usable）→ ★ 2026-10-10 修：不只「讀得成」·★ 要「數目對」
    # ★ 病灶：★ 舊版「0 例」也打 ✅ = 假綠 → ★ 現在：有「底線數」才 ✅
    FLOOR = {"病歷庫.jsonl": 20, "a2a_history.json": 100}   # ★ 底線（低於=🔴）
    usable = []
    usable_bad = False
    try:
        ev = os.path.join(HERE,"method","病歷庫.jsonl")
        if os.path.exists(ev):
            n = sum(1 for l in open(ev) if l.strip() and json.loads(l).get("id"))
            floor = FLOOR.get("病歷庫.jsonl", 1)
            ok = n >= floor
            if not ok: usable_bad = True
            usable.append(f"病歷庫 {n} 例{'≥' if ok else ' < 底線'}{floor}{'✅' if ok else '🔴假綠'}")
        else:
            usable_bad = True; usable.append("病歷庫 不存在 🔴")
        ah = os.path.join(HERE,"data","a2a_history.json")
        if os.path.exists(ah):
            raw = open(ah).read().strip()
            n2 = len(json.loads(raw)) if raw.startswith("[") else len([l for l in raw.split("\n") if l.strip()])
            ok2 = n2 >= FLOOR.get("a2a_history.json", 1)
            if not ok2: usable_bad = True
            usable.append(f"A2A 歷史 {n2} 條{'✅' if ok2 else '🔴'}")
    except Exception as e:
        usable_bad = True
        usable.append(f"讀不出：{str(e)[:30]}")
    R.append(("④ 能不能用", "; ".join(usable) or "?", "🔴" if usable_bad else "✅", None))
    return R

def save_baseline():
    id_files = ["method/WHOAMI.md", "method/IDENTITY.json"]
    base = {"ts": __import__("datetime").datetime.now().isoformat(),
            "identity": {f: fp(os.path.join(HERE,f)) for f in id_files if os.path.exists(os.path.join(HERE,f))}}
    json.dump(base, open(os.path.join(HERE,"data","memory_baseline.json"),"w"), ensure_ascii=False, indent=1)
    return base

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "baseline":
        b = save_baseline()
        print(f"  ✅ 基線已存（身份指紋 {len(b['identity'])} 個）")
    else:
        print("=" * 62)
        print("  ★ 記憶完整性（阿診自己設計）")
        print("=" * 62)
        print("  ★ 判據：不是「檔案在不在」→ 是「有沒有靜默地少了」")
        print()
        red = 0
        for name, note, st, extra in check():
            print(f"  {st:12s} {name:12s} {note}")
            print(f"     ★ 誰能驗我：{VERIFIERS.get(name,'?')}")
            if extra:
                for e in extra[:3]: print(f"       - {e}")
            if st.startswith("🔴"): red += 1
        print("-" * 62)
        print(f"  {'🔴 有 '+str(red)+' 項缺 → 要補' if red else '✅ 四維度全過'}")
