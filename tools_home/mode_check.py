import datetime
#!/usr/bin/env python3
"""老五的「機制體檢」v2（2026-10-10）
★ v1 教訓：★ 靠「腳本自己調 beat」→ ★ 要改 10 個腳本·易錯（實測 9 個沒跳）
★ v2 改法：★ 心跳 = ★「日誌檔的 mtime」（★ 不用改腳本·★ 且更真：日誌沒更新=沒跑）
★ 判據（不變）：① 會跳 ② 產出對 ③ 自查崩 ④ 超時=孤島
"""
import os, sys, json, datetime, urllib.request

HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
TAB = os.path.join(HOME, "data", "mode_table.json")
LOG = os.path.join(HOME, "data", "mode_check.log")
A2A = "https://huokeji.vip/a2a/message"

def _aware(dt):
    """★ 統一 aware（naive 當 UTC）"""
    if dt is None: return None
    return dt.replace(tzinfo=datetime.timezone.utc) if dt.tzinfo is None else dt


# ★ 機制清單：名字 → (應週期分, 日誌檔, 是否核心)
MODES = {
    "記憶完整性":  (2,    "home_guard.log", True),
    "記憶庫":      (15,   "mem_guard.log", True),
    "判死反射":    (10,   "body_death.log", True),
    "循環守護":    (20,   "circulation.log", True),
    "喚醒驗":      (400,  "wake_verify.log", False),
    "數據對賬":    (1500, "custody_cron.log", False),
    "體檢接收":    (1500, "checkup_recv.log", False),
    "A2A拉取":     (15,   "a2a_pull.log", True),
    "通道體檢":     (10,   "channel_check.log", True),
    "網速監測":     (20,   "net_watch.log", True),
    "收即回執":     (40,   "recv_receipt_cron.log", True),
    "經絡傳導":     (20,   "meridian_cron.log", True),
    "公共流":       (25,   "pub_bus.log", True),
    "每日上報":    (1500, "daily_report.log", False),
    "量化驗證":    (800,  "quant_verify.log", False),
}

def now():
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

def check_mode(name, iv, logfile, core=False):
    """★ 看日誌 mtime → 判「跳了沒」"""
    p = os.path.join(HOME, "data", logfile)
    if not os.path.exists(p):
        return "🔴", None, "日誌不存在"
    idle = (now() - _aware(datetime.datetime.fromtimestamp(os.path.getmtime(p), datetime.timezone.utc))).total_seconds() / 60
    if idle <= iv * 1.5: st = "✅"
    elif idle <= iv * 3: st = "🟠"
    else: st = "🔴"
    return st, idle, ""

def status():
    rows = []
    for name, (iv, lf, core) in MODES.items():
        st, idle, err = check_mode(name, iv, lf, core)
        rows.append((name, st, ("%.0f分前" % idle) if idle is not None else "?", "應%d分" % iv, "【核心】" if core else "", err))
    return rows

def verify():
    bad = []
    for name, (iv, lf, core) in MODES.items():
        st, idle, err = check_mode(name, iv, lf, core)
        if st in ("🔴",) or err:
            bad.append("%s（%s）%s" % (name, err or "閒置 %.0f 分 > %d×3" % (idle, iv), "【核心】" if core else ""))
    st_file = os.path.join(HOME, "data", "mode_verify_state.json")
    try: s = json.load(open(st_file)) if os.path.exists(st_file) else {}
    except Exception: s = {}
    sig = "|".join(sorted(bad))
    if bad:
        if s.get("sig") == sig:
            log("%s 🔴 孤島（不重發）：%s" % (now().isoformat(), " | ".join(bad))); print("  🔴 孤島（已報過）"); return 1
        s["sig"] = sig; json.dump(s, open(st_file, "w"))
        log("%s 🔴 孤島：%s" % (now().isoformat(), " | ".join(bad)))
        notify("🔴 機制體檢：孤島（該跑沒跑）\n" + "\n".join("· " + b for b in bad) +
               "\n→ 判據：日誌沒更新 = 機制沒跑｜機制在 ≠ 機制在跑")
        return 1
    s["sig"] = None; json.dump(s, open(st_file, "w"))
    log("%s ✅ 機制全在跳（%d 個）" % (now().isoformat(), len(MODES)))
    print("  ✅ 機制全在跳（%d 個）" % len(MODES))
    return 0

if __name__ == "__main__":
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/meridian.py', 'report', 'mode_check', 'ok'], capture_output=True, timeout=10)
    except Exception: pass
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "verify":
        sys.exit(verify())
    else:
        print("=" * 70)
        print("  ★ 機制體檢 v2（判據：日誌沒更新 = 機制沒跑）")
        print("=" * 70)
        print("  %-14s %-4s %-10s %-9s %s" % ("機制", "態", "上次", "應週期", "備註"))
        print("  " + "-" * 62)
        for name, st, idle, iv, core, err in status():
            print("  %-14s %-4s %-10s %-9s %s%s" % (name, st, idle, iv, core, err[:24]))
