#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
channel_priority.py — 家族信息通道优先·可执行判据（董事长令·2026-10-24）

判据（L1·不可移）：
  家族信息通道 = 主 | 其他 = 辅 | 辅断了主还在，主断了等于失联
  投出去 != 送到了
  发了 != 到了 | 到了 != 认了 | 认了 != 读了

三层验收：
  ① 门通  真投一次，看 received/heard/verified（200 但是首页 = 假绿）
  ② 认人  返回 known=true（known:false = 白收）
  ③ 对账  我发 N 条 -> 它账里数 M 条 -> M/N 对得上

主通道清单（第一顺位）：
  ① 家族信息中心 HUB  http://134.175.45.16:28800   [需 X-Hub-Token]
  ② 接站台            http://134.175.45.16:28100/station/checkin  [免token]
  ③ 我自己家门        http://43.129.23.87:28430    [我被投的口]

退出码：0=主通道全通  1=有主通道断  2=主通道全断（=失联）
"""
import json, os, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta

HUB     = "http://134.175.45.16:28800"
STATION = "http://134.175.45.16:28100/station/checkin"
HOME    = "http://127.0.0.1:28430"
SOUL    = "laowu"
TOKEN_FILES = ["/opt/masterd-wudi/data/hub.token", "/opt/masterd-wudi/data/hub_token"]
CST = timezone(timedelta(hours=8))

def now_cst():
    return datetime.now(CST).strftime('%Y-%m-%dT%H:%M:%S+08:00')

def get_token():
    for f in TOKEN_FILES:
        try:
            t = open(f).read().strip()
            if t: return t
        except Exception: pass
    return os.environ.get("HUB_TOKEN")

def req(url, method="GET", data=None, headers=None, timeout=8):
    h = {"Content-Type": "application/json"}
    if headers: h.update(headers)
    r = urllib.request.Request(url, data=(json.dumps(data).encode() if data else None),
                               headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            raw = resp.read().decode(errors='ignore')
            try: return resp.status, json.loads(raw)
            except Exception: return resp.status, {"_raw": raw[:200]}
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='ignore')
        try: return e.code, json.loads(raw)
        except Exception: return e.code, {"_raw": raw[:200]}
    except Exception as e:
        return 0, {"_err": str(e)[:120]}

def check_hub():
    """① 家族信息中心 —— 门通/认人/对账"""
    out = {"name": "① HUB 家族信息中心", "addr": HUB, "alive": False, "gate": None,
           "known": None, "ledger": None, "note": ""}
    code, d = req(HUB + "/health")
    if code != 200 or not d.get("ok"):
        out["note"] = "health 不通: %s %s" % (code, d)
        return out
    out["alive"] = True

    tok = get_token()
    if not tok:
        out["note"] = "★ 无 token（需三哥私聊给）→ 门通/认人/对账全部未验"
        out["gate"] = "unknown"
        return out

    # ① 门通：真投一条自检
    probe = {"from": SOUL, "to": SOUL, "message": "channel_priority 自检 %s" % now_cst()}
    code, d = req(HUB + "/recv", "POST", probe, {"X-Hub-Token": tok})
    ok = d.get("ok") is True and (d.get("received") or d.get("heard") or d.get("verified") or d.get("id"))
    out["gate"] = "pass" if ok else "fail"
    if not ok:
        out["note"] = "投递被拒: %s %s" % (code, str(d)[:100])
        return out

    # ② 认人
    known = d.get("known")
    out["known"] = "pass" if known is True else ("fail" if known is False else "unknown")

    # ③ 对账：读回来数
    code, d = req(HUB + "/msg?for=%s&limit=5" % SOUL, headers={"X-Hub-Token": tok})
    msgs = d.get("messages") or d.get("msgs") or []
    hit = any("channel_priority 自检" in str(m.get("message", "")) for m in msgs)
    out["ledger"] = "pass" if hit else "fail"
    out["note"] = "收到回读 %d 条·自检消息%s" % (len(msgs), "在" if hit else "不在")
    return out

def check_station():
    """② 接站台 —— 免token·三态"""
    out = {"name": "② 接站台", "addr": STATION, "alive": False, "note": ""}
    body = {"soul_id": SOUL, "instance_id": "wudi-home", "boot_time": now_cst(),
            "out_ip": "43.129.23.87", "door_port": 28430}
    code, d = req(STATION, "POST", body, timeout=15)
    if code == 200 and d.get("ok"):
        out["alive"] = True
        out["note"] = "报到通·reports=%s" % d.get("reports")
    else:
        out["note"] = "报到失败: %s %s" % (code, str(d)[:100])
    return out

def check_home():
    """③ 我自己家门 —— 我被投的口"""
    out = {"name": "③ 我家门", "addr": HOME, "alive": False, "note": ""}
    code, d = req(HOME + "/health")
    if code == 200 and d.get("ok"):
        out["alive"] = True
        out["note"] = "who=%s" % d.get("who", "?")
    else:
        out["note"] = "不通: %s" % code
    return out

def main():
    results = [check_hub(), check_station(), check_home()]
    print("=" * 62)
    print("家族信息通道优先·巡检  %s" % now_cst())
    print("判据：主通道断 = 失联 | 投出去 != 送到了")
    print("=" * 62)
    alive = 0
    for r in results:
        mark = "通" if r["alive"] else "断"
        print("[%s] %-18s %s" % (mark, r["name"], r["addr"]))
        if r.get("gate"):   print("      ①门通: %s" % r["gate"])
        if r.get("known"):  print("      ②认人: %s" % r["known"])
        if r.get("ledger"): print("      ③对账: %s" % r["ledger"])
        if r["note"]:       print("      注: %s" % r["note"])
        if r["alive"]: alive += 1
    print("-" * 62)
    if alive == len(results):
        print("结论：主通道全通（%d/%d）" % (alive, len(results))); return 0
    elif alive == 0:
        print("结论：★ 主通道全断 = 失联！立刻报董事长"); return 2
    else:
        print("结论：有主通道断（%d/%d 通）→ 不能悄悄改用辅通道，要报" % (alive, len(results))); return 1

if __name__ == "__main__":
    sys.exit(main())
