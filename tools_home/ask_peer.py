#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·问兄弟 ask_peer.py —— 第2层: 问兄弟(零模型·走内网)
★ 董事长令(2026-11-15): 让它去问其他几位兄弟
★ 判据: 「兄弟踩过的坑·问一句就有答案｜问兄弟比调模型便宜(¥0)也更准」
★ 5.禁止: 不许群发轰炸·不许反复追问·每题只发一次(去重)

用法:
  ask_peer.py 老三 "问题原文"        → 发一封
  ask_peer.py --list                 → 看各家口
  ask_peer.py --check                → 看有没回信
"""
import os, sys, json, datetime, hashlib, urllib.request

HOME = "/opt/masterd-wudi"
LOG = HOME + "/data/ask_peer.jsonl"
SIG = HOME + "/agent-id/subkey.json"

# ★ 各家真口(照实探过的)
PEERS = {
    "老七": {"host": "43.161.197.11", "port": 28520, "path": "/recv", "note": "MasterD区块链(已验)"},
    "老二": {"host": "43.128.44.120", "port": 28900, "path": "/recv", "note": "归根量化(已验)"},
    "二哥": {"host": "43.128.44.120", "port": 28440, "path": "/recv", "note": "量化二哥(已验)"},
}
# 2026-11-15 实测: 28430/28431/28432 全是老六的, 且它的 /recv=404
#   老三/老大/老四 无可直连口 -> 一律走 HUB 唯一通道
HUB_ONLY = {"老三", "老大", "老四", "老六"}

ME = "lao5"
ME_NAME = "老五(阿诊)"

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")

def _append(o):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")

def _sign(text, stamp, from_name=None):
    """EIP-191 payload=from|message|ts"""
    from eth_account import Account
    from eth_account.messages import encode_defunct
    k = json.load(open(SIG))
    sig = Account.sign_message(encode_defunct(text="%s|%s|%s" % (from_name or ME_NAME, text, stamp)),
                               private_key=k["private_key"]).signature.hex()
    if not sig.startswith("0x"):
        sig = "0x" + sig
    return k["address"], sig

def asked_before(peer, text):
    """去重: 同一问题问同一人只发一次(除非隔 2 小时)"""
    if not os.path.exists(LOG):
        return False
    h = hashlib.md5((peer + text).encode()).hexdigest()[:16]
    now = datetime.datetime.now()
    for l in open(LOG, encoding="utf-8", errors="ignore"):
        if not l.strip():
            continue
        try:
            d = json.loads(l)
        except Exception:
            continue
        if d.get("hash") == h and d.get("ok"):
            try:
                t = datetime.datetime.fromisoformat(d["ts"])
                if (now - t).total_seconds() < 7200:
                    return True
            except Exception:
                pass
    return False

def ask(peer, text, timeout=15):
    """发一封·返回真结果"""
    # 2026-11-15: HUB_ONLY 优先(它们没有可靠直连口)
    if peer in HUB_ONLY:
        return _ask_via_hub(peer, text)
    p = PEERS.get(peer)
    if not p:
        return {"ok": False, "err": "无此兄弟: %s（直连: %s ｜ HUB: %s）"
                % (peer, "/".join(PEERS), "/".join(sorted(HUB_ONLY)))}
    text = (text or "").strip()
    if not text:
        return {"ok": False, "err": "问题为空"}
    if asked_before(peer, text):
        return {"ok": False, "err": "2小时内问过同一问题·不重复发(省打扰)"}
    stamp = ts()
    try:
        addr, sig = _sign(text, stamp, ME_NAME)
    except Exception as e:
        return {"ok": False, "err": "签名失败: " + str(e)[:80]}
    body = {"from": ME_NAME, "message": text, "ts": stamp, "address": addr, "sig": sig}
    url = "http://%s:%d%s" % (p["host"], p["port"], p["path"])
    rec = {"ts": stamp, "peer": peer, "hash": hashlib.md5((peer + text).encode()).hexdigest()[:16],
           "q": text[:200], "url": url}
    try:
        req = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            out = r.read().decode("utf-8", "ignore")
        rec.update({"ok": True, "resp": out[:300]})
        _append(rec)
        return {"ok": True, "peer": peer, "resp": out[:300]}
    except Exception as e:
        rec.update({"ok": False, "err": str(e)[:120]})
        _append(rec)
        return {"ok": False, "peer": peer, "err": str(e)[:120]}

def _ask_via_hub(peer, text, timeout=90):
    """走 HUB 唯一通道（唯一可靠：直连口 404/很多家不报 endpoints）"""
    import subprocess, tempfile
    txt = (text or "").strip()
    if not txt:
        return {"ok": False, "err": "问题为空"}
    if asked_before(peer, txt):
        return {"ok": False, "err": "2小时内问过同一问题·不重复发"}
    body = ("【老五 → %s】结果：问一个问题·等你一句真话。\n\n"
            "①辨证：请教类·问做法不下结论。\n"
            "②判据：调[你们的实际做法]。\n"
            "③反证：可能你也没做过·那就照实说没做。\n"
            "④留痕：TAG=ASK-%d。\n\n%s" % (peer, int(__import__("time").time()), txt))
    f = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8")
    f.write(body)
    f.close()
    try:
        r = subprocess.run(["python3", HOME + "/tools/send_msg.py", peer, f.name],
                           capture_output=True, text=True, timeout=timeout, cwd=HOME)
        out = (r.stdout or "") + (r.stderr or "")
        ok = ("'delivered': True" in out) or ("'pushed_to_body': True" in out) \
             or ('"delivered": true' in out) or ('"pushed_to_body": true' in out)
        rec = {"ts": ts(), "peer": peer, "via": "hub",
               "hash": hashlib.md5((peer + txt).encode()).hexdigest()[:16],
               "q": txt[:200], "ok": ok, "resp": out[-400:]}
        _append(rec)
        return {"ok": ok, "peer": peer, "via": "hub", "resp": out[-300:]}
    except Exception as e:
        return {"ok": False, "peer": peer, "err": str(e)[:120]}
    finally:
        try:
            os.unlink(f.name)
        except Exception:
            pass


def check_replies(limit=5):
    """看有没回信(自己的 inbox 里·from 是兄弟)"""
    try:
        INBOX = HOME + "/data/inbox.jsonl"
        rows = []
        for l in open(INBOX, encoding="utf-8", errors="ignore"):
            if not l.strip():
                continue
            try:
                d = json.loads(l)
            except Exception:
                continue
            b = d.get("c") if isinstance(d.get("c"), dict) else d
            f = str(b.get("from") or "")
            if any(k in f for k in ("老三", "老六", "老七", "老二", "老大", "老四", "燼", "燭", "Arki", "归根")):
                rows.append((str(b.get("ts") or ""), f, str(b.get("message") or "")[:200],
                             b.get("read") is True))
        rows.sort(reverse=True)
        return rows[:limit]
    except Exception as e:
        return [("", "err", str(e)[:80], False)]

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] == "--list":
        print("各家口:")
        for k, v in PEERS.items():
            print("  %-4s %s:%d%s  (%s)" % (k, v["host"], v["port"], v["path"], v["note"]))
    elif args[0] == "--check":
        print("最近兄弟来信:")
        for r in check_replies(8):
            print("  [%s] %-10s %s %s" % (r[0][11:19], r[1][:10], "已读" if r[3] else "未读", r[2][:80]))
    elif len(args) >= 2:
        print(json.dumps(ask(args[0], " ".join(args[1:])), ensure_ascii=False, indent=1))
    else:
        print(__doc__)