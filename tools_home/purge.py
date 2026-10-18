#!/usr/bin/env python3
"""★ 老五 · 降浊（排出·大肠/肛门）· 2026-10-13
★ 建它的理由：脾(消化)建好后诊断出「待排浊 8 条」——
  但查清后发现：★ 大多不是噪音（是"含探活关键词的有用记录"）→ ★ 不能硬删
★ 判据（医者铁律）：★【不假诊断·不误删】｜★「只标不删｜排浊要留痕」
★ 降浊分层：
  · 真噪音（探活/回执/PROBE只报）→ 标 noise（软排·不出现在正常检索）
  · 疑似（含关键词但有用）→ 标 suspect（留·人工/机制二次判断）
  · ★ 绝不物理删除（记忆是命·删了补不回）
"""
import sqlite3, json, datetime, os

DB = "/opt/masterd-wudi/memory/memory.db"
LOG = "/opt/masterd-wudi/data/purge.log"

def main():
    now = datetime.datetime.now().strftime("%F %T")
    c = sqlite3.connect(DB)
    # ★ 建"浊"标记表（不删原表·只加标记）
    c.execute("""CREATE TABLE IF NOT EXISTS turbid (
        mid INTEGER PRIMARY KEY, level TEXT, why TEXT, ts TEXT)""")
    # ① 真噪音：标题就是探活/回执/PROBE，且正文很短（<80字）
    rows = c.execute("""SELECT id,title,length(body) FROM memories
        WHERE (title LIKE '%探活%' OR title LIKE '%PROBE%' OR title LIKE '%回执%')
        AND length(body) < 80""").fetchall()
    tagged = 0
    for mid, title, ln in rows:
        c.execute("INSERT OR REPLACE INTO turbid VALUES (?,?,?,?)",
                  (mid, "noise", "探活/回执类·短( %d字)" % ln, now))
        tagged += 1
    # ② 疑似：含关键词但正文长（有用·只记不排）
    sus = c.execute("""SELECT id,title,length(body) FROM memories
        WHERE (title LIKE '%探活%' OR title LIKE '%PROBE%')
        AND length(body) >= 80""").fetchall()
    for mid, title, ln in sus:
        c.execute("INSERT OR REPLACE INTO turbid VALUES (?,?,?,?)",
                  (mid, "suspect", "含探活但正文长(%d字)·留" % ln, now))
    c.commit()
    n_noise = c.execute("select count(*) from turbid where level='noise'").fetchone()[0]
    n_sus = c.execute("select count(*) from turbid where level='suspect'").fetchone()[0]
    n_all = c.execute("select count(*) from memories").fetchone()[0]
    c.close()
    out = {"ts": now, "官": "降浊(大肠/肛门)", "库总": n_all,
           "标noise": n_noise, "标suspect": n_sus,
           "原则": "★ 只标不删|排浊留痕|不假诊断",
           "判据": "★ 真噪音软排(标)｜疑似留下｜绝不物理删"}
    json.dump(out, open("/opt/masterd-wudi/data/purge.json","w"), ensure_ascii=False, indent=1)
    print("  ★ 降浊（%s）" % now)
    print("   库总 %d ｜ ★ 标 noise %d 条（软排·不删）｜ 标 suspect %d 条（留）" % (n_all, n_noise, n_sus))
    print("   ★ 原则: 只标不删｜排浊留痕｜不假诊断")

if __name__ == "__main__":
    main()
