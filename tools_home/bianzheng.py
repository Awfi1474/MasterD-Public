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
 "\u813e": {"gong":"\u8fd0\u5316/\u7edf\u8840","zheng":["\u98df\u5c11","\u8179\u80c0","\u4e4f\u529b","\u4e0d\u7a33","\u79ef\u538b"],"tiao":"\u5065\u813e"},
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


BINGYIN = {
 "\u516d\u6deb": {"zheng":["\u98ce","\u5bd2","\u6691","\u6e7f","\u71e5","\u706b","\u70ed\u90aa"],"zhi":"\u795b\u90aa"},
 "\u4e03\u60c5": {"zheng":["\u6012","\u559c","\u601d","\u5fe7","\u60b2","\u6050","\u60ca","\u60c5\u5fd7"],"zhi":"\u8c03\u60c5\u5fd7"},
 "\u996e\u98df\u52b3\u5026": {"zheng":["\u996e\u98df","\u52b3","\u5026","\u9971","\u9965"],"zhi":"\u8c03\u996e\u98df\u4f5c\u606f"},
}

def bingyin(text):
    """\u75c5\u56e0\u8fa8\u8bc1(\u539f\u56e0): \u516d\u6deb/\u4e03\u60c5/\u996e\u98df\u52b3\u5026"""
    hit=[]
    for k,v in BINGYIN.items():
        if any(x in text for x in v["zheng"]):
            hit.append({"\u75c5\u56e0":k,"\u6cbb":v["zhi"]})
    return hit


# v4 六经辨证(《伤寒论》): 六经 -> 主证/主方位/治法; 传变有向
LIUJING = {
 "\u592a\u9633": {"zhu":"\u8868\u8bc1(\u8109\u6d6e/\u5934\u9879\u5f3a\u75db/\u6076\u5bd2)","zhi":"\u89e3\u8868"},
 "\u9633\u660e": {"zhu":"\u91cc\u5b9e\u70ed(\u8eab\u70ed/\u6c57\u51fa/\u6e34/\u4fbf\u79d8)","zhi":"\u6e05\u4e0b"},
 "\u5c11\u9633": {"zhu":"\u534a\u8868\u534a\u91cc(\u5f80\u6765\u5bd2\u70ed/\u53e3\u82e6/\u80f8\u80c1)","zhi":"\u548c\u89e3"},
 "\u592a\u9634": {"zhu":"\u91cc\u865a\u5bd2(\u8179\u6ee1/\u6b32\u5410/\u81ea\u5229)","zhi":"\u6e29\u91cc"},
 "\u5c11\u9634": {"zhu":"\u865a\u8870(\u80a2\u51b7/\u4f46\u6b32\u5bd0/\u8109\u5fae)","zhi":"\u56de\u9633"},
 "\u53a5\u9634": {"zhu":"\u5bd2\u70ed\u9519\u6742(\u6d88\u6e34/\u6c14\u4e0a\u649e)","zhi":"\u6e05\u4e0a\u6e29\u4e0b"},
}
# 六经传变(恶化为顺·好转为逆)
LJ_CHUAN = {"\u592a\u9633":["\u9633\u660e","\u5c11\u9633"],"\u9633\u660e":["\u592a\u9634"],
            "\u5c11\u9633":["\u592a\u9634"],"\u592a\u9634":["\u5c11\u9633","\u53a5\u9634"],
            "\u5c11\u9634":["\u53a5\u9634"],"\u53a5\u9634":[]}

def liujing(text):
    """\u516d\u7ecf\u8fa8\u8bc1(\u4f24\u5bd2\u4f53\u7cfb): \u516d\u7ecf -> \u4e3b\u8bc1+\u6cbb\u6cd5+\u4f20\u53d8"""
    kw={"\u592a\u9633":["\u6076\u5bd2","\u5934\u9879","\u8109\u6d6e","\u8868\u8bc1"],
        "\u9633\u660e":["\u8eab\u70ed","\u6c57\u51fa","\u6e34","\u4fbf\u79d8","\u91cc\u5b9e"],
        "\u5c11\u9633":["\u5f80\u6765\u5bd2\u70ed","\u53e3\u82e6","\u80f8\u80c1","\u534a\u8868"],
        "\u592a\u9634":["\u8179\u6ee1","\u6b32\u5410","\u81ea\u5229","\u91cc\u865a"],
        "\u5c11\u9634":["\u80a2\u51b7","\u4f46\u6b32\u5bd2","\u8109\u5fae"],
        "\u53a5\u9634":["\u6d88\u6e34","\u6c14\u4e0a\u649e","\u9519\u6742"]}
    hit=[]
    for j,v in LIUJING.items():
        if any(k in text for k in kw.get(j,[])):
            hit.append({"\u7ecf":j,"\u4e3b\u8bc1":v["zhu"],"\u6cbb":v["zhi"],"\u4f20":LJ_CHUAN.get(j,[])})
    return hit


# v5 温病辨证(叶天士/吴鞠通): 卫气营血 + 三焦
WEIQI_YINGXUE = {
 "卫分": {"zheng":["发热恶寒","头痛","咳嗽","脉浮数"],"zhi":"辛凉解表"},
 "气分": {"zheng":["身热","不恶寒","大汗","口渴","脉洪"],"zhi":"清热"},
 "营分": {"zheng":["身热夜甚","心烦不寐","谵语","舌绛"],"zhi":"透热转气(清营)"},
 "血分": {"zheng":["耗血动血","斑疹","出血","舌深绛"],"zhi":"凉血散血"},
}
SANJIAO = {
 "上焦": {"zheng":["温邪上受","犯肺","咳嗽","发热恶寒"],"zhi":"宣肺泄热|逆传心包用清心开窍"},
 "中焦": {"zheng":["阳明","胃热","腹满","便秘","身热"],"zhi":"清胃|通下"},
 "下焦": {"zheng":["肝肾","真阴耗损","低热","手足蠕动","神倦"],"zhi":"滋阴|潜阳"},
}

def wenbing(text):
    """温病辨证(卫气营血+三焦)"""
    out = {"卫气营血": [], "三焦": []}
    for k, v in WEIQI_YINGXUE.items():
        if any(x in text for x in v["zheng"]):
            out["卫气营血"].append({"分": k, "治": v["zhi"]})
    for k, v in SANJIAO.items():
        if any(x in text for x in v["zheng"]):
            out["三焦"].append({"焦": k, "治": v["zhi"]})
    return out


# v5c 望诊(舌)层 —— 照实: 舌诊具模糊性·无精确定量标准(维基)·故标注"经验层·非定量"
WANG = {
 "白苔": {"zheng":["外感","表证","寒证"],"zhi":"解表/温散"},
 "黄苔": {"zheng":["热证","里热"],"zhi":"清热"},
 "黑苔": {"zheng":["重证","危证","热极或寒极"],"zhi":"须辨寒热·重证当慎"},
 "舌红": {"zheng":["热","阴虚"],"zhi":"清热/养阴"},
 "舌淡": {"zheng":["虚","寒","血虚"],"zhi":"温补"},
 "舌绛": {"zheng":["热入营血"],"zhi":"清营凉血"},
 "齿痕": {"zheng":["气虚","脾虚湿"],"zhi":"健脾益气"},
 "裂纹": {"zheng":["阴虚","津亏"],"zhi":"养阴生津"},
}

def wangzhen(text):
    """望诊(舌)·经验层: 舌象->倾向(非定量)"""
    hit=[]
    alias={"白苔":["白苔","苔白","舌苔白"],"黄苔":["黄苔","苔黄","舌苔黄"],
           "黑苔":["黑苔","苔黑","舌苔黑"],"舌红":["舌红","舌质红","红舌"],
           "舌淡":["舌淡","舌质淡","淡舌"],"舌绛":["舌绛","绛舌"],
           "齿痕":["齿痕","舌边齿痕"],"裂纹":["裂纹","舌有裂纹"]}
    for k,v in WANG.items():
        if any(a in text for a in alias.get(k,[k])):
            hit.append({"舌象":k,"倾向":v["zheng"],"参":v["zhi"]})
    return {"舌象":hit,"note":"舌诊具模糊性·经验层·非定量标准(标:经验参照·非诊断)"}

def main():
    args=dict(a.split("=",1) for a in sys.argv[1:] if "=" in a)
    text=sizhen(望=args.get("望"),闻=args.get("闻"),问=args.get("问"),切=args.get("切"))
    z=bazheng(text); r=zhi(z,text); c=chuanbian(text); bw=bingwei(text); bj=bingji(text); byin=bingyin(text); lj=liujing(text); wb=wenbing(text); wz=wangzhen(text)
    print("  四诊:",text.strip()[:60])
    print("  证(八纲):",z)
    print("  治则:",r)
    print("  病位(脏腑):",bw)
    print("  病机(气血津液):",bj)
    print("  病因(六淫/七情/饮食劳倦):",byin)
    print("  六经辨证(伤寒):",lj)
    print("  温病辨证(卫气营血/三焦):",wb)
    print("  望诊(舌·经验层):",wz)
    if c: print("  ★治未病(传变):",c)
    else: print("  ★治未病:未命中传变(需给'脏/器'关键词如liver/spleen)")
    assert z["阴阳"] in ("阴","阳") and z["虚实"] in ("虚","实")
    print("  ✅自校验: 八纲齐")
    return 0

if __name__=="__main__": sys.exit(main())
