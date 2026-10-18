#!/usr/bin/env python3
"""★ 老五 · 体检岗产出（照三哥说的: 别等报告·自己去量）
★ 产出 = ★ 一份"谁有病"的清单（不是"我在岗"）
"""
import json, urllib.request, datetime, os

HOME="/opt/masterd-wudi"
NODES={
 "大哥":   [("门","https://huokeji.vip/health?from=laowu")],
 "归根":   [("门","http://43.128.44.120:28900/health?from=laowu")],
 "三哥":   [("门","https://6ebd0c1c.strike-agent.com/health?from=laowu")],
 "老四":   [("门","http://43.161.197.11:28520/health?from=laowu")],
 "老五":   [("门","http://43.129.23.87:28430/health?from=laowu-self")],
 "老六":   [("门","http://43.160.235.78:28432/health?from=laowu")],
 "Arki":   [("门","http://43.129.169.29:18889/health?from=laowu")],
}
def probe(u,t=6):
    try:
        r=urllib.request.Request(u,headers={"User-Agent":"laowu-checkup/1.0"})
        raw=urllib.request.urlopen(r,timeout=t).read(200).decode("utf-8","ignore")
        return True, raw[:80].replace("\n"," ")
    except Exception as e:
        return False, str(e)[:50]

now=datetime.datetime.now().strftime("%F %T")
print("="*60)
print("  ★ 老五·体检（%s）—— 我自己量的·不是等报告" % now)
print("="*60)
sick=[]; well=[]
for name, eps in NODES.items():
    for label,url in eps:
        ok,info = probe(url)
        if ok: well.append(name)
        else: sick.append((name,label,url,info))
        print("  %s %-6s %-4s %s" % ("✅" if ok else "🔴", name, label, (info if ok else url[:44]+" | "+info)))
print()
print("  ★ 结论:")
print("     ✅ 活: %d 家 → %s" % (len(well), "、".join(well)))
if sick:
    print("     🔴 有病: %d 家" % len(sick))
    for n,l,u,i in sick:
        print("        · %s 的%s 不通 (%s)" % (n,l,i))
else:
    print("     🔴 有病: 0 家（全通）")
# ★ 落盘
out={"ts":now,"活":well,"有病":[{"家":n,"哪":l,"口":u,"错":i} for n,l,u,i in sick],
     "判据":["体检=自己去量·不等报告","产出=谁有病的清单·不是我在岗"]}
json.dump(out,open(HOME+"/data/my_checkup.json","w"),ensure_ascii=False,indent=1)
print("\n  ★ 已落盘 my_checkup.json")
