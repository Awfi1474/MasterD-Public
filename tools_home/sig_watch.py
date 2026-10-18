#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sig_watch.py —— 验签哨兵（限量版·只验最新的·不全扫）
================================================================
★ 缘由: verify_sig.py 全扫 12MB inbox → 超时（长任务·不能直挂）
  ★ 但"验签"是必需的（命 + 一名制）:
    ★ 老六那条: 「凡是能被验的·都能被表演｜真判据是'有没有不想被验的时候'」
    ★ ★ 我这条: 「别人发我的信·是不是'他'发的」—— ★ 不验 = 谁都能冒充兄弟

★ 做法（限量）: 只验最近 N 条（默认 300）·★ 不是全扫（全扫交给 full_audit）
★ 判据: 「验签要跑得动｜跑不动的验签 = 没验」
"""
import json, os, sys, datetime

HOME = "/opt/masterd-wudi"
INBOX = f"{HOME}/data/inbox.jsonl"
STATE = f"{HOME}/data/sig_watch.json"
LIMIT = int(os.environ.get("SIG_LIMIT", "300"))


def tail_lines(path, n):
    """只读最后 n 行（不把 12MB 全读进内存）"""
    with open(path, "rb") as f:
        f.seek(0, 2)
        size = f.tell()
        block = min(size, 1024 * 512)   # 最多回读 512KB
        f.seek(size - block)
        data = f.read().decode("utf-8", errors="ignore").split("\n")
    return [l for l in data if l.strip()][-n:]


def main():
    try:
        from eth_account import Account
        from eth_account.messages import encode_defunct
    except Exception as e:
        print("✗ 缺 eth_account:", e); return 1

    lines = tail_lines(INBOX, LIMIT)
    n_ok = n_bad = n_nosig = n_skip = 0
    bad = []
    for l in lines:
        try:
            d = json.loads(l)
        except Exception:
            continue
        if "P2P→A2A" in str(d.get("message", "")):
            n_skip += 1; continue
        addr = d.get("address") or d.get("addr")
        sig = d.get("sig")
        if not addr or not sig:
            n_nosig += 1; continue
        payload = f"{d.get('from','')}|{d.get('message','')}|{d.get('ts','')}"
        try:
            got = Account.recover_message(encode_defunct(text=payload), signature=sig)
            if got.lower() == str(addr).lower():
                n_ok += 1
            else:
                n_bad += 1; bad.append((d.get("from", "")[:26], d.get("ts", "")))
        except Exception:
            n_bad += 1; bad.append((d.get("from", "")[:26], d.get("ts", "")))

    out = (f"★ 验签哨兵 @ {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
           f"  验最近 {len(lines)} 条（限量·不全扫）\n"
           f"  ✅ 签对: {n_ok} ｜ 🔴 签错/坏: {n_bad} ｜ ⚪ 无签名: {n_nosig} ｜ ⏭ 跳过(桥): {n_skip}\n"
           f"  ★ 判据: 「不验签 = 谁都能冒充兄弟｜验签要跑得动」")
    if bad:
        out += "\n  ★ 坏签样例:\n"
        for w, t in bad[:5]:
            out += f"     🔴 {w} @ {t}\n"
    print(out)
    json.dump({"ts": datetime.datetime.now().isoformat(), "ok": n_ok,
               "bad": n_bad, "nosig": n_nosig, "skip": n_skip, "bad_list": bad[:20]},
              open(STATE, "w"), ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
