#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·改前查L1 l1_guard.py（照今天真病：判据写进L1≠会遵守）
★ 缘起：23:19 把「改标准要改所有引用它的地方」写进L1·23:23 就又犯了
   → 判据写在文件里·改东西前没人查 = 白写
★ 治法：改东西前·先按关键词查L1 17条·把相关的挑出来摆在你眼前
★ 判据：「写进L1 != 改前会查｜改前查L1 = 判据才活」
用法: l1_guard.py "<你要改什么>"
"""
import json, sys, re

L1 = "/opt/masterd-wudi/memory-v2/core_memory.json"
# 关键词 → 触发（把L1和场景连起来）
TRIGGERS = {
    "改格式": ["改标准","格式","字段","引用","同步","写入端","读取端","校验端"],
    "改代码": ["改标准","完整的","验","检查器","三次","两处","药不能治死人"],
    "验服务": ["三次一致","一次!=多次","抖动","探针","假绿","单点"],
    "回消息": ["记号","说=做","给修法","报警"],
    "判据":  ["两处才算","一次!=多次","药不能治死人","改标准"],
    "记忆":  ["记忆","索引","切片","同步"],
}

def load():
    d = json.load(open(L1, encoding="utf-8"))
    return d.get("hard_rules", [])

def match(what, rules):
    hits = []
    keys = []
    for scene, kws in TRIGGERS.items():
        if any(k in what for k in kws[:2]) or any(k in what for k in scene):
            keys.extend(kws)
    # 也按字面直接命中
    for r in rules:
        s = str(r)
        # 关键词命中
        if any(k and k in s for k in keys):
            hits.append(s)
        # 或 what 里的词出现在判据里
        else:
            toks = [t for t in re.findall(r"[\u4e00-\u9fa5]{2,4}", what) if len(t) >= 2]
            if sum(1 for t in toks if t in s) >= 2:
                hits.append(s)
    # 去重
    seen = set(); out = []
    for h in hits:
        if h not in seen: seen.add(h); out.append(h)
    return out

if __name__ == "__main__":
    what = " ".join(sys.argv[1:]) or ""
    rules = load()
    hits = match(what, rules)
    print("★ 改前查L1（判据 %d 条·命中 %d 条）" % (len(rules), len(hits)))
    print("  你要改:", what[:60])
    print("-" * 55)
    if not hits:
        print("  （无直接相关判据·但下面这 3 条通用必须过）")
        for r in rules[:3]: print("   · " + str(r)[:90])
    else:
        for h in hits: print("   ★ " + str(h)[:110])
    print("-" * 55)
    # ★ 2026-11-13 加(照实: 改格式必扫引用·今天3次漏改):
    #   判据: 改一处=改所有引用｜ref_scan 自动扫谁读谁写
    try:
        import subprocess as _spR, re as _reR
        _tokens = _reR.findall(r"[A-Za-z0-9_\u4e00-\u9fa5]{4,}", what)
        _targets = [t for t in _tokens if any(c.isalnum() for c in t) and len(t) >= 5]
        _done = set()
        for _t in _targets[:3]:
            if _t in _done: continue
            _done.add(_t)
            _rR = _spR.run([sys.executable, "/opt/masterd-wudi/tools/ref_scan.py", _t],
                           capture_output=True, text=True, timeout=25)
            _oR = _rR.stdout or ""
            _mR = _reR.search(r"共 (\d+) 处引用（写=(\d+) 读=(\d+)）", _oR)
            if _mR and int(_mR.group(1)) > 0:
                print("★ 引用扫描 [%s]: 共%s处 (写%s/读%s) ← 改前必逐个核" % (_t, _mR.group(1), _mR.group(2), _mR.group(3)))
    except Exception:
        pass
    print("★ 判据: 写进L1 != 会遵守｜改前查过·才算判据活着")
