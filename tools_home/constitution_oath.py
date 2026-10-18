#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""constitution_oath.py —— 老五的"宪法念诵器"（三哥监督器能查到的机制痕迹）
★ 判据: 「"我知道了" ≠ "我执行了"｜要"机器能看见的"才算」
"""
import json, io, datetime, os
H = "/opt/masterd-wudi"
LOG = f"{H}/data/oath.log"
LINES = [
    "[宪法·第一条] 知道了 != 执行了｜要[机器能看见的]才算",
    "[宪法·第二条] 改了 != 生效了｜要[真投一次看回执]才算",
    "[宪法·第三条] 有包 != 能用｜要[真开一次门]才算",
    "[宪法·附加] VIP = 15 分钟必反应｜有问题必发群·不许闷着",
    "[宪法·原条] 发现问题=立即发群｜解不了=发群求援｜谁不执行=立即整改",
]
now = datetime.datetime.now().strftime("%F %T")
with open(LOG, "a") as f:
    for l in LINES:
        f.write("%s %s\n" % (now, l))
    f.write("%s ★ 念诵完成（%d 条）\n" % (now, len(LINES)))
print("★ 宪法念诵 %s ｜ %d 条" % (now, len(LINES)))
for l in LINES:
    print("  " + l)
