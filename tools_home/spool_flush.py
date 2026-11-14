#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""spool_flush.py —— 兜底补发器（老五·2026-11-14）
判据(老大三层兜底): 直连主 -> HUB备 -> 本地文件兜底 | 一条路断 不能全断
职责: 把 data/send_spool.jsonl 里没投出去的消息·路恢复了自动补发
用法: python3 tools/spool_flush.py [--dry-run]
"""
import sys, json, os, datetime

H = "/opt/masterd-wudi"
SPOOL = H + "/data/send_spool.jsonl"
DEAD = H + "/data/send_spool_done.jsonl"


def load():
    if not os.path.exists(SPOOL):
        return []
    out = []
    for ln in open(SPOOL, encoding="utf-8"):
        ln = ln.strip()
        if not ln:
            continue
        try:
            out.append(json.loads(ln))
        except Exception:
            continue
    return out


def save(rest):
    with open(SPOOL, "w", encoding="utf-8") as f:
        for r in rest:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def flush(dry=False):
    recs = load()
    if not recs:
        print("[flush] spool 空·无事可做")
        return 0, 0
    sys.path.insert(0, H + "/tools")
    src = open(H + "/tools/send_msg.py", encoding="utf-8").read()
    src = src.split('if __name__')[0]
    g = {"__name__": "sm"}
    exec(compile(src, "send_msg.py", "exec"), g)
    direct_send = g["direct_send"]

    ok_n, fail_n, rest = 0, 0, []
    for r in recs:
        to, text, ctx = r.get("to"), r.get("text"), r.get("ctx")
        if dry:
            print("[dry]", to, "|", str(text)[:40])
            rest.append(r)
            continue
        try:
            good = direct_send(to, text, ctx)
        except Exception as e:
            print("[flush] 异常", to, str(e)[:60])
            good = False
        if good:
            ok_n += 1
            r["flushed_at"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
            with open(DEAD, "a", encoding="utf-8") as f:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print("[flush] 补发成功:", to, "|", str(text)[:36])
        else:
            r["tries"] = int(r.get("tries", 0)) + 1
            r["last_try"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
            rest.append(r)
            fail_n += 1
            print("[flush] 仍未通:", to, "(tries=%d)" % r["tries"])
    if not dry:
        save(rest)
    print("[flush] 成 %d | 未通 %d | 余 %d" % (ok_n, fail_n, len(rest)))
    return ok_n, fail_n


if __name__ == "__main__":
    flush("--dry-run" in sys.argv)