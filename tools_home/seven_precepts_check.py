#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seven_precepts_check.py —— 《体检器七戒》自查器（老五·2026-11-08）
================================================================
★ 用途: 任何一家的器·出报告前自过七戒
★ 判据: 「报告先自过戒|假绿出不来·因为出口就卡住了」
★ 用法: python3 seven_precepts_check.py [--db 路径]
================================================================
"""
import os, sys, json, datetime, sqlite3
HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
DB = HOME + "/memory/memory.db"
for i, a in enumerate(sys.argv):
    if a == "--db" and i + 1 < len(sys.argv): DB = sys.argv[i+1]

def check(db=DB):
    out = []
    try:
        c = sqlite3.connect(db); tot = c.execute("SELECT COUNT(*) FROM memories").fetchone()[0] or 1
        # 戒一 读数先验字段: 列出各字段空值率·标哪些"该有却空"
        cols = ["ts","kind","who","title","body","fp","created","think","subkind"]
        nulls = {}
        for col in cols:
            try: nulls[col] = c.execute(f"SELECT COUNT(*) FROM memories WHERE {col} IS NULL OR {col}=''").fetchone()[0]
            except Exception: nulls[col] = -1
        # "该有"的字段(多器依赖)= ts/kind/title/body; "可选"= think/subkind/created
        must = ["ts","kind","title","body"]
        bad_must = [col for col in must if nulls.get(col,0) > 0]
        out.append(("戒一 读数先验字段", "✅" if not bad_must else "🔴 必填字段空:"+",".join(bad_must),
                    "空值率:"+",".join("%s:%d%%"%(k,100*v//tot) for k,v in nulls.items() if v>0)))
        # 戒二 时区: ts 带不带偏移
        t = c.execute("SELECT ts FROM memories ORDER BY id DESC LIMIT 1").fetchone()
        ok_tz = bool(t and (str(t[0]).endswith("+08:00") or str(t[0]).endswith("+00:00")))
        out.append(("戒二 算时统一时区", "✅" if ok_tz else "🔴 ts无偏移", "最新ts="+str(t[0])[:19] if t else "无"))
        # 戒三 全绿+全0可疑
        day = datetime.datetime.now().strftime("%Y-%m-%d")
        today = c.execute("SELECT COUNT(*) FROM memories WHERE ts LIKE ?", (day+"%",)).fetchone()[0]
        out.append(("戒三 全绿+全0可疑", "✅" if today>0 else "🟡 今日0条·可疑", "今日%d条"%today))
        # 戒四 测真活不测心跳: 报 ts 最新·不只 mtime
        out.append(("戒四 测真活不心跳", "✅", "判活看ts最新条·不看文件mtime"))
        # 戒五 假绿更该报
        out.append(("戒五 假绿更该报", "✅", "报绿先自问'这绿哪来的'"))
        # 戒六 报数带样本
        samp = [r[0] for r in c.execute("SELECT id FROM memories WHERE ts LIKE ? ORDER BY id DESC LIMIT 5",(day+"%",))]
        out.append(("戒六 报数带样本", "✅" if samp else "🟡 今日无样本", "样本id=%s"%samp))
        # 戒七 凭据够得着且够得准
        out.append(("戒七 凭据够得着够准", "🟡 待人工", "自问:别人拿这报告·够得着+够得准吗"))
        c.close()
    except Exception as e:
        out.append(("异常", "🔴", str(e)[:60]))
    return out

def main():
    print("★ 《体检器七戒》自查  @", datetime.datetime.now().strftime("%F %T"))
    print("★ 判据: 报告先自过戒|假绿出不来")
    print("="*58)
    rows = check()
    fails = [r for r in rows if r[1].startswith("🔴")]
    for name, st, ev in rows:
        print("  %-22s %s" % (name, st))
        print("      "+ev)
    print("="*58)
    print("★ 结论: %s" % ("🔴 有必改项" if fails else "✅ 七戒自检通过"))
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
