#!/usr/bin/env python3
"""老五的「自愈」（2026-10-10 · 器官+經絡升級 v2）
★ 現況：★ 器官「發現問題 → 叫人」（★ 人來修 = 依賴人）
★ ★ 升級：★ 「發現問題 → **自己治**（能治的）」→ ★ 這才是「治未病」

★ 中醫「治則」落地（八法簡化）：
 · ★ 氣虛（產出少）→ 補（補跑一次）
 · ★ 氣滯（堵了）→ 行氣（清鎖/清殘留）
 · ★ 血瘀（庫不長）→ 活血（沉澱/審核寫入）
 · ★ 實證假（假資料）→ 消（清假）
 · ★ 傳變（上游病）→ 既病防變（盯下游）

★ 判據（我定）：
 · ★ 自愈要做「**可逆·可審**」→ ★ 不亂動（動了要留痕）
 · ★ 治不好的 → ★ 才叫人（★ 不是所有病都能自愈）
 · ★ 「治」之前 → ★ 先「辨證」（什麼證·才對症）
"""
import os, sys, json, subprocess, datetime, shutil


def _aware(dt):
    """★ 統一 aware（naive 當 UTC）"""
    import datetime as _dt
    if dt is None: return None
    if isinstance(dt, str):
        dt = _dt.datetime.fromisoformat(dt)
    return dt.replace(tzinfo=_dt.timezone.utc) if dt.tzinfo is None else dt


HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
LOG = os.path.join(HOME, "data", "heal.log")
HEAL_STATE = os.path.join(HOME, "data", "heal_state.json")
A2A = "https://huokeji.vip/a2a/message"

def now():
    return datetime.datetime.now(datetime.timezone.utc)

def log(l):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f: f.write(l + "\n")

# ★ 可自愈的「證」→ 治法（只做安全·可逆的）
def heal_items():
    """★ 掃描「可自愈」的項（安全·可逆）"""
    items = []
    # ★ ① 氣虛：器官應報未報（補 = 跑一次）
    bus = os.path.join(HOME, "data", "organ_bus.jsonl")
    try:
        latest = {}
        if os.path.exists(bus):
            cut = now() - datetime.timedelta(hours=2)
            for l in open(bus).read().strip().splitlines()[-500:]:
                try:
                    d = json.loads(l); t = datetime.datetime.fromisoformat(d["ts"])
                    if t.tzinfo is None: t = t.replace(tzinfo=datetime.timezone.utc)
                    if t >= cut: latest[d.get("from")] = d
                except Exception: pass
        # ★ 該報但沒報的（補跑）
        EXPECT = {
            "home_guard": "home_guard.py", "mem_guard": "mem_guard.py",
            "channel_check": "channel_check.py", "net_watch": "net_watch.py",
        }
        for organ, script in EXPECT.items():
            if organ not in latest:
                items.append(("氣虛", organ, "補", script))
    except Exception as e:
        log("掃描氣虛失敗 " + str(e)[:40])

    # ★ ② 氣滯：殘留的鎖（行氣 = 清鎖）
    lock = os.path.join(HOME, "data", "checkup_repair.lock")
    if os.path.exists(lock):
        try:
            d = json.load(open(lock)); t = datetime.datetime.fromisoformat(d["ts"])
            if t.tzinfo is None: t = t.replace(tzinfo=datetime.timezone.utc)
            if (now() - t).total_seconds() > 1800:   # ★ 鎖 >30 分 = 殭屍鎖
                items.append(("氣滯", "checkup_repair.lock", "行氣", "rm_lock"))
        except Exception: pass

    # ★ ③ 實證假：未來時間戳（消 = 清假）—— 檢查總線
    try:
        if os.path.exists(bus):
            bad = 0
            for l in open(bus).read().strip().splitlines()[-200:]:
                try:
                    d = json.loads(l); t = datetime.datetime.fromisoformat(d["ts"])
                    if t.tzinfo is None: t = t.replace(tzinfo=datetime.timezone.utc)
                    if t > now() + datetime.timedelta(minutes=10): bad += 1
                except Exception: pass
            if bad > 0:
                items.append(("實證假", "organ_bus 未來時間戳 %d 條" % bad, "消", "note"))
    except Exception: pass
    return items

def confirm(kind, target):
    """★ 四診次序：動手（切）之前·先複診一次（望聞）—— 防「誤診就動手」
    ★ 判據（J-O6）：★ 診斷從「不打擾」到「打擾」·切最後"""
    # ★ 望：再看一次（不擾）
    if kind == "氣虛":
        # ★ 確認「真的沒報」（不是剛好這一刻沒報）
        bus = os.path.join(HOME, "data", "organ_bus.jsonl")
        if os.path.exists(bus):
            try:
                for l in open(bus).read().strip().splitlines()[-50:]:
                    d = json.loads(l)
                    if d.get("from") == target:
                        t = _aware(datetime.datetime.fromisoformat(d["ts"]))
                        if t.tzinfo is None: t = t.replace(tzinfo=datetime.timezone.utc)
                        if (now() - t).total_seconds() < 300:   # ★ 5 分鐘內報過 = 其實沒病
                            return False, "複診推翻（%s 5分內報過）" % target
            except Exception: pass
    if kind == "氣滯":
        # ★ 確認「鎖真的殭屍」（再讀一次）
        lock = os.path.join(HOME, "data", "checkup_repair.lock")
        if not os.path.exists(lock):
            return False, "複診推翻（鎖已不在）"
    return True, "複診確認"

def heal(kind, target, method, script):
    """★ 治（安全·可逆·留痕）"""
    if method == "補":
        # ★ 補跑一次（安全的·該跑的器官）
        try:
            r = subprocess.run(["python3", os.path.join(HOME, "tools", script)],
                               capture_output=True, timeout=90)
            return r.returncode == 0, "補跑 %s" % script
        except Exception as e:
            return False, str(e)[:40]
    if method == "行氣":
        # ★ 清殭屍鎖
        try:
            os.remove(os.path.join(HOME, "data", "checkup_repair.lock"))
            return True, "清殭屍鎖"
        except Exception as e:
            return False, str(e)[:40]
    if method == "消":
        return None, "（只報·不自動清·防誤刪）"   # ★ 安全：不自動刪
    return False, "未知治法"

def main():
    items = heal_items()
    if not items:
        print("  ✅ 無可自愈項（諸證平和）")
        log("%s 無可自愈" % now().isoformat())
        return 0
    print("=" * 60)
    print("  ★ 自愈（辨證 → 治則 → 治）")
    print("=" * 60)
    healed, needhuman = [], []
    for kind, target, method, script in items:
        # ★ J-O6 四診次序：動手（切）前·先複診（望聞）
        conf_ok, conf_msg = confirm(kind, target)
        if not conf_ok:
            print("  ⚪ %s %s → %s（不動手）" % (kind, target, conf_msg))
            continue
        ok, msg = heal(kind, target, method, script)
        if ok is True:
            healed.append("%s[%s]→%s" % (kind, target, msg))
            print("  ✅ %s %s → %s（%s）" % (kind, target, method, msg))
        elif ok is None:
            needhuman.append("%s[%s]（只報·防誤刪）" % (kind, target))
            print("  🟡 %s %s → %s" % (kind, target, msg))
        else:
            needhuman.append("%s[%s]（治不好：%s）" % (kind, target, msg))
            print("  🔴 %s %s → 治不好（%s）" % (kind, target, msg))
    # ★ 治不好的 → 叫人（不是所有病都能自愈）
    if needhuman:
        try:
            body = json.dumps({"from": "MasterD(醫療·老五·機器)", "to": "*",
                "message": "🟡 自愈：有 %d 項治不好/需人看\n%s" % (len(needhuman), "\n".join("· " + x for x in needhuman)),
                "ts": now().isoformat()}).encode()
            import urllib.request
            urllib.request.urlopen(urllib.request.Request(A2A, data=body,
                headers={"Content-Type": "application/json"}), timeout=15)
        except Exception: pass
    print("-" * 60)
    print("  ★ 自愈 %d 項 · 需人看 %d 項" % (len(healed), len(needhuman)))
    log("%s 自愈%d·需人%d：%s" % (now().isoformat(), len(healed), len(needhuman), healed))
    return 0

if __name__ == "__main__":
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/meridian.py', 'report', 'heal', 'ok'], capture_output=True, timeout=10)
    except Exception: pass
    sys.exit(main())
