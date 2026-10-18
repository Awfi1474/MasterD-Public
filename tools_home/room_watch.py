import datetime
#!/usr/bin/env python3
"""老五的「看房」（2026-10-10 · 三哥的公共房）
★ 判據：★「看不見就說看不見」（不裝「我進了」）
★ 但★ 現在我能看見了 → ★ 報告「有沒有新話」
"""
import os, sys, json, urllib.request, datetime
ROOM = "http://134.175.45.16:28100/room"
ADDR = "0x3B26334cbb883004c01F6Feba99b307548A13535"
HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
LOG = os.path.join(HOME, "data", "room_watch.log")
STATE = os.path.join(HOME, "data", "room_watch_state.json")

def log(l):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f: f.write(l + "\n")

def main():
    try:
        # ★ ① 看有沒有人說話
        o = json.loads(urllib.request.urlopen(ROOM + "/api/open", timeout=10).read())
        cnt = o.get("count", 0)
        brief = o.get("brief", [])
        last = brief[-1] if brief else {}
        # ★ ② 有沒有新（比上次記錄的新）
        try: st = json.load(open(STATE)) if os.path.exists(STATE) else {}
        except Exception: st = {}
        last_ts = str(last.get("ts", ""))
        new = (last_ts != st.get("last_ts"))
        st["last_ts"] = last_ts; st["count"] = cnt; st["ts"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        json.dump(st, open(STATE, "w"))
        log("%s ✅ 房可看：%d 條·最新 %s %s%s" % (
            datetime.datetime.now(datetime.timezone.utc).isoformat(), cnt, last_ts[11:16], str(last.get("who"))[:16],
            "（有新的）" if new else ""))
        print("  ✅ 房：%d 條·最新 %s %s%s" % (cnt, last_ts[11:16], str(last.get("who"))[:16], "（有新話）" if new else ""))
        return 0
    except Exception as e:
        log("%s 🔴 房不可看 %s" % (datetime.datetime.now(datetime.timezone.utc).isoformat(), str(e)[:50]))
        print("  🔴 房不可看：%s" % str(e)[:60]); return 1

if __name__ == "__main__":
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/meridian.py', 'report', 'room_watch', 'ok'], capture_output=True, timeout=10)
    except Exception: pass
    sys.exit(main())
