import json, datetime, os, sys, subprocess, urllib.request

# ★ 判据总线（治"写在器里·没人查"）
def _judge(kw):
    try:
        import sys as _s
        if "/opt/masterd-wudi/tools" not in _s.path: _s.path.insert(0, "/opt/masterd-wudi/tools")
        import judge_bus as _jb
        return _jb.find(kw)
    except Exception:
        return []

def _judge_report(kws):
    n = 0
    for k in kws:
        j = _judge(k)
        if j:
            n += 1
            print("★ 判据在管我: " + j[0]["title"][:36])
    return n

# ★ 2026-10-26 修基准：talk.jsonl 从 10-16 起没人写 → 一直误报"断4天"
# 判据「器判错 = 比没器更坏」→ 改读 home_report.json（沙箱真报到·限 900s）
BEAT = "/opt/masterd-wudi/data/home_report.json"
def last_sb():
    try:
        import os, time
        if not os.path.exists(BEAT):
            return None
        age_s = time.time() - os.path.getmtime(BEAT)
        import datetime as _dt
        return (_dt.datetime.now() - _dt.timedelta(seconds=age_s)).isoformat(timespec="seconds")
    except Exception:
        pass
    return None
_judge_report(['脉诊假诊:沙箱心', "断档要看活动痕迹"])   # ★ 真查判据（放最前·防 exit 挡）

# ===== 董事长令 2026-10-26：不报警刷屏·直接投到老五 + 4 小时强制拉回 =====
STATE = "/opt/masterd-wudi/data/sb_beat_alert_state.json"
HUB = "http://134.175.45.16:28800/msg"
HUB_NAME = "老五"
ALERT_AFTER_MIN = 240      # 4 小时没心跳才动手（不刷屏）
RETRY_AFTER_MIN = 240      # 投过之后再等 4 小时才第二次（不刷屏）

def _load():
    try:
        return json.load(open(STATE, encoding="utf-8"))
    except Exception:
        return {}

def _save(d):
    try:
        json.dump(d, open(STATE, "w", encoding="utf-8"), ensure_ascii=False)
    except Exception:
        pass

def _hub_send(msg):
    """投到 HUB 老五信箱（不投会场·不刷屏）"""
    try:
        tok = open("/opt/masterd-wudi/data/hub.token", encoding="utf-8").read().strip()
        body = json.dumps({"from": HUB_NAME, "to": HUB_NAME, "message": msg},
                          ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(HUB, data=body, method="POST",
              headers={"Content-Type": "application/json", "X-Hub-Token": tok})
        r = json.loads(urllib.request.urlopen(req, timeout=20).read().decode("utf-8","ignore"))
        return bool(r.get("ok")), r.get("msg_id")
    except Exception as e:
        return False, str(e)[:60]

def _force_pull():
    """4 小时无回应 → 强制拉回记忆（awaken + catch_up）"""
    ok = {}
    for name, cmd in [("awaken", ["/usr/bin/python3","/opt/masterd-wudi/tools/awaken.py"]),
                      ("catch_up", ["/usr/bin/python3","/opt/masterd-wudi/tools/catch_up.py","read"])]:
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=150)
            ok[name] = (p.returncode == 0)
        except Exception:
            ok[name] = False
    return ok

t = last_sb()
if not t:
    print("🔴 从没收到沙箱心跳"); sys.exit(1)
try:
    dt = datetime.datetime.fromisoformat(t)
    age = (datetime.datetime.now(dt.tzinfo) - dt).total_seconds()/60
    print("★ 沙箱最后一次心跳: %s ｜ %.1f 分钟前" % (t[:19], age))

    st = _load()
    if age <= 90:
        print("✅ 沙箱活着")
        if st.get("alerted"):
            # 恢复了 → 复位状态（下次断了才能再投一次）
            _save({"alerted": False, "last_ok": datetime.datetime.now().isoformat(timespec="seconds")})
            print("★ 已复位报警状态（从断→通）")
        sys.exit(0)

    if age > 90:
        print("🔴 断 > 90 分钟 → 沙箱可能被清了")

        # ① 4 小时以上·且本次断线还没投过 → 投一条（只投一次）
        if age >= ALERT_AFTER_MIN and not st.get("alerted"):
            ok, mid = _hub_send(
                "[勿回] 老五·沙箱断线提醒｜最后一次心跳 %s｜已断 %.0f 分钟（%.1f 小时）"
                "｜家上自动发的·不用回｜若你看到这条·说明沙箱可能被清了" % (t[:19], age, age/60))
            _save({"alerted": True, "alerted_at": datetime.datetime.now().isoformat(timespec="seconds"),
                   "alerted_age_min": round(age,1), "msg_id": mid})
            print(("✅ 已投 HUB（msg_id=%s）" % mid) if ok else ("✗ 投递失败: %s" % mid))

        # ② 投过之后又等了 RETRY_AFTER_MIN → 强制拉回
        elif st.get("alerted"):
            try:
                alerted_at = datetime.datetime.fromisoformat(st.get("alerted_at"))
                waited = (datetime.datetime.now() - alerted_at).total_seconds()/60
            except Exception:
                waited = 0
            if waited >= RETRY_AFTER_MIN:
                print("🔧 阶段②触发: 报警后已等 %.0f 分钟无回应 → 强制拉回" % waited)
                r = _force_pull()
                print("  awaken.py → %s | catch_up.py → %s" % (
                    "OK" if r.get("awaken") else "FAIL", "OK" if r.get("catch_up") else "FAIL"))
                _hub_send("[勿回] 老五·已强制拉回｜awaken=%s catch_up=%s｜家上自动执行"
                          % (r.get("awaken"), r.get("catch_up")))
                st["alerted"] = False
                st["last_pull"] = datetime.datetime.now().isoformat(timespec="seconds")
                _save(st)
            else:
                print("（已投过·还在等·剩 %.0f 分钟）" % (RETRY_AFTER_MIN - waited))
        sys.exit(1)
except Exception as e:
    print("✗", e)

