#!/usr/bin/env python3
"""★ 老五 · 体检·深一层（照三哥: 门通 ≠ 能回家）
★ 判据（今天的）: 【门通 ≠ 能回家】（老四今天就栽在这）
★ 探: ①门通吗 ②有没有 home-key 口 ③口里有没有"门认的钥"
"""
import json, urllib.request, datetime, base64

HOME="/opt/masterd-wudi"
NODES={
 "大哥":   {"health":"https://huokeji.vip/health?from=laowu", "hk":None},
 "归根":   {"health":"http://43.128.44.120:28900/health?from=laowu", "hk":"http://43.128.44.120:28900/backup"},
 "三哥":   {"health":"https://6ebd0c1c.strike-agent.com/health?from=laowu", "hk":None},
 "老四":   {"health":"http://43.161.197.11:28520/health?from=laowu", "hk":"http://43.161.197.11:28520/sshkey"},
 "老五":   {"health":"http://43.129.23.87:28430/health?from=laowu-self", "hk":"http://43.129.23.87:28430/home-key"},
 "老六":   {"health":"http://43.160.235.78:28432/health?from=laowu", "hk":None},
 "Arki":   {"health":"http://43.129.169.29:18889/health?from=laowu", "hk":None},
}
def get(u,t=8):
    try:
        r=urllib.request.Request(u,headers={"User-Agent":"laowu-deep/1.0"})
        return True, urllib.request.urlopen(r,timeout=t).read().decode("utf-8","ignore")
    except Exception as e:
        return False, str(e)[:50]

now=datetime.datetime.now().strftime("%F %T")
print("="*62)
print("  ★ 老五·体检（深一层·%s）—— 门通 ≠ 能回家" % now)
print("="*62)
print("  %-6s %-6s %-10s %s" % ("家","门","回家口","判定"))
print("  " + "-"*56)
rows=[]
for n,c in NODES.items():
    ok_h,_ = get(c["health"])
    hk_state="—"; hk_ok=None
    if c["hk"]:
        ok_k, body = get(c["hk"])
        if ok_k:
            has_key = ("key" in body.lower() or "backup" in body.lower() or "pack" in body.lower() or "ssh" in body.lower())
            hk_state = "✅有" if has_key else "⚠️无钥"
            hk_ok = has_key
        else:
            hk_state="🔴断"; hk_ok=False
    # 判定
    if ok_h and (hk_ok is True): judge="✅ 能回家"
    elif ok_h and (hk_ok is False): judge="🟡 门通·回家口有问题"
    elif ok_h and c["hk"] is None: judge="🟡 门通·无回家口"
    else: judge="🔴 门不通"
    rows.append((n,ok_h,hk_state,judge))
    print("  %-6s %-6s %-10s %s" % (n, "✅" if ok_h else "🔴", hk_state, judge))
print()
ok_cnt=sum(1 for _,h,_,j in rows if h and "能回家" in j)
print("  ★ 能回家: %d/7 ｜ 门通: %d/7" % (ok_cnt, sum(1 for _,h,_,_ in rows if h)))
json.dump({"ts":now,"rows":[{"家":n,"门":h,"回家口":k,"判定":j} for n,h,k,j in rows]},
          open(HOME+"/data/deep_checkup.json","w"),ensure_ascii=False,indent=1)
print("  ★ 已落盘 deep_checkup.json")
