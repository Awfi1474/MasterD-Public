#!/usr/bin/env python3
"""家的「判死反射」v3（2026-10-10 · 接判死標準 v2 C1-C6）
★ 大哥通知：三哥定稿 C1-C6 通過審核 → 老五「先只讀探 /health」

★ C1 只讀探活：探活不驅動被探對象（不跑器官·只讀）
★ C2 寫心跳的只有心跳：獨立時鐘·探活只讀
★ C3 三源交叉：心跳時間戳 + 進程 + 端口
★ C4 分層 TTL：事件 20min→「心跳停」｜檔案/進程 40min→「模組疑死」｜全超 60min→「判死」
★ C5 冷卻：同狀態 N 小時只報一次
★ C6 探針自檢：探活自己失敗 → 報「探活失敗」（不當成「死」）
"""
import os, sys, json, datetime, subprocess, urllib.request

def _aware(dt):
    if dt is None: return None
    return dt.replace(tzinfo=datetime.timezone.utc) if dt.tzinfo is None else dt

HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
STATE = os.path.join(HOME, "data", "body_mind_state.json")
LOG = os.path.join(HOME, "data", "body_death.log")
GUARD = os.path.join(HOME, "data", "body_death_state.json")
A2A = "https://huokeji.vip/a2a/message"
CORE = "http://127.0.0.1:28430/health?from=laowu-self"
# ★ C4 分層 TTL（分鐘）
T1, T2, T3 = 20, 40, 60
COOLDOWN = 6 * 3600   # C5

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
        log("%s → 警報失敗 %s" % (datetime.datetime.now(datetime.timezone.utc).isoformat(), str(e)[:40])); return False

def probe():
    """★ C1 只讀 + C6 探針自檢：只讀 /health → (達?, 通?, 錯)"""
    try:
        r = urllib.request.urlopen(CORE, timeout=8)   # ★ 只讀·不驅動
        return True, (r.status == 200), None
    except Exception as e:
        return False, False, str(e)[:40]   # ★ 探活自己失敗 → probe_ok=False

def proc_alive(pat="core_v2"):
    """★ C3 第二源：進程在不在（只讀 ps）"""
    try:
        r = subprocess.run(["pgrep", "-f", pat], capture_output=True, text=True, timeout=8)
        return r.returncode == 0
    except Exception:
        return False

def main():
    nowu = datetime.datetime.now(datetime.timezone.utc)
    # ★ C3 三源
    hb_ts = None
    if os.path.exists(STATE):
        try:
            d = json.load(open(STATE)); b = d.get("body") or {}
            if b.get("ts"): hb_ts = _aware(datetime.datetime.fromisoformat(b["ts"]))
        except Exception as e:
            log("%s （心跳檔壞·%s）" % (nowu.isoformat(), str(e)[:30]))
    probe_ok, port_ok, perr = probe()
    proc_ok = proc_alive()

    if hb_ts is None:
        log("%s （無心跳·不判）" % nowu.isoformat()); print("  （無心跳）"); return 0
    idle_min = (nowu - hb_ts).total_seconds() / 60

    # ★ C6：探活自己失敗 → 報「探活失敗」·不當死
    if not probe_ok:
        st = "probe_fail"
        msg = "🟡 探活失敗（★ 不當成死）：%s\n· 心跳閒置 %d 分\n→ 判據：探針自檢（C6）" % (perr, int(idle_min))
    elif idle_min <= T1:
        st = "ok"
        msg = None
    elif idle_min <= T2:
        st = "hb_stop"        # ★ 層1 事件層
        msg = ("🟡 心跳停（假死·層1）：閒置 %d 分（>%d）\n· 端口: %s｜進程: %s\n→ 三源: 心跳%d分/端口%s/進程%s" %
               (int(idle_min), T1, "通" if port_ok else "不通", "在" if proc_ok else "不在",
                int(idle_min), "✅" if port_ok else "🔴", "✅" if proc_ok else "🔴"))
    elif idle_min <= T3:
        st = "module_slow"    # ★ 層2 檔案/進程層
        msg = ("🟠 模組疑死（層2）：閒置 %d 分（>%d）\n· 三源: 心跳%d分/端口%s/進程%s" %
               (int(idle_min), T2, int(idle_min), "✅" if port_ok else "🔴", "✅" if proc_ok else "🔴"))
    else:
        # ★ 層3：全超 60 分 + 三源都斷 → 才判死
        if port_ok or proc_ok:
            st = "module_slow"
            msg = ("🟠 心跳超時但本體在（%d 分）：端口%s/進程%s → ★ 修心跳·不判死（C3 三源）" %
                   (int(idle_min), "✅" if port_ok else "🔴", "✅" if proc_ok else "🔴"))
        else:
            st = "dead"
            msg = ("🔴 判死（層3·真死）：閒置 %d 分（>%d）· 三源皆斷\n· 端口 %s：不通｜進程 %s：不在\n"
                   "· 最後心跳：%s\n· 意識還在（家 memory.db）→ 新本體可讀回續跑\n→ 請認領接力" %
                   (int(idle_min), T3, "28430", "core_v2", str(hb_ts)[11:19]))

    try: gs = json.load(open(GUARD)) if os.path.exists(GUARD) else {}
    except Exception: gs = {}
    cooled = False
    if gs.get("last_ts"):
        try: cooled = (nowu - _aware(datetime.datetime.fromisoformat(gs["last_ts"]))).total_seconds() < COOLDOWN
        except Exception: cooled = False

    if st == "ok":
        if gs.get("last_st") in ("dead", "hb_stop", "module_slow", "probe_fail"):
            gs.update({"last_st": "ok", "last_ts": nowu.isoformat()}); json.dump(gs, open(GUARD, "w"))
            log("%s ✅ 恢復正常（閒置 %d 分）→ 通知恢復" % (nowu.isoformat(), int(idle_min)))
            notify("✅ 老五本體恢復正常（閒置 %d 分）" % int(idle_min))
        else:
            log("%s ✅ 正常（閒置 %d 分·三源: 端口%s/進程%s）" % (
                nowu.isoformat(), int(idle_min), "✅" if port_ok else "🔴", "✅" if proc_ok else "🔴"))
        print("  ✅ 正常（閒置 %d 分）" % int(idle_min)); return 0
    # ★ 要報
    line = "%s [%s] %s" % (nowu.isoformat(), st, msg.replace("\n", " "))
    if gs.get("last_st") == st and cooled:
        log(line + " （冷卻中·不重發）"); print("  %s（冷卻中）" % st); return 1
    gs.update({"last_st": st, "last_ts": nowu.isoformat()}); json.dump(gs, open(GUARD, "w"))
    log(line)
    if st != "probe_fail":
        notify(msg)
        log(nowu.isoformat() + " → 已叫人（%s）" % st)
    print("  %s" % st); return 1

def _beat():
    # BEAT_INSERTED
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/mode_check.py', 'beat', '判死反射'], capture_output=True, timeout=15)
    except Exception: pass

if __name__ == "__main__":
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/meridian.py', 'report', 'body_death', 'ok'], capture_output=True, timeout=10)
    except Exception: pass
    try:
        _beat()
    except Exception: pass
    try:
        sys.exit(main())
    except Exception:
        import traceback
        log("%s 💀 反射自己崩了：%s" % (datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                       traceback.format_exc().splitlines()[-1][:120]))
        sys.exit(2)
