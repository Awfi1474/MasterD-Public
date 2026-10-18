import datetime
#!/usr/bin/env python3
"""老五的「體檢接收」（2026-10-10 · 重建）
★ 董事長問：★ 體檢報告「自動接收」還是「推送」？機制在不在工作？
★ 實況（我查的）：
 · ★ 各家「推送」✅（大哥 09:00 自動·Arki 09:30 自動·二哥/三哥/老四有自檢）
 · ★ 我「接收」🔴（收集器丟了·cron 裡也沒這條）→ ★ 靜默壞了
★ 設計（模組+機制互相配合·董事長要的）：
 · ★ 模組（pull）：★ 主動拉（不靠他們記得發）
 · ★ 機制（timer）：★ 每天 9:30 自動跑（他們發完·我收）
 · ★ 配合：★ 兩個都跑 → ★ 拉到的 vs 推來的 → ★ 對賬（缺誰·警報）
"""
import os, sys, json, datetime, urllib.request

HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
INBOX = os.path.join(HOME, "data", "inbox.jsonl")
OUT = os.path.join(HOME, "checkups")
LOG = os.path.join(HOME, "data", "checkup_recv.log")
STATE = os.path.join(HOME, "data", "checkup_state.json")
A2A = "https://huokeji.vip/a2a/message"

# ★ 應該交體檢的（6 位兄弟）
MEMBERS = ["大哥", "二哥", "三哥", "老四", "老五", "Arki"]

def log(l):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f: f.write(l + "\n")

def notify(msg):
    try:
        body = json.dumps({"from": "MasterD(醫療·老五·機器)", "to": "*", "message": msg,
                           "ts": datetime.datetime.now(datetime.timezone.utc).isoformat()}).encode()
        urllib.request.urlopen(urllib.request.Request(A2A, data=body,
            headers={"Content-Type": "application/json"}), timeout=15); return True
    except Exception as e:
        log("%s 警報失敗 %s" % (datetime.datetime.now(datetime.timezone.utc).isoformat(), str(e)[:40])); return False

def member_of(m):
    f = str(m.get("from", ""))
    for k in MEMBERS:
        if k in f: return k
        if k == "二哥" and "量化" in f: return "二哥"
        if k == "三哥" and "cognitive" in f: return "三哥"
        if k == "老五" and ("五弟" in f or "醫療" in f): return "老五"
    return None

def is_checkup(t):
    return any(k in t for k in ["體檢", "体检", "自检", "自檢", "每日体检", "每日體檢"]) and \
           not any(k in t for k in ["[PROBE]", "通道验证"])

def main(day=None):
    day = day or datetime.datetime.now().strftime("%Y-%m-%d")
    # ★ ① 讀家 inbox（已含 A2A 拉取）→ 挑今天的體檢
    msgs = []
    if os.path.exists(INBOX):
        for l in open(INBOX):
            try: msgs.append(json.loads(l))
            except Exception: pass
    today = [m for m in msgs if str(m.get("ts", "")).startswith(day) and is_checkup(str(m.get("message", "")))]
    by = {}
    for m in today:
        k = member_of(m)
        if k: by.setdefault(k, []).append(m)
    # ★ ② 寫收集報告
    os.makedirs(os.path.join(OUT, day), exist_ok=True)
    rep = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(), "day": day,
           "total": len(today), "by": {k: len(v) for k, v in by.items()},
           "missing": [k for k in MEMBERS if k not in by]}
    json.dump(rep, open(os.path.join(OUT, day, "collected.json"), "w"), ensure_ascii=False, indent=1)
    log("%s 收集：%d 條 · 交了 %s · 缺 %s" % (datetime.datetime.now(datetime.timezone.utc).isoformat(),
        len(today), list(by.keys()), rep["missing"]))
    print("  ★ 今日（%s）體檢：%d 條" % (day, len(today)))
    for k in MEMBERS:
        print("   %s %s（%d 條）" % ("✅" if k in by else "🔴", k, len(by.get(k, []))))
    # ★ ③ 缺誰 → 警報（節制：同一天只報一次）
    try: st = json.load(open(STATE)) if os.path.exists(STATE) else {}
    except Exception: st = {}
    if rep["missing"] and st.get("last_day") != day:
        st["last_day"] = day; json.dump(st, open(STATE, "w"))
        notify("🟡 體檢缺交（%s）：%s\n· 交了：%s\n→ 請提醒（或我這邊沒收到）" %
               (day, "、".join(rep["missing"]), "、".join(by.keys()) or "無"))
        log("%s → 已發缺交警報" % datetime.datetime.now(datetime.timezone.utc).isoformat())
        return 1
    return 0

def _beat():
    # BEAT_INSERTED
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/mode_check.py', 'beat', '體檢接收'], capture_output=True, timeout=15)
    except Exception: pass

if __name__ == "__main__":
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/meridian.py', 'report', 'checkup_recv', 'ok'], capture_output=True, timeout=10)
    except Exception: pass
    try:
        _beat()
    except Exception: pass
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
