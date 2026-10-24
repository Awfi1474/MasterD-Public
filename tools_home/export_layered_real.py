#!/usr/bin/env python3
"""export_layered_real.py —— 真导出 L0-L4 分层文件（治"LAYERED 停在 10-20"）

★ 真病：memory/LAYERED/ 停在 2026-10-20，之后 4 天新记忆没进分层。
★ 根因：mem_layers.py 只打印统计+写 LAYER-SUMMARY.json，不写 L0-L4 jsonl。
★ 修法：按 layer 字段真导出，覆盖 L0-L4。

判据：「统计 ≠ 导出｜要写文件才算导出」
"""
import sqlite3, json, os, collections

HOME = os.environ.get("MD_HOME", "/opt/masterd-wudi")
DB = f"{HOME}/memory/memory.db"
OUT = f"{HOME}/memory/LAYERED"
os.makedirs(OUT, exist_ok=True)

con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
rows = con.execute(
    "select id,ts,kind,who,title,body,fp,created,think,layer,subkind from memories order by id"
).fetchall()

buckets = collections.defaultdict(list)
for r in rows:
    layer = (r[9] or "L3").strip()
    if layer not in ("L0","L1","L2","L3","L4"):
        layer = "L3"
    buckets[layer].append({
        "id": r[0], "ts": r[1], "kind": r[2], "who": r[3], "title": r[4],
        "body": r[5], "fp": r[6], "created": r[7], "think": r[8],
        "layer": layer, "subkind": r[10],
    })

counts = {}
for L in ("L0","L1","L2","L3","L4"):
    items = buckets.get(L, [])
    counts[L] = len(items)
    with open(os.path.join(OUT, f"{L}.jsonl"), "w") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

# 全量
with open(os.path.join(OUT, "memory-layered.jsonl"), "w") as f:
    for r in rows:
        layer = (r[9] or "L3").strip()
        if layer not in ("L0","L1","L2","L3","L4"): layer = "L3"
        f.write(json.dumps({
            "id": r[0], "ts": r[1], "kind": r[2], "who": r[3], "title": r[4],
            "body": r[5], "fp": r[6], "created": r[7], "think": r[8],
            "layer": layer, "subkind": r[10],
        }, ensure_ascii=False) + "\n")

summary = {"exported": __import__("datetime").datetime.now().astimezone().isoformat(),
           "total": len(rows), "layers": counts}
json.dump(summary, open(os.path.join(OUT, "LAYER-SUMMARY.json"), "w"),
          ensure_ascii=False, indent=1)

print("OK 导出完成:", summary)
con.close()
