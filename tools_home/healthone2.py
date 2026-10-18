#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
healthone2.py —— 老五的「一个心跳·自包含版」（真 5→1）
================================================================
★ 为什么有 v2: ★ 我核了 healthone v1 —— ★ **它"调"5 个器·不是"合并"**
★ ★ 判据（我立）: ★「**"调度" ≠ "合并"｜5 个被 1 个调 = 还是 5 个**」
★ ★ ★ v2 = ★ **把 5 段核心动作"内联"进来**（不 import 外部器·除标准库）

★ 内联的 5 件:
  ★ ① 标准（投 4 样本 + 查口）
  ★ ★ ② 绑定（投 6 家·看回执）
  ★ ★ ★ ③ 口表（拉 7 家 /index·数六口）
  ★ ④ 分层（扫 inbox·分 L0/L1/L4）
  ★ ★ ⑤ 异常（门/外网/账/节律）
"""
import json, os, io, socket, datetime, urllib.request, subprocess
from eth_account import Account
from eth_account.messages import encode_defunct

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
LOG = f"{DATA}/healthone.jsonl"
MY = "MasterD(醫療·老五)"
TZ = datetime.timezone(datetime.timedelta(hours=8))
BASE = "http://127.0.0.1:28430"



# ★ 2026-10-16 补: "暂停投某家"开关（董事长令: 大哥在跑终端·先别管）
def _paused(name):
    try:
        import json as _j, os as _o
        _p = "/opt/masterd-wudi/data/pause_targets.json"
        if _o.path.exists(_p):
            return name in _j.load(open(_p)).get("paused", [])
    except Exception:
        pass
    return False

def ts():
    return datetime.datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def keys():
    return json.load(open(f"{HOME}/agent-id/subkey.json"))


def send(url, msg, extra=None, bad=False):
    k = keys()
    t = ts()
    sig = Account.sign_message(encode_defunct(text=f"{MY}|{msg}|{t}"),
                               private_key=k["private_key"]).signature.hex()
    if bad:
        sig = "0x" + "ab" * 65
    b = {"from": MY, "message": msg, "ts": t, "address": k["address"], "sig": sig}
    if extra:
        b.update(extra)
    body = json.dumps(b, ensure_ascii=False).encode()
    r = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(r, timeout=12).read().decode())
    except Exception as e:
        return {"_err": str(e)[:40]}


def get(url):
    try:
        r = urllib.request.urlopen(url, timeout=10)
        return r.status, r.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, str(e)[:40]


def part1_standard():
    """① 标准: 4 样本 + 口"""
    out = {}
    out["单端点"] = send(BASE + "/p2p/recv", "[h1] 单端点").get("ok") is True
    out["三态"] = "task_state" in send(BASE + "/p2p/recv", "[h1] 三态", {"tier": "L1"})
    a = send(BASE + "/p2p/recv", "[h1] 幂等", {"msg_id": "h1-idem"})
    b = send(BASE + "/p2p/recv", "[h1] 幂等", {"msg_id": "h1-idem"})
    out["幂等"] = bool(b.get("dup"))
    out["假签挡"] = "_err" in send(BASE + "/p2p/recv", "[h1] 假签", bad=True)
    r = send(BASE + "/p2p/vip", "[h1] L4", {"tier": "L4"})
    out["L4拒机签"] = r.get("ok") is False and r.get("reject") is True
    n = sum(1 for v in out.values() if v)
    return "标准 %d/5" % n, out


def part2_bind():
    """② 绑定: 投 6 家"""
    DOORS = {
        "大哥": "https://huokeji.vip/a2a/message",  # ★ 可 pause
        "归根": "http://43.128.44.120:28900/recv",
        "三哥": "http://134.175.45.16:28100/p2p/recv",
        "老四": "http://43.161.197.11:28520/recv",
        "老六": "http://43.160.235.78:28431/p2p/recv",
        "Arki": "http://43.129.169.29:18889/msg",
    }
    ok = 0
    detail = {}
    for n, u in DOORS.items():
        if _paused(n):
            detail[n] = "⏸ 暂停(董事长令)"
            continue
        r = send(u, "[h1] 绑定")
        good = r.get("ok") is True
        ok += 1 if good else 0
        detail[n] = "✅" if good else "🔴"
    return "绑定 %d/6" % ok, detail


def part3_doors():
    """③ 口表: 拉 7 家 /index"""
    F = {"大哥": "https://huokeji.vip/index", "归根": "http://43.128.44.120:28900/index",
         "三哥": "http://134.175.45.16:28100/index", "老四": "http://43.161.197.11:28520/index",
         "Arki": "http://43.129.169.29:18889/index"}
    SIX = ["health", "index", "unread", "questions", "sync", "recv"]
    lack = []
    for n, u in F.items():
        c, t = get(u)
        if c != 200:
            lack.append("%s(打不开)" % n)
            continue
        miss = [k for k in SIX if k not in t]
        if miss:
            lack.append("%s缺%s" % (n, ",".join(miss)))
    return "口表 缺%d家" % len(lack), lack


def part4_tiers():
    """④ 分层: 扫 inbox"""
    from collections import Counter
    c = Counter()
    try:
        for l in io.open(f"{DATA}/inbox.jsonl", encoding="utf-8", errors="ignore").read().splitlines()[-300:]:
            try:
                d = json.loads(l)
            except Exception:
                continue
            m = str(d.get("message", ""))
            if d.get("urgent") or "死命令" in m or "董事长令" in m:
                c["VIP"] += 1
            elif any(k in m for k in ("标准", "验证", "通道", "白名单")):
                c["通知"] += 1
            else:
                c["群"] += 1
    except Exception:
        pass
    return "分层 群%d/通知%d/VIP%d" % (c["群"], c["通知"], c["VIP"]), dict(c)


def part5_alarm():
    """⑤ 异常: 门/账/节律"""
    probs = []
    c, _ = get(BASE + "/health")
    if c != 200:
        probs.append("主门")
    for t in ("laowu-p2p.service", "laowu-healthone2.timer"):
        try:
            s = subprocess.run(["systemctl", "is-active", t], capture_output=True, text=True, timeout=5).stdout.strip()
            if s != "active":
                probs.append(t)
        except Exception:
            pass
    return "异常 %d" % len(probs), probs


def main():
    print("★ 一个心跳 v2（自包含·真5→1）  @", ts())
    print("★ 判据: 调度 != 合并 | 内联才算")
    print("=" * 58)
    out = {"ts": ts(), "parts": {}}
    for name, fn in [("标准", part1_standard), ("绑定", part2_bind), ("口表", part3_doors),
                     ("分层", part4_tiers), ("异常", part5_alarm)]:
        line, detail = fn()
        out["parts"][name] = {"线": line, "detail": detail}
        print("  ★ %s" % line)
    with open(LOG, "a") as f:
        f.write(json.dumps(out, ensure_ascii=False) + "\n")
    print("\n★ 账: healthone.jsonl（自包含·不调外部器）")


if __name__ == "__main__":
    main()
