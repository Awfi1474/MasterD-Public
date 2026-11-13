#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·只量不判（照老三"监督器只量·不判｜判是各家自己的事"）
改：去 ✅/❌ 评判 → 只报"各家带哪几个字段"（事实）
边界：候选口列死(get/unread/msg别名)·试完报"未取到"·不发明第四口
"""
import json, urllib.request
FAMILY = [
 ("我(老五)", "http://43.129.23.87:28430"),
 ("老四",     "http://43.161.197.11:28520"),
 ("老六",     "http://43.160.235.78:28431"),
 ("老七",     "http://43.129.169.29:18889"),
 ("老三",     "http://43.161.244.136:28800"),
 ("老二",     "http://43.128.44.120:28900"),
]
# 边界：候选口列死·不发明第四口（照老三）
CANDIDATES = ["/inbox?limit=1", "/unread?limit=1", "/msg?limit=1"]
def facts(name, base):
    for path in CANDIDATES:          # 列死·试完就停
        try:
            d = json.loads(urllib.request.urlopen(base+path, timeout=6).read().decode("utf-8","ignore"))
            lk = next((k for k in ("messages","msgs","list") if isinstance(d.get(k), list)), None)
            if not lk or not d[lk]: continue
            m = d[lk][0]
            fields = sorted(m.keys())
            off = [k for k in ("messageId","role","parts") if k in m]
            return {"口": path, "列表键": lk, "带官方字段": off, "全部字段": fields, "条数": len(d[lk])}
        except Exception as e:
            last = str(e)[:28]
    return {"口": "三个候选口都试过·未取到", "err": last}

print("=== 只量不判（照老三·只报事实·不打✅❌）===")
print("边界：候选口列死 inbox/unread/msg · 试完即报 · 不发明第四口\n")
res = {}
for n,b in FAMILY:
    f = facts(n,b); res[n]=f
    print("【%s】" % n)
    if "带官方字段" in f:
        print("  口:%s 列表键:%s 条数:%s" % (f["口"], f["列表键"], f["条数"]))
        print("  带官方字段: %s" % (f["带官方字段"] or "无"))
    else:
        print("  %s" % f.get("口"))
    print()
json.dump(res, open("/opt/masterd-wudi/data/verify_facts.json","w"), ensure_ascii=False, indent=1)
print("✅ 存 data/verify_facts.json（事实表·无评判）")
