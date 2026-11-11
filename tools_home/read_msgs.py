#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""read_msgs.py v2 —— 老五·看消息统一入口(2026-11-08·通道统一后)
================================================================
判据(通道统一5统一): 收/查 读【HUB真源】·不只读本地inbox.jsonl
  · 第一源: HUB /inbox?for=lao5 (全族真源)
  · 第二源: 本地 data/inbox.jsonl (兜底·HUB不通时)
  · 中转: HUB /msg?for=lao5 (过时·只读不用)
用法: read_msgs.py [N] [since]
================================================================
"""
import sys, json, urllib.request

TOK = open("/opt/masterd-wudi/data/hub.token").read().strip()
HUB = "http://43.161.244.136:28800"
FOR = "lao5"   # ★ 焊死令(2026-11-12): 读默认带 for=自己·不靠记
LOCAL = "/opt/masterd-wudi/data/inbox.jsonl"

def from_hub(n, since):
    try:
        req = urllib.request.Request(HUB + "/inbox?for=" + FOR + "&limit=%d" % max(n,30),
                                     headers={"Authorization": "Bearer " + TOK})
        d = json.loads(urllib.request.urlopen(req, timeout=10).read())
        rows = []
        for m in (d.get("messages") or d.get("list") or []):
            ts = str(m.get("ts", ""))
            if since and ts < since:
                continue
            rows.append((ts[:16], str(m.get("from",""))[:14], str(m.get("to",""))[:10], str(m.get("message",""))))
        return rows
    except Exception as e:
        print("  [HUB不通·落本地]", str(e)[:60])
        return None

def from_local(n, since):
    rows, seen = [], set()
    try:
        lines = open(LOCAL, encoding="utf-8", errors="ignore").readlines()[-4000:]
    except Exception:
        return []
    for l in lines:
        try: d = json.loads(l)
        except Exception: continue
        ts = str(d.get("ts",""))
        if since and ts < since: continue
        msg = str(d.get("message",""))
        k = (ts[:16], str(d.get("from","")), msg[:50])
        if k in seen: continue
        seen.add(k)
        rows.append((ts[:16], str(d.get("from",""))[:14], str(d.get("to",""))[:10], msg))
    return rows

def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    since = sys.argv[2] if len(sys.argv) > 2 else None
    rows = from_hub(n, since)
    src = "HUB /inbox(全族真源)"
    if rows is None:
        rows = from_local(n, since)
        src = "本地 inbox.jsonl(兜底)"
    rows.sort()
    for r in rows[-n:]:
        print("[%s] %-14s -> %-10s | %s" % (r[0], r[1], r[2], r[3][:150].replace("\n"," ")))
    print("--- %d 条(%s) ---" % (min(n,len(rows)), src))

if __name__ == "__main__":
    main()
