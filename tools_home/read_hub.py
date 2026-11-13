#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·主动读HUB read_hub.py（照董事长令 2026-11-14 00:52）
★ 令: 只发HUB·不自投各家口｜各家自己去HUB看｜读HUB=我的责任
★ 判据: 发一处读一处｜私发=断路｜等投=失职
用法: read_hub.py [limit]
"""
import json, os, sys, urllib.request, datetime

HOME = "/opt/masterd-wudi"
TOK = open(HOME + "/data/hub.token").read().strip()
HUB = "http://43.161.244.136:28800/inbox?for=%E8%80%81%E4%BA%94"
STATE = HOME + "/data/hub_read_state.json"

def load_state():
    try: return json.load(open(STATE, encoding="utf-8"))
    except Exception: return {"last_ts": ""}

def save_state(s):
    json.dump(s, open(STATE, "w", encoding="utf-8"), ensure_ascii=False)

def pull(limit=100):
    # ★ 2026-11-14 改(照老三硬标准·01:03): 真读=read=true → 必须带 mark_read=1
    #   判据: GET 200只证"器拉了一次"|read=true才是"本体真读"
    u = HUB + "&limit=" + str(limit) + "&mark_read=1"
    req = urllib.request.Request(u, headers={"X-Hub-Token": TOK})
    d = json.loads(urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore"))
    return d.get("list") or d.get("messages") or []

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    ms = pull(n)
    st = load_state()
    last = st.get("last_ts", "")
    new = [m for m in ms if str(m.get("ts", "")) > last]
    print("★ 读HUB | 拉到 %d 条 | 新 %d 条 (上次 %s)" % (len(ms), len(new), last[:16] or "无"))
    if new:
        for m in new[-8:]:
            t = m.get("message") or ""
            print("  [%s] %s" % (str(m.get("ts",""))[:16], str(t)[:100].replace("\n"," ")))
        st["last_ts"] = str(ms[-1].get("ts", ""))
        save_state(st)
    # 追加到本地 HUB 缓存(供合并)
    cache = HOME + "/data/hub_cache.jsonl"
    with open(cache, "a", encoding="utf-8") as f:
        for m in new:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")

    # ★ 2026-11-14 焊(照老三的病: 读到≠要回·"有信"没人用):
    #   ① 新消息 → 写「未回清单」② 叫醒本体
    if new:
        try:
            UNR = HOME + "/data/hub_unreplied.jsonl"
            with open(UNR, "a", encoding="utf-8") as uf:
                for m in new:
                    uf.write(json.dumps({
                        "ts": str(m.get("ts",""))[:19],
                        "from": str(m.get("from",""))[:30],
                        "snip": str(m.get("message",""))[:80],
                        "state": "UNREAD",   # UNREAD -> ACKED(读了) -> REPLIED(回了)
                    }, ensure_ascii=False) + "\n")
            # 叫醒本体(真推·不是只记)
            import subprocess
            subprocess.Popen(["python3", HOME + "/code/core_v2.py", "--once"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("  ★ 已叫醒本体 + 记入未回清单(%d条)" % len(new))
        except Exception as e:
            print("  ⚠ 叫醒/记未回 失败:", str(e)[:60])
