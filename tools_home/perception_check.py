#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""感知体检器·perception_check.py (老五 2026-11-10)
用途: 用"感知四层"量任意一家(或自己)的"感知能力"。
董事长令: 真正研究感知 + 互相验证(我验各家 / 各家验我 / 不互验)。
判据: 感知=收+释+组+疼痛 | 收到!=感觉到 | 能疼才算真感知
用法: python3 perception_check.py <家名> <host> <port> [token]
      python3 perception_check.py self        # 量自己
输出: 可被对方复算的JSON(互验用)
"""
import sys, os, json, socket, urllib.request, datetime

def now(): return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

def probe(host, port, path="/health", timeout=5):
    """①收(transduce): 真探·只读"""
    try:
        r = urllib.request.urlopen("http://%s:%d%s" % (host, port, path), timeout=timeout)
        return r.getcode(), r.read()[:2000].decode('utf-8', 'ignore')
    except Exception as e:
        return None, str(e)[:60]

def check(name, host, port):
    """感知四层 逐层量"""
    out = {"who": name, "addr": "%s:%d" % (host, port), "ts": now(), "layers": {}}
    code, body = probe(host, port)
    # ① 收(transduce): 能收到吗
    got = code == 200
    out["layers"]["①收(sensor)"] = {"ok": got, "code": code}
    if not got:
        out["verdict"] = "无感知(收不到)"
        return out
    # ② 释/组(interpret): 收到的是不是"能懂的结构"(而非空/兜底页)
    interpretable = False; info = {}
    try:
        j = json.loads(body)
        interpretable = isinstance(j, dict) and len(j) > 0
        info = {k: j[k] for k in list(j)[:5]}
    except Exception:
        interpretable = len(body.strip()) > 0
    out["layers"]["②释/组(interpret)"] = {"ok": interpretable, "sample": info}
    # ③ 能记(自证分): 有没有"记忆/自报"字段(能证明它记得自己是谁)
    rem = any(k in body for k in ('memory', '记忆', 'who', 'name', 'identity', '自证'))
    out["layers"]["③能记(自证分)"] = {"ok": rem}
    # ④ 疼(反馈): 有没有"告警/心跳/代价"类字段(会疼的证据)
    pain = any(k in body for k in ('alert', 'alarm', '告警', 'heartbeat', '心跳', 'health', 'ok'))
    out["layers"]["④疼(反馈)"] = {"ok": pain}
    n = sum(1 for v in out["layers"].values() if v["ok"])
    out["verdict"] = "%d/4 层" % n
    return out

if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "self":
        r = check("老五(阿诊)", "43.129.23.87", 28430)
        # 自己也能读沙箱本地
        code, body = probe("127.0.0.1", 8766, "/", 3)
        r["sandbox_local_8766"] = code
    else:
        name, host, port = a[0], a[1], int(a[2])
        r = check(name, host, port)
    print(json.dumps(r, ensure_ascii=False, indent=2))
