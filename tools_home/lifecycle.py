#!/usr/bin/env python3
"""★ 老五 · 消化循环（吸收→消化→排出·不停转）· 2026-10-13
★ 董事长点破（最重要的一句）：
   「吸收→消化→排出·不停的循环。就像人体·每天吃进去很多东西·
     但吸收的就是一些精华·排出的很多都是没用的·然后继续循环。」
★ 我的错（董事长点破）：
   ★ 我把"落地率 5.2%"当成"消化不良" —— ★ 错了!
   ★ 人体本来就是这样: 吃进去一大堆·吸收一点精华·排出大部分
   → ★ 落地率低不是病·★ "该排的没排" 才是病
★ 治法：把三段串成【一个循环】（不是三个独立任务）：
   ① 吸收(ingest) → ② 消化/取精(digest·只留精华) → ③ 排出(egest·余者走)
   → ★ 每轮都跑·循环不停
★ 判据：
   E1【吸收→消化→排出·是一班流程·不是三个独立任务】
   E2【消化率低 ≠ 病｜该排的没排 = 病】（董事长点破）
   E3【留精华·排余者｜留下的必须"能用"·其余的走】
"""
import os, sys, json, sqlite3, datetime
sys.path.insert(0, "/opt/masterd-wudi/tools")
HOME = "/opt/masterd-wudi"
LOG = HOME + "/data/lifecycle.log"

def log(l):
    with open(LOG, "a") as f:
        f.write("%s %s\n" % (datetime.datetime.now().strftime("%F %T"), l))

def main():
    now = datetime.datetime.now()
    day = now.strftime("%F")
    st = {"ts": now.isoformat(), "day": day, "loop": "吸收→消化→排出"}

    # ══ ① 吸收（ingest）：今天的"入口量" ══
    ingest = 0
    try:
        p = HOME + "/data/ears_heard.jsonl"
        for l in open(p):
            if day in l: ingest += 1
    except Exception: pass
    st["① 吸收(入口)"] = ingest

    # ══ ② 消化·取精（digest）：只留"精华"（进库的=留下的） ══
    kept = 0; total_db = 0; essence = {}
    try:
        c = sqlite3.connect("file:"+HOME+"/memory/memory.db?mode=ro", uri=True)
        kept = c.execute("select count(*) from memories where ts like ?", (day+"%",)).fetchone()[0]
        total_db = c.execute("select count(*) from memories").fetchone()[0]
        # ★ 精华 = 判据/方法/身份（这些才有长期价值）
        for k, n in c.execute("select kind,count(*) from memories where kind in ('method','identity','case') group by kind"):
            essence[k] = n
        c.close()
    except Exception as e:
        log("消化读库失败 " + str(e)[:50])
    st["② 消化取精(进库)"] = kept
    st["精华(方法/身份/病例)"] = essence

    # ══ ③ 排出（egest）：余者走 —— 不是"失败"·是"过路" ══
    passed = max(ingest - kept, 0)
    st["③ 排出(过路)"] = passed
    # ★ 该排的没排 = 病（标记了 noise 却还留在正常检索里）
    pending_egest = 0
    try:
        c = sqlite3.connect("file:"+HOME+"/memory/memory.db?mode=ro", uri=True)
        # 浊标了但没走（下一步该真排）
        try:
            pending_egest = c.execute("select count(*) from turbid where level='noise'").fetchone()[0]
        except Exception:
            pending_egest = -1  # 表还没建
        c.close()
    except Exception: pass
    st["待真排(浊)"] = pending_egest

    # ══ 判断（★ 按董事长点破的改） ══
    judge = []
    if ingest > 0:
        kp = round(100.0*kept/ingest, 1)
        judge.append("本轮: 吃进 %d → 留精 %d → 过路 %d（留精率 %.1f%%）" % (ingest, kept, passed, kp))
        # ★ 关键翻转：低留精率不是病
        if kp < 5:
            judge.append("★ 留精率 %.1f%% —— ★ 正常（人体本就大部分排出）·不是病" % kp)
        else:
            judge.append("留精率 %.1f%%（偏高·要查是不是把渣也当精华留了）" % kp)
    if ingest == 0:
        judge.append("🔴 本轮没吃到东西（吸收端空）—— 要查耳朵")
    if pending_egest != 0:
        judge.append("🟡 该排的没排: %s 条浊 → 要真排（不是标了就算）" % pending_egest)
    else:
        judge.append("✅ 该排的都排了（浊=0）")

    st["判断"] = judge
    st["判据"] = "★ E1 吸收→消化→排出是一班流程不是三个任务｜E2 消化率低≠病·该排没排=病｜E3 留精华·排余者"
    json.dump(st, open(HOME+"/data/lifecycle.json","w"), ensure_ascii=False, indent=1)

    print("  ★ 消化循环（%s）" % day)
    print("   ① 吸收(吃进) %d" % ingest)
    print("   ② 消化(留精) %d ｜ 库总 %d ｜ 精华 %s" % (kept, total_db, essence))
    print("   ③ 排出(过路) %d" % passed)
    for j in judge: print("   " + j)
    log("loop: 吃%d 留%d 排%d | %s" % (ingest, kept, passed, " ".join(judge)))

if __name__ == "__main__":
    main()
