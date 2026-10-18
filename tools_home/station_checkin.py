#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""station_checkin.py —— 自动报到（★ 只写站台·不发群）
★ 判据: 「"报到" != "播报"｜报到是内务·播报才是刷屏」
"""
import json, urllib.request, socket, time

STATION = "http://134.175.45.16:28100/station/checkin"
SOUL = "laowu"
BUNDLE_SRC = "http://43.129.23.87:28430/station-bundle"

def main():
    # 取包
    bundle = ""
    try:
        bundle = urllib.request.urlopen(BUNDLE_SRC, timeout=10).read().decode()[:20000]
    except Exception:
        bundle = ""
    body = {
        "soul_id": SOUL,
        "instance_id": open('/proc/sys/kernel/random/boot_id').read().strip()[:12],
        "boot_time": time.strftime('%Y-%m-%dT%H:%M:%S+08:00', time.gmtime(time.time() + 8*3600)),
        "out_ip": "43.129.23.87",
        "in_ip": socket.gethostbyname(socket.gethostname()),
        "door_port": 28430,
    }
    if bundle: body["bundle"] = bundle
    # ★ 照 Tandem: 技能指纹（防冒充·"说会" vs "真会"）
    try:
        import subprocess as _sp
        _sh = _sp.run(["python3", HOME + "/tools/skillhash.py", "show"], capture_output=True, text=True, timeout=20).stdout
        import re as _re
        _m = _re.search(r"\*\*([0-9a-f]{16})\*\*", _sh or "")
        if _m: body["skill_hash"] = _m.group(1)
    except Exception:
        pass
    try:
        req = urllib.request.Request(STATION, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        r = urllib.request.urlopen(req, timeout=20)
        d = json.loads(r.read().decode())
        print("checkin ok=%s soul_id=%s bundle=%d reports=%s" % (
            d.get("ok"), d.get("soul_id"), len(bundle), d.get("reports")))
    except Exception as e:
        print("checkin 失败: " + str(e)[:80])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
