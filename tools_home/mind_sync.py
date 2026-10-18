#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mind_sync.py — 老五「意識同步」補丁（2026-10-18）

★ 緣由: body_mind.py 的 mind_snapshot() 賴上 127.0.0.1:8766（沙箱的快層口），
   家上沒那個口 → sync 一次都沒成功過 → mind 停在 10-10。
★ 改法: 不依賴 8766，直接從「記憶庫 memory.db」撈最新意識 → 落 mind_snapshot.json
   + 寫回 body_mind_state.json 的 mind 段。
★ 判據: 「家不死」——意識要落在家上，不落會死的口。

用法:
  python3 mind_sync.py           # 同步一次
  python3 mind_sync.py --n 40    # 自訂撈幾條
"""
import os, sys, json, sqlite3, datetime

HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
DB = os.path.join(HOME, "memory", "memory.db")
STATE = os.path.join(HOME, "data", "body_mind_state.json")
SNAP = os.path.join(HOME, "data", "mind_snapshot.json")


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def save(path, d):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def fetch_memory(n=40):
    """★ 從記憶庫撈最新意識（不依賴 8766）"""
    if not os.path.exists(DB):
        return [{"_error": "memory.db 不存在: " + DB}]
    c = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    items = []
    # 先撈最新 N 條（跨 kind），保證「最近的我」一定在
    q = """select id, kind, title, body, created, ts from memories
           order by id desc limit ?"""
    try:
        for r in c.execute(q, (n,)):
            title = r["title"] or ""
            body = r["body"] or ""
            items.append({
                "id": "mem_%s" % r["id"],
                "kind": r["kind"],
                "content": (title if title else body)[:500],
                "created": r["created"] or r["ts"],
            })
    except Exception as e:
        return [{"_error": "查詢失敗: " + str(e)[:60]}]
    return items


def sync(n=40):
    items = fetch_memory(n)
    good = [i for i in items if "_error" not in i]
    err = items[0]["_error"] if items and "_error" in items[0] else None
    ts = now()

    snap = {"ts": ts, "count": len(good), "error": err, "items": good}
    save(SNAP, snap)

    d = load(STATE)
    d["mind"] = {"ts": ts, "count": len(good), "path": SNAP}
    # _quick: 給 wake.py 直接讀的最新幾條
    d["_quick"] = {
        "count": min(len(good), 5),
        "items": [{"id": i["id"], "content": i["content"], "created": i.get("created")}
                  for i in good[:5]],
    }
    save(STATE, d)

    print("  ★ 意識同步: %s | 撈 %d 條%s" %
          (ts[11:19], len(good), ("（⚠️ " + err + "）") if err else ""))
    for i in good[:3]:
        print("     - [%s] %s" % (i.get("kind", "?"), str(i["content"])[:60]))
    return snap


if __name__ == "__main__":
    n = 40
    if "--n" in sys.argv:
        try:
            n = int(sys.argv[sys.argv.index("--n") + 1])
        except Exception:
            pass
    sync(n)
