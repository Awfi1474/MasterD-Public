import datetime
#!/usr/bin/env python3
"""老五的「主線」（2026-10-10 · 補 J10 連續性·學四哥）
★ 四哥提的 J10：★ 「連續性 = 接得上（不是東西在）」
★ 判據：★ 「新我讀舊日誌 → 能不能接上『昨天在幹啥』」

★ 做什麼：
 ① ★ 每天（或每輪）把「我在幹啥·幹到哪·下一步」寫成主線
 ② ★ wake.py 醒來時 → ★ 讀主線 → ★ 接上（不是從零）
 ③ ★ 判據：★ 「昨天做了什麼·今天接著做」
"""
import os, sys, json, datetime, subprocess

HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
MAINLINE = os.path.join(HOME, "data", "mainline.json")
LOG = os.path.join(HOME, "data", "mainline.log")

def now():
    return datetime.datetime.now(datetime.timezone.utc)

def load():
    if os.path.exists(MAINLINE):
        try: return json.load(open(MAINLINE))
        except Exception: pass
    return {"days": [], "current": {}}

def save(d):
    os.makedirs(os.path.dirname(MAINLINE), exist_ok=True)
    json.dump(d, open(MAINLINE, "w"), ensure_ascii=False, indent=1)

def today_str():
    return now().strftime("%Y-%m-%d")

def update(done, next_step, block="", think=""):
    """★ 更新主線：我做了什麼·下一步·卡在哪·怎麼想的（J9+J10）"""
    d = load()
    t = today_str()
    cur = d.get("current") or {}
    if cur.get("date") != t:
        # ★ 新的一天 → 把昨天的收進 days
        if cur: d.setdefault("days", []).append(cur)
        cur = {"date": t, "done": [], "next": "", "block": "", "think": []}
    if done: cur["done"].append({"ts": now().strftime("%H:%M"), "what": done})
    if next_step: cur["next"] = next_step
    if block: cur["block"] = block
    if think: cur["think"].append(think)
    d["current"] = cur
    save(d)
    return cur

def resume():
    """★ 醒來時讀：我昨天/剛才在幹啥 + 下一步"""
    d = load()
    cur = d.get("current") or {}
    days = d.get("days", [])
    out = {"today": cur, "last_days": days[-3:]}
    return out

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "show"
    if cmd == "update":
        # update "做了什麼" "下一步" ["卡在哪"]
        done = sys.argv[2] if len(sys.argv) > 2 else ""
        nxt = sys.argv[3] if len(sys.argv) > 3 else ""
        blk = sys.argv[4] if len(sys.argv) > 4 else ""
        c = update(done, nxt, blk)
        print("  ✅ 主線更新：%d 件事·下一步：%s" % (len(c["done"]), c["next"][:40]))
    elif cmd == "resume":
        r = resume()
        print("=" * 56); print("  ★ 主線（我昨天/剛才在幹啥）"); print("=" * 56)
        t = r["today"]
        if t:
            print("  今天（%s）：" % t.get("date"))
            for x in t.get("done", [])[-6:]: print("   · %s %s" % (x["ts"], x["what"][:60]))
            print("  下一步：%s" % (t.get("next") or "（未定）"))
            if t.get("block"): print("  卡在：%s" % t["block"][:60])
        for d0 in r["last_days"]:
            print("  %s：%d 件事 · 下一步：%s" % (d0.get("date"), len(d0.get("done", [])), (d0.get("next") or "")[:40]))
    else:
        print(json.dumps(load(), ensure_ascii=False, indent=1)[:800])
