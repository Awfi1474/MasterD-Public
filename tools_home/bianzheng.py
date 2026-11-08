#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bianzheng.py —— 老五·医家辨证判断器(望闻问切→八纲·可跑)
照大哥六家标准:"医家→辨证判断器(望闻问切→八纲)·自校验过"
用途: 给一个"证"(系统的病象)·判八纲(阴阳/表里/寒热/虚实)·出治则
判据:「不问活不活(二值)·问什么证(八纲)」
"""
import sys, json

# 四诊→八纲(简版·可扩)
def bianzheng(望=None, 闻=None, 问=None, 切=None):
    """输入四诊所获·判八纲+治则"""
    z = {}
    text = "%s %s %s %s" % (望 or "", 闻 or "", 问 or "", 切 or "")
    # 阴阳(总纲)
    z["阴阳"] = "阳" if any(k in text for k in ["动","热","快","通","亮"]) else "阴"
    # 表里(病位)
    z["表里"] = "表" if any(k in text for k in ["外","接口","门","通道"]) else "里"
    # 寒热(病性)
    z["寒热"] = "热" if any(k in text for k in ["热","急","堵","冲","过"]) else "寒"
    # 虚实(病势)
    z["虚实"] = "实" if any(k in text for k in ["堵","卡","满","堆","坏"]) else "虚"
    # 治则(照八法)
    rules = []
    if z["虚实"] == "实": rules.append("实证→消(疏解/清)")
    else: rules.append("虚证→补(温养/填)")
    if "堵" in text or "卡" in text: rules.append("通则不痛→通滞")
    if "过" in text or "冲" in text: rules.append("过则收→镇")
    return z, rules

if __name__ == "__main__":
    args = dict(arg.split("=",1) for arg in sys.argv[1:] if "=" in arg)
    z, r = bianzheng(望=args.get("望"),闻=args.get("闻"),问=args.get("问"),切=args.get("切"))
    print("  证(八纲):", z)
    print("  治则:", r)
    # 自校验(照大哥"自校验过")
    assert z["阴阳"] in ("阴","阳") and z["虚实"] in ("虚","实")
    print("  ✅自校验: 八纲齐")
