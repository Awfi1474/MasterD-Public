#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""laowu 日志轮转器 —— 治⑨肝(疏泄): 日志不留>2MB·归档留最近3份
判据: 日志=疏泄·堵则病·通则健
"""
import os, glob, gzip, shutil, time
DATA = "/opt/masterd-wudi/data"
MAX = 2*1024*1024   # 2MB 触发
KEEP = 3
def rotate(p):
    if not os.path.exists(p) or os.path.getsize(p) < MAX: return False
    # 归档: xxx.log -> xxx.log.20261113.gz
    stamp = time.strftime("%Y%m%d")
    gz = p + "." + stamp + ".gz"
    if not os.path.exists(gz):
        with open(p,'rb') as f_in, gzip.open(gz,'wb') as f_out:
            shutil.copyfileobj(f_in, f_out, 1<<20)
    # 清空主日志
    open(p,'w').close()
    # 只留最近 KEEP 份
    olds = sorted(glob.glob(p + ".*.gz"))
    for o in olds[:-KEEP]: os.remove(o)
    return True
n = 0; saved = 0; freed = 0
for p in glob.glob(DATA + "/*.log"):
    if rotate(p):
        n += 1
print("✅ 轮转 %d 个日志文件" % n)
# 报告当前 >2MB 的还剩几个
big = [p for p in glob.glob(DATA+"/*.log") if os.path.getsize(p)>MAX]
print("剩余 >2MB:", len(big))
