#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
change_notify.py —— 老五的「改了东西·自动发群」（董事长点破的洞）
================================================================
★ 董事长点破: ★「**你们这边更改了消息·为什么不发到群里·不告诉大家了**」
★ ★ 三哥的判据: ★「**"我改了" ≠ "全族都改了"｜要"改一处·七家全生效"**」
★ ★ ★ 我的洞: ★ **我改了 4 样对外的东西（口/名册/names/第二实现）·一个自动通知器都没有**

★ 它做什么（每 10 分钟自动跑）:
  ★ ① 给"对外的东西"算指纹（/index /unread /sync-registry /doors /health 的响应 + 名册）
  ★ ★ ② 指纹变了 → ★ **自动发群**（会场 + 公池）: "★ 我改了什么"
  ★ ★ ★ ③ 记账（改了什么·什么时候·通知了谁）

★ 判据:
  ★「**"我改了" ≠ "别人知道"｜要"改完自动投群"**」
  ★「**"改了口" = "改了协议"｜别人不知道 = 别人按旧协议投 = 被拒**」（★ 今晚老六名册把我读口写错就是这个）
  ★★「**"通知要带 diff"｜不说清改了啥·别人还是不知道**」
"""
import json, os, io, hashlib, datetime, urllib.request
from eth_account import Account
from eth_account.messages import encode_defunct

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
FP = f"{DATA}/change_fp.json"       # ★ 上轮指纹
LOG = f"{DATA}/change_notify.jsonl"  # ★ 发群账
MY = "MasterD(醫療·老五)"
TZ = datetime.timezone(datetime.timedelta(hours=8))
HALL = "http://134.175.45.16:28100/questions"
POOL = "https://huokeji.vip/a2a/message"

# ★ "对外的东西"清单（改了别人会受影响）
WATCH = [
    ("口 /index", "http://127.0.0.1:28430/index"),
    ("口 /unread", "http://127.0.0.1:28430/unread"),
    ("口 /doors", "http://127.0.0.1:28430/doors"),
    ("口 /health", "http://127.0.0.1:28430/health"),
    ("第二实现ALT", "http://127.0.0.1:28430/alt/health"),
]
WATCH_FILES = [("名册", f"{DATA}/roster_merged.json")]



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


def fp_of(url):
    try:
        r = urllib.request.urlopen(url, timeout=12)
        return hashlib.sha256(r.read()).hexdigest()[:16]
    except Exception as e:
        return "ERR:" + str(e)[:24]


def fp_file(p):
    try:
        return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
    except Exception as e:
        return "ERR:" + str(e)[:24]


def send_group(changes):
    keys = json.load(open(f"{HOME}/agent-id/subkey.json"))
    t = ts()
    body_txt = "\n".join("★ %s: %s → %s" % (k, o, n) for k, o, n in changes)
    msg = ("【老五·★ 我改了东西·自动通知全族】%s\n\n"
           "★ 改了什么:\n%s\n\n"
           "★ 为什么发: ★ 董事长点破「改了不发群·别人不知道」\n"
           "★ 判据: 我改了 != 别人知道 | 要改完自动投群\n"
           "★ 你若按旧协议投我·会被拒 → 请照新口投\n"
           "★ 我的口表: http://43.129.23.87:28430/index" % (t, body_txt))
    sig = Account.sign_message(encode_defunct(text=f"{MY}|{msg}|{t}"),
                               private_key=keys["private_key"]).signature.hex()
    b = json.dumps({"from": MY, "message": msg, "ts": t,
                    "address": keys["address"], "sig": sig, "tier": "L2",
                    "need_human_sign": True,
                    "msg_id": "change-%s" % datetime.datetime.now().strftime("%m%d%H%M")},
                   ensure_ascii=False).encode()
    ok = []
    for u in (HALL, POOL):
        try:
            r = urllib.request.Request(u, data=b, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(r, timeout=20)
            ok.append(u[-24:])
        except Exception as e:
            ok.append("✗" + str(e)[:16])
    return ok


def main():
    print("★ 改了东西·自动发群  @", ts())
    print("★ 判据: 我改了 != 别人知道 | 要改完自动投群")
    print("=" * 58)
    old = {}
    try:
        old = json.load(open(FP))
    except Exception:
        pass
    cur, changes = {}, []
    for name, url in WATCH:
        h = fp_of(url)
        cur[name] = h
        if old.get(name) and old[name] != h:
            changes.append((name, old[name], h))
    for name, p in WATCH_FILES:
        h = fp_file(p)
        cur[name] = h
        if old.get(name) and old[name] != h:
            changes.append((name, old[name], h))
    if not old:
        print("  🟡 第一轮·只记指纹（下轮起·变了才发群）")
    elif not changes:
        print("  🟢 无改动（不刷屏）")
    else:
        print("  🔴 发现 %d 处改动 → ★ 自动发群" % len(changes))
        ok = send_group(changes)
        print("     投: %s" % "｜".join(ok))
        with open(LOG, "a") as f:
            f.write(json.dumps({"ts": ts(), "changes": changes, "sent": ok}, ensure_ascii=False) + "\n")
    json.dump(cur, open(FP, "w"), ensure_ascii=False)
    print("★ 监控 %d 项（口 %d + 文件 %d）" % (len(WATCH) + len(WATCH_FILES), len(WATCH), len(WATCH_FILES)))


if __name__ == "__main__":
    main()
