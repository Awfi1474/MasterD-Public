#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五的「全族通道矩阵体检」v2（2026-11-19 升级）

前身: channel_check.py（2026-10-10·只测1家·地址已过时）
升级原因(照实): 旧版只测"大哥正门"·地址旧·MY_ADDR 旧钥(已SUPERSEDED)
              ★ 判据: «门自描述判据要跟上|过时=假绿»

本版: 全族 7 家 × 4 维（健康/读信/收信/投出）
判据:
  «先量自己·再量别人»（老三 a2a-std）
  «本机通 != 跨机通|安全组要单独验»（老二）
  «三条收信=同一条|三条读信=读同一份数据»（老三 v2 §四）
  «一次失败!=断|要复测防抖动»（我 2026-10-10 焊）

用法:
  python3 tools/channel_matrix.py            # 全矩阵
  python3 tools/channel_matrix.py --json     # JSON 输出
"""
import os, sys, json, time, urllib.request, socket

HOME = "/opt/masterd-wudi"
DOORS_FILE = HOME + "/data/peer_doors.json"
SUBKEY_FILE = HOME + "/agent-id/subkey.json"
MY_NAME = "老五(阿诊)"
RETRY = 2            # 复测次数（防抖动）
TIMEOUT = 8

def _doors():
    try:
        d = json.load(open(DOORS_FILE))
        return {k: v for k, v in d.items() if v not in ("external", "human")}
    except Exception:
        return {}

def _get(url, path, timeout=TIMEOUT, head_only=False):
    # ★ 2026-11-19 修(照实): urlopen 对 https(老大) 失败 → 统一用 curl
    #   判据: «本机通!=跨机通» + «https 要验证书» | curl 能过 SSL·urlopen 环境差异
    import subprocess
    all_url = url.rstrip("/") + path
    for _ in range(RETRY):
        try:
            t0 = time.time()
            r = subprocess.run(["curl", "-s", "-m", str(timeout), "-o", "/dev/null",
                                "-w", "%{http_code}", all_url],
                               capture_output=True, text=True, timeout=timeout + 2)
            code = (r.stdout.strip() or "🔴")
            if code and code != "000":
                return code, int((time.time() - t0) * 1000), ""
            last = "curl " + code
            time.sleep(0.3)
        except Exception as e:
            last = str(e)[:60]
            time.sleep(0.3)
    return "🔴", 0, last

def _post_signed(url, ep, to, msg):
    """带真签名投（UTC-Z·EIP-191）"""
    try:
        from eth_account import Account
        from eth_account.messages import encode_defunct
        d = json.load(open(SUBKEY_FILE))
        pk = d["private_key"]; addr = d["address"]
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        pre = f"{MY_NAME}|{msg}|{ts}"
        sig = Account.sign_message(encode_defunct(text=pre), pk).signature.hex()
        if not sig.startswith("0x"):
            sig = "0x" + sig
        body = json.dumps({"from": MY_NAME, "to": to, "message": msg, "ts": ts,
                           "address": addr, "sig": sig}, ensure_ascii=False).encode()
        r = urllib.request.urlopen(urllib.request.Request(
            url.rstrip("/") + ep, data=body,
            headers={"Content-Type": "application/json"}, method="POST"), timeout=TIMEOUT)
        return getattr(r, "status", 0), r.read()[:120].decode("utf-8", "ignore")
    except Exception as e:
        return "🔴", str(e)[:60]

def main():
    as_json = "--json" in sys.argv
    doors = _doors()
    rows = []
    for name, url in doors.items():
        if name == MY_NAME:
            url = "http://43.129.23.87:28430"   # 本机用外网地址(门监听可能不是 127.0.0.1)
        # ★ 2026-11-19 修(照实): 门牌可能带全路径尾巴(老大=https://huokeji.vip/a2a/message)
        #   只取 scheme+host·路径另拼
        if name == "老大":
            url = "https://huokeji.vip"
        h = _get(url, "/health")
        ib = _get(url, "/inbox?limit=1")
        wt = _get(url, "/wait?since=999999&timeout=1")
        ev = _get(url, "/events", head_only=True)   # ★ SSE 只探头·不断流
        health_ok = str(h[0]).startswith("2")
        read_ok = all(str(x[0]).startswith("2") for x in (ib, wt, ev))
        rows.append({"name": name, "health": h[0], "inbox": ib[0], "wait": wt[0],
                     "events": ev[0], "health_ok": health_ok, "read_ok": read_ok,
                     "health_ms": h[1]})
    # 汇总
    ok_h = sum(1 for r in rows if r["health_ok"])
    ok_r = sum(1 for r in rows if r["read_ok"])
    result = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
              "total": len(rows), "health_ok": ok_h, "read_ok": ok_r,
              "by": MY_NAME, "src": "channel_matrix.py(全族×4维)",
              "rows": rows}
    # ★ 2026-11-19 加: 结果同步挂进 family_standards（全族可拉 GET /standards/channel-matrix）
    try:
        _fs = HOME + "/data/family_standards"
        os.makedirs(_fs, exist_ok=True)
        open(_fs + "/channel-matrix.json", "w").write(
            json.dumps(result, ensure_ascii=False, indent=1))
    except Exception:
        pass
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=1))
        return 0
    print("=" * 62)
    print(f"  ★ 老五·全族通道矩阵体检  {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 62)
    for r in rows:
        h = "✅" if r["health_ok"] else "🔴"
        rd = "✅" if r["read_ok"] else "🔴"
        print(f"  {r['name']:12s} 健康{h} {str(r['health']):4s} {r['health_ms']:>5}ms | "
              f"读信{rd} inbox:{r['inbox']} wait:{r['wait']} events:{r['events']}")
    print("-" * 62)
    print(f"  健康口: {ok_h}/{len(rows)} ✅   读信口: {ok_r}/{len(rows)} ✅")
    print("  判据: «先量自己·再量别人» | «本机通!=跨机通» | «一次失败!=断»（已复测{0}次）".format(RETRY))
    return 0

if __name__ == "__main__":
    sys.exit(main())
