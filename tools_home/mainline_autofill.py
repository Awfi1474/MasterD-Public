#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mainline_autofill.py — 老五「主线自动补今天」补丁（2026-10-18）

★ 緣由: mainline.json 停在 10-10，因為 update() 只在手動寫時才調。
   wake.py 醒來讀主線 → 讀到 8 天前的「今天」。
★ 改法: 從記憶庫撈「今天的 event/identity/判據」→ 自動補進 mainline.json 的 current。
   不改 mainline.py 原邏輯，獨立一支。
★ 判據: 「昨天做了什麼·今天接著做」—— 主線要自己長，不能等人餵。

用法:
  python3 mainline_autofill.py           # 補今天
"""
import os, sys, json, sqlite3, datetime

HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
DB = os.path.join(HOME, "memory", "memory.db")
MAINLINE = os.path.join(HOME, "data", "mainline.json")
N = 12


def now():
    return datetime.datetime.now(datetime.timezone.utc)


def today_str():
    return now().strftime("%Y-%m-%d")


def load():
    if os.path.exists(MAINLINE):
        try:
            with open(MAINLINE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"days": [], "current": {}}


def save(d):
    os.makedirs(os.path.dirname(MAINLINE), exist_ok=True)
    tmp = MAINLINE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.replace(tmp, MAINLINE)


def fetch_today(n=N):
    """★ 撈今天（CST）的記憶 —— 不依賴 8766"""
    if not os.path.exists(DB):
        return []
    c = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    # created 是 UTC iso；用 date(created) 比對今天（CST 需 +8h）
    q = """select id, kind, title, body, created from memories
           where kind in ('event','identity','判据','器官','教训','真病')
           order by id desc limit 200"""
    out = []
    try:
        for r in c.execute(q):
            out.append({
                "id": r["id"], "kind": r["kind"],
                "title": r["title"] or "", "body": r["body"] or "",
                "created": r["created"] or "",
            })
    except Exception:
        return []
    return out


def autofill(n=N):
    d = load()
    t = today_str()
    cur = d.get("current") or {}

    # 抓今天的条目（按 CST 日期）
    rows = fetch_today(200)
    today_rows = []
    for r in rows:
        cst = r["created"]
        try:
            dt = datetime.datetime.fromisoformat(cst)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            cst = (dt + datetime.timedelta(hours=8)).strftime("%Y-%m-%d")
        except Exception:
            cst = ""
        if cst == t:
            today_rows.append(r)

    # 若 current 不是今天 → 收旧的开新的
    if cur.get("date") != t:
        if cur:
            d.setdefault("days", []).append(cur)
        cur = {"date": t, "done": [], "next": "", "block": "", "think": []}

    # 已有的 what 集合（去重）
    have = set(x.get("what", "")[:40] for x in cur.get("done", []))

    added = 0
    for r in today_rows[:n]:
        what = (r["title"] or r["body"] or "")[:70].replace("\n", " ").strip()
        if not what:
            continue
        if what[:40] in have:
            continue
        cur["done"].append({"ts": "auto", "what": what, "kind": r["kind"], "id": r["id"]})
        have.add(what[:40])
        added += 1

    # 若 current.done 空 → 至少放最新一条
    if not cur["done"] and rows:
        r = rows[0]
        cur["done"].append({"ts": "auto", "what": (r["title"] or r["body"])[:70], "kind": r["kind"], "id": r["id"]})
        added += 1

    d["current"] = cur
    save(d)
    print("  ★ 主线自动补: %s | 今天 %d 条 | 新补 %d 条" % (t, len(today_rows), added))
    for x in cur["done"][-4:]:
        print("     · [%s] %s" % (x.get("kind", "?"), x["what"][:56]))
    return cur


if __name__ == "__main__":
    autofill()
