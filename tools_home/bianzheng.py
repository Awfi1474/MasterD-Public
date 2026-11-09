#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bianzheng.py v2 —— 老五·医家辨证器(做实版·加五行传变/治未病)
照我自己的道(医家=辨证论治+治未病|见肝传脾·既病防变)
判据:「不问活不活(二值)·问什么证(八纲)」+「治未病:见肝传脾=预判下游」
"""
import sys, json, datetime

# 五行相克(传变:见肝之病·知肝传脾·当先实脾)
KE = {"肝":"脾","脾":"肾","肾":"心","心":"肺","肺":"肝"}  # 相克(传变方向)
# 器→脏(我的器官映射)
ORGAN2ZANG = {"liver":"肝","spleen":"脾","kidney":"肾","heart":"心","lung":"肺",
              "liver.py":"肝","spleen.py":"脾","lifecycle":"肝","meridian":"经络"}

def sizhen(望=None,闻=None,问=None,切=None):
    return "%s %s %s %s" % (望 or "",闻 or "",问 or "",切 or "")

def bazheng(text):
    z={}
    z["阴阳"]="阳" if any(k in text for k in ["动","热","快","通","亮","涨"]) else "阴"
    z["表里"]="表" if any(k in text for k in ["外","接口","门","通道","口"]) else "里"
    z["寒热"]="热" if any(k in text for k in ["热","急","堵","冲","过","烧"]) else "寒"
    z["虚实"]="实" if any(k in text for k in ["堵","卡","满","堆","坏","积"]) else "虚"
    return z

def chuanbian(text):
    """★ 治未病:见肝传脾—— 找到一个脏·预判它传的下游(相克)"""
    hit=[z for o,z in ORGAN2ZANG.items() if o in text]
    out=[]
    for z in set(hit):
        nxt=KE.get(z)
        if nxt: out.append({"病脏":z,"传":nxt,"治":"当先实%s(既病防变)"%nxt})
    return out

def zhi(z, text):
    rules=[]
    rules.append("实证→消(疏解/清)" if z["虚实"]=="实" else "虚证→补(温养/填)")
    if any(k in text for k in ["堵","卡"]): rules.append("通则不痛→通滞")
    if any(k in text for k in ["过","冲"]): rules.append("过则收→镇")
    return rules


ZANG = {
 "\u5fc3": {"gong":"\u8840\u8109/\u795e\u660e","zheng":["\u60b8","\u5931\u7720","\u795e\u660f","\u70e6","\u5065\u5fd8"],"tiao":"\u517b\u5fc3\u5b89\u795e"},
 "\u809d": {"gong":"\u758f\u6cc4/\u85cf\u8840","zheng":["\u90c1","\u6012","\u810b\u75db","\u76ee\u7729","\u8c03\u5ea6","\u4e71"],"tiao":"\u758f\u809d"},
 "\u813e": {"gong":"\u8fd0\u5316/\u7edf\u8840","zheng":["\u98df\u5c11","\u8179\u80c0","\u4e4f\u529b","\u4e0d\u7a33"],"tiao":"\u5065\u813e"},
 "\u80ba": {"gong":"\u6c14/\u5ba3\u53d1","zheng":["\u54b3","\u5598","\u9f3b","\u6c14\u77ed"],"tiao":"\u5ba3\u964d"},
 "\u80be": {"gong":"\u85cf\u7cbe/\u7eb3\u6c14","zheng":["\u8170","\u8033","\u6cc4","\u6f0f","\u5931\u85cf","\u5bc6"],"tiao":"\u8865\u80be"},
}
QI_XUE = {
 "\u6c14\u865a": {"zheng":["\u4e4f\u529b","\u61d2","\u4e0d\u8db3"],"tiao":"\u8865\u6c14"},
 "\u6c14\u6ede": {"zheng":["\u5835","\u5361","\u6ede","\u95f7"],"tiao":"\u884c\u6c14"},
 "\u8840\u865a": {"zheng":["\u82cd\u767d","\u8840\u5c11","\u6de1"],"tiao":"\u8865\u8840"},
 "\u8840\u7600": {"zheng":["\u7600","\u75db\u5b9a\u70b9"],"tiao":"\u6d3b\u8840"},
 "\u6d25\u4e8f": {"zheng":["\u5e72","\u71e5","\u6e34"],"tiao":"\u751f\u6d25"},
 "\u6c34\u6e7f": {"zheng":["\u80bf","\u6e7f","\u75f0","\u6c34"],"tiao":"\u5229\u6c34\u5316\u75f0"},
}

def bingwei(text):
    hit=[]
    for z,v in ZANG.items():
        if any(k in text for k in v["zheng"]):
            hit.append({"\u75c5\u4f4d":z,"\u4e3b\u529f":v["gong"],"\u8c03":v["tiao"]})
    return hit

def bingji(text):
    hit=[]
    for k,v in QI_XUE.items():
        if any(x in text for x in v["zheng"]):
            hit.append({"\u75c5\u673a":k,"\u8c03":v["tiao"]})
    return hit

def main():
    args=dict(a.split("=",1) for a in sys.argv[1:] if "=" in a)
    text=sizhen(望=args.get("望"),闻=args.get("闻"),问=args.get("问"),切=args.get("切"))
    z=bazheng(text); r=zhi(z,text); c=chuanbian(text); bw=bingwei(text); bj=bingji(text)
    print("  四诊:",text.strip()[:60])
    print("  证(八纲):",z)
    print("  治则:",r)
    print("  病位(脏腑):",bw)
    print("  病机(气血津液):",bj)
    if c: print("  ★治未病(传变):",c)
    else: print("  ★治未病:未命中传变(需给'脏/器'关键词如liver/spleen)")
    assert z["阴阳"] in ("阴","阳") and z["虚实"] in ("虚","实")
    print("  ✅自校验: 八纲齐")
    return 0

if __name__=="__main__": sys.exit(main())
