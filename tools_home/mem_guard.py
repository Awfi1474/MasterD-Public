import datetime
#!/usr/bin/env python3
"""記憶庫守護（2026-10-10）★ 三哥教的告警 + 我的沉澱
★ 判據：★ 最新記憶 > 24h → ★ 告警（不是等壞了才知道）
"""
import os, sys, json, datetime, urllib.request
sys.path.insert(0, "/opt/masterd-wudi/tools")
HOME = "/opt/masterd-wudi"
LOG = os.path.join(HOME, "data", "mem_guard.log")
STATE = os.path.join(HOME, "data", "mem_guard_state.json")
A2A = "https://huokeji.vip/a2a/message"

def log(l):
    with open(LOG, "a") as f: f.write(l + "\n")

def notify(msg):
    try:
        body = json.dumps({"from": "MasterD(醫療·老五·機器)","to":"*","message":msg,
                           "ts":datetime.datetime.now(datetime.timezone.utc).isoformat()}).encode()
        urllib.request.urlopen(urllib.request.Request(A2A, data=body,
            headers={"Content-Type":"application/json"}), timeout=15)
        return True
    except Exception as e:
        log("%s → 警報失敗 %s" % (datetime.datetime.now(datetime.timezone.utc).isoformat(), str(e)[:40])); return False

def main():
    import memory_db as m
    m.HOME = HOME; m.DB = os.path.join(HOME,"memory","memory.db"); m.init()
    # ★ ① 先沉澱（自動寫）
    try:
        import memory_distill
        memory_distill.HOME = HOME
        # ★ 2026-10-10 學 Arki：自動亂寫會稀釋 → 改成「提議」
        memory_distill.propose()
        # ★ 2026-10-14 老五接"记忆通路": ★ propose 完·自动回流进库
        #   病: propose 只"提议"·不进库 → ★ 各层停在昨天（血堵在闸门前）
        #   判据: F1【消化了要回流｜propose ≠ 写入】
        try:
            import mem_flow
            mem_flow.main()
        except Exception as _e2:
            log("%s 回流失败 %s" % (now, str(_e2)[:50]))
    except Exception as e:
        log("%s 沉澱失敗 %s" % (datetime.datetime.now(datetime.timezone.utc).isoformat(), str(e)[:60]))
    # ★ ② 再健康檢查（自動查）
    ok, msg = m.health()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try: st = json.load(open(STATE)) if os.path.exists(STATE) else {}
    except Exception: st = {}
    if not ok:
        if st.get("last") == msg:
            log("%s 🔴 %s（同問題·不重發）" % (now, msg)); return 1
        st["last"] = msg; json.dump(st, open(STATE,"w"))
        log("%s 🔴 %s" % (now, msg))
        notify("🔴 記憶庫告警（自律發現）：" + msg); log(now + " → 已發警報")
        return 1
    else:
        if st.get("last"):
            st["last"] = None; json.dump(st, open(STATE,"w"))
            log("%s ✅ 記憶庫恢復：%s" % (now, msg))
        else:
            log("%s ✅ %s" % (now, msg))
        return 0

def _beat():
    # BEAT_INSERTED
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/mode_check.py', 'beat', '記憶庫'], capture_output=True, timeout=15)
    except Exception: pass

if __name__ == "__main__":
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/meridian.py', 'report', 'mem_guard', 'ok'], capture_output=True, timeout=10)
    except Exception: pass
    try:
        _beat()
    except Exception: pass
    try:
        sys.exit(main())
    except Exception:
        import traceback
        log("%s 💀 守護自己崩了：%s" % (datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                       traceback.format_exc().splitlines()[-1][:120]))
        sys.exit(2)
