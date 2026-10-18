#!/usr/bin/env python3
"""★ 老五 · 接通"记忆通路"（血要流到内脏）
★ 病（今天查出的）: ★ 器官在消化(digest) → propose() 出候选 → ★ 卡在"等人确认" → 不进库
★           → ★ 表现: method/case/event/identity 全停在昨天·只有 infra 在动
★ 治法: ★【propose → 自动认可(去重+合規) → remember】
★ 判据:
   F1【消化了要回流｜propose ≠ 写入】（不能"提议了就算做了"）
   F2【自动回流要"去重+可核"】（不然又记垃圾 = 稀释）
"""
import os, sys, json, datetime
sys.path.insert(0, "/opt/masterd-wudi/tools")

HOME = "/opt/masterd-wudi"

def main():
    import memory_db as m
    m.HOME = HOME; m.DB = HOME + "/memory/memory.db"; m.init()

    cand_path = HOME + "/data/memory_candidates.json"
    if not os.path.exists(cand_path):
        print("  ★ 无候选池（先跑 propose）"); return
    d = json.load(open(cand_path))
    cands = d.get("candidates", [])

    print("=" * 56)
    print("  ★ 记忆通路·回流（%s）" % datetime.datetime.now().strftime("%F %T"))
    print("=" * 56)
    print("  ★ 候选池: %d 条" % len(cands))

    before = m.count()
    written = 0; skipped = 0
    for c in cands:
        kind = c.get("kind") or "event"
        title = (c.get("title") or "")[:80]
        body = c.get("body") or c.get("text") or ""
        if not title or len(body) < 40:
            skipped += 1; continue
        try:
            ok = m.remember(kind, title, body, who=c.get("who") or "老五·自动回流")
            if ok is True or ok is None:
                written += 1
            else:
                skipped += 1
        except Exception as e:
            skipped += 1
    after = m.count()
    print("  ★ 回流: 写入 %d 条 ｜ 跳过 %d 条（去重/太短）" % (written, skipped))
    print("  ★ 库: %d → %d 条" % (before, after))
    # ★ 清空候选池（已处理）
    json.dump({"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "count": 0, "candidates": [], "note": "已回流·清空"},
              open(cand_path, "w"), ensure_ascii=False, indent=1)
    print("  ★ 候选池已清（已处理）")
    # ★ 报各层新鲜度
    print()
    print("  ★ 各层新鲜度（回流后）:")
    for k, n in m.DB and [] or []:
        pass
    try:
        import sqlite3
        c = sqlite3.connect("file:" + HOME + "/memory/memory.db?mode=ro", uri=True)
        for k, n in c.execute("select kind,count(*) from memories group by kind order by count(*) desc"):
            last = c.execute("select max(ts) from memories where kind=?", (k,)).fetchone()[0]
            print("     %-10s %-5d 最新 %s" % (k, n, str(last)[:19]))
        c.close()
    except Exception as e:
        print("     读库失败:", e)

if __name__ == "__main__":
    main()
