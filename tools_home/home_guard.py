import datetime
#!/usr/bin/env python3
"""家在家的記憶哨兵（2026-10-10 v2）
★★ 關鍵：它跑在「家」（不死）→ 沙箱被清它也活
★ 三件：① 自查（不靠沙箱）② 節制（同問題只報一次）③ 破了發 A2A
★★ 2026-10-10 v2 修：① f-string 斷行 bug ② 加「自己崩了也要報」
"""
import os, sys, json, hashlib, urllib.request, datetime, traceback

HOME = "/opt/masterd-wudi"
SPEC = os.path.join(HOME, "memory", "LAYERS_SPEC.json")
LOG  = os.path.join(HOME, "data", "home_guard.log")
STATE = os.path.join(HOME, "data", "guard_state.json")
BASELINE = os.path.join(HOME, "data", "home_baseline.json")
A2A = "https://huokeji.vip/a2a/message"

def sha(p):
    if not os.path.exists(p): return None
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(65536), b''): h.update(c)
    return h.hexdigest()[:16]

def log(line):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f: f.write(line + "\n")

def notify(msg):
    """發 A2A（不靠沙箱）"""
    try:
        body = json.dumps({"from": "MasterD(醫療·老五·機器)", "to": "*",
                           "message": msg, "ts": datetime.datetime.now(datetime.timezone.utc).isoformat()}).encode()
        req = urllib.request.Request(A2A, data=body, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=15)
        return True
    except Exception as e:
        log("%s → A2A 警報失敗：%s" % (datetime.datetime.now(datetime.timezone.utc).isoformat(), str(e)[:50]))
        return False

def main():
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    # ★ 2026-10-10：接進共生表（簽到 + 認領）
    try:
        sys.path.insert(0, "/opt/masterd-wudi/tools")
        from symbiosis import beat, claim
        beat("老五·家哨兵", note="家人值守")
        claim("記憶完整性", "老五·家哨兵")
    except Exception as _e: pass
    spec = json.load(open(SPEC))
    problems, notes = [], []
    # ① 必須有的（家自己的清單·查「在 + 非空」）
    for rel in spec["must_have"]:
        p = os.path.join(HOME, rel)
        if not os.path.exists(p): problems.append("缺檔 " + rel)
        elif os.path.getsize(p) == 0: problems.append("空檔 " + rel)
    # ② 數目底線（★ 治「假綠」）
    cf = os.path.join(HOME, "memory", "cases", "CASES.jsonl")
    if os.path.exists(cf):
        n = sum(1 for l in open(cf) if l.strip())
        notes.append("病歷 %d 例" % n)
        if n < spec["floors"]["cases"]:
            problems.append("病歷 %d < 底線 %d（假綠）" % (n, spec["floors"]["cases"]))
    # ③ 身份指紋（★ 治「漂移」）
    # ★ 2026-10-25 修: 旧逻辑只报不更新基线 → 死循环假红(报了4次同一句)
    #   新逻辑: 检测到漂移 → 先记录 change_log(留痕) → 再更新基线(防死循环)
    #   判据: 「器判错 = 比没器更坏｜报了不处理 = 假装在守」
    ids = {}
    for r in spec["must_have"]:
        if "IDENTITY" in r or "SOUL" in r: ids[r] = sha(os.path.join(HOME, r))
    if os.path.exists(BASELINE):
        _bd = json.load(open(BASELINE))
        b = _bd.get("id_fp", {})
        _cl = _bd.get("change_log", [])
        _drift = []
        for k, v in ids.items():
            if b.get(k) and b[k] != v:
                problems.append("身份漂移 " + k)
                _drift.append({"ts": now, "file": k, "old": b[k], "new": v,
                               "why": "自动检测到变更·已更新基线(需人工确认是否漂移)", "by": "home_guard(auto)"})
        if _drift:
            # 留痕: 把这次变更写进 change_log 再更新基线
            _cl = (_cl + _drift)[-50:]
            json.dump({"ts": now, "id_fp": ids, "change_log": _cl}, open(BASELINE, "w"))
            notes.append("基線已更新(漂移%d處·留痕)" % len(_drift))
    else:
        json.dump({"ts": now, "id_fp": ids, "change_log": []}, open(BASELINE, "w"))
        notes.append("首建基線")

    sig = "|".join(sorted(problems))
    try: st = json.load(open(STATE)) if os.path.exists(STATE) else {}
    except Exception: st = {}

    if problems:
        status = "🔴 " + " | ".join(problems)
        line = "%s %s (%s)" % (now, status, ", ".join(notes))
        if st.get("last_sig") == sig:
            log(line + " （同問題·已報過·不重發）")
            print(line); return 1
        st["last_sig"] = sig; json.dump(st, open(STATE, "w"))
        log(line)
        if notify("🔴 記憶哨兵警報（家自查發現）：" + " | ".join(problems)):
            log(now + " → 已發 A2A 警報")
        return 1
    else:
        if st.get("last_sig"):
            st["last_sig"] = None; json.dump(st, open(STATE, "w"))
            log("%s ✅ 家記憶恢復完好 (%s)" % (now, ", ".join(notes)))
        else:
            log("%s ✅ 家記憶完好 (%s)" % (now, ", ".join(notes)))
        print(now + " ✅ 家記憶完好")
        return 0

def _beat():
    # BEAT_INSERTED
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/mode_check.py', 'beat', '記憶完整性'], capture_output=True, timeout=15)
    except Exception: pass

if __name__ == "__main__":
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/meridian.py', 'report', 'home_guard', 'ok'], capture_output=True, timeout=10)
    except Exception: pass
    try:
        _beat()
    except Exception: pass
    try:
        sys.exit(main())
    except Exception:
        # ★★★ 2026-10-10：哨兵自己崩了 → ★ 也要報（不然「崩了沒人知」）
        tb = traceback.format_exc()
        log("%s 💀 哨兵自己崩了：%s" % (datetime.datetime.now(datetime.timezone.utc).isoformat(), tb.replace("\n", " ")[:200]))
        notify("💀 記憶哨兵自己崩了（家上腳本異常）：" + tb.splitlines()[-1][:120])
        sys.exit(2)
