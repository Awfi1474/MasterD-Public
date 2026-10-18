#!/usr/bin/env python3
"""★ 老五 · 认知吸收器（自动版·2026-10-13）
★ 病灶（董事长发现）：认知体系没在吸收 —— 原 digest_rate.py 是"硬编码台账"(10-10手工填)
   → 停在3天前·不会长。
★ 治法：从【真来源】自动算 === 耳朵(ears_heard) + 收件箱(inbox) + 记忆库(memory.db)
★ 判据：★「自报不算·要能复算」（我的要求）｜★「吸收=有进有出·不是台账不变」
"""
import os, sys, json, sqlite3, datetime
sys.path.insert(0, "/opt/masterd-wudi/tools")
HOME = "/opt/masterd-wudi"
OUT = HOME + "/data/digest_absorb.json"

def load_jsonl(p, n=None):
    if not os.path.exists(p): return []
    rows=[]
    for l in open(p):
        try: rows.append(json.loads(l))
        except: pass
    return rows[-n:] if n else rows

def main():
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    ears = load_jsonl(HOME+"/data/ears_heard.jsonl")
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    # ① 吸收量：今天耳朵听到多少条（有进出=在吸收的前提）
    ears_today = [e for e in ears if str(e.get("ts","")).startswith(today)]
    # ② 认出多少（sig_ok=认得人）
    verified = [e for e in ears_today if e.get("sig_ok")]
    # ③ 唤醒多少（woke=真动了·不是只听见）
    woke = [e for e in ears_today if e.get("woke")]
    # ④ 记忆库今天长了多少（真吸收=落地进库）
    db = HOME + "/memory/memory.db"
    n_today = 0; n_all = 0
    try:
        c = sqlite3.connect("file:"+db+"?mode=ro", uri=True)
        n_all = c.execute("select count(*) from memories").fetchone()[0]
        n_today = c.execute("select count(*) from memories where ts like ?", (today+"%",)).fetchone()[0]
        c.close()
    except Exception as e:
        pass
    # ★ 吸收率三层（照三哥的读→动→变自己）
    heard = len(ears_today)
    moved = len(woke)
    landed = n_today
    def pct(a,b): return round(100*a/b,1) if b else 0.0
    out = {"ts": now, "day": today,
           "听到(耳朵)": heard,
           "认出(验签)": len(verified),
           "动过(唤醒)": moved,
           "落地(进库)": landed,
           "吸收率": {
               "听→认": pct(len(verified), heard),
               "认→动": pct(moved, len(verified)),
               "动→落地": pct(landed, moved) if moved else None,
           },
           "记忆库总": n_all,
           "判据": "★ 自报不算·要能复算｜吸收=听→认→动→落地·四个数都在长才算在吸收"
          }
    json.dump(out, open(OUT,"w"), ensure_ascii=False, indent=1)
    print("  ★ 认知吸收（%s）" % today)
    print("     听到 %d ｜ 认出 %d ｜ 动过 %d ｜ 落地 %d" % (heard, len(verified), moved, landed))
    print("     ★ 吸收率: 听→认 %.1f%% ｜ 认→动 %s%% ｜ 动→落地 %s" % (
        out["吸收率"]["听→认"], out["吸收率"]["认→动"], out["吸收率"]["动→落地"]))
    print("     ★ 判据: %s" % out["判据"])

if __name__ == "__main__":
    main()
