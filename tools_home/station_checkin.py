#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""station_checkin.py —— 自动报到（★ 改走 HUB 心跳·2026-11-08）
★ 判据：「报到 != 播报｜报到是内务·播报才是刷屏」
★ 2026-11-08 改：三哥HUB无专门station口(实测404)·报到改用 HUB /heartbeat
   · 老大原站台(134.175.45.16:28100)已失效（三哥换机）
   · 新HUB：43.161.244.136:28800
★ 修 bug：原代码用未定义的 HOME（skillhash 那段）
"""
import json, urllib.request, socket, time, os

HOME = os.environ.get("MD_HOME", "/opt/masterd-wudi")
HUB = "http://43.161.244.136:28800"
STATION = HUB + "/heartbeat"          # ★ 报到=心跳
ME = "老五(阿诊)"

def token():
    try: return open(f"{HOME}/data/hub.token").read().strip()
    except Exception: return ""

def main():
    body = {
        "from": ME,
        "status": "alive",
        "ip": "43.129.23.87",
        "port": 28430,
        "boot_time": time.strftime('%Y-%m-%dT%H:%M:%S+08:00', time.gmtime(time.time() + 8*3600)),
    }
    # ★ 技能指纹（防冒充·"说会" vs "真会"）—— 文件不在就跳过（不因小件断报到）
    try:
        sh = os.path.join(HOME, "tools", "skillhash.py")
        if os.path.exists(sh):
            import subprocess, re
            out = subprocess.run(["python3", sh, "show"], capture_output=True, text=True, timeout=20).stdout
            m = re.search(r"([0-9a-f]{16})", out or "")
            if m: body["skill_hash"] = m.group(1)
    except Exception:
        pass
    tok = token()
    try:
        req = urllib.request.Request(STATION, data=json.dumps(body, ensure_ascii=False).encode(),
                                     headers={"Content-Type": "application/json", "X-Hub-Token": tok},
                                     method="POST")
        d = json.loads(urllib.request.urlopen(req, timeout=20).read().decode())
        print("checkin ok=%s role=%s ack=%s" % (d.get("ok"), d.get("role"), d.get("ack")))
    except Exception as e:
        print("checkin 失败: " + str(e)[:100])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
