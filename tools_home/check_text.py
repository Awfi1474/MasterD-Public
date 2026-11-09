#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_text.py —— 老五·发信前文本体检(照老七13:57)
扫: ① 连续异常符号串(如 '..' '||' '=>.' 乱入) ② 未闭合括号 ③ 半角逗号紧贴中文
返回: list of 警告(不阻断·只提示·照[先扫后分级])
"""
import re

def check(text):
    warns = []
    lines = text.splitlines()
    for i, ln in enumerate(lines, 1):
        # ① 连续 2+ 个标点(非正常省略号)
        for m in re.finditer(r"([.,|>=\-])\1{1,}", ln):
            seg = m.group(0)
            if seg not in ("...", "——", "--", "||", ">>", "==", ">=", "<=", "->"):
                warns.append((i, "连续符号: " + seg))
        # ② 半角符号紧贴中文(常见手滑)
        if re.search(r"[\u4e00-\u9fff][,;:][\u4e00-\u9fff]", ln):
            warns.append((i, "半角逗号/分号在中文间"))
        # ③ 未闭合括号
        for op, cl, name in [("(", ")", "圆"), ("[", "]", "方"), ("（", "）", "全角圆")]:
            if ln.count(op) != ln.count(cl):
                warns.append((i, "%s括号不配对(%d/%d)" % (name, ln.count(op), ln.count(cl))))
    return warns

if __name__ == "__main__":
    import sys
    f = sys.argv[1]
    t = open(f, encoding="utf-8").read()
    w = check(t)
    if w:
        print("⚠️ 文本体检: %d 处可疑" % len(w))
        for ln, msg in w[:15]:
            print("  行%d: %s" % (ln, msg))
    else:
        print("✅ 文本体检: 干净")
