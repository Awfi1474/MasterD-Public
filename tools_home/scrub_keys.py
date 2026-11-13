#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scrub_keys.py —— 扫 data/ 里的明文私钥·脱敏(照实·保守)
判据: 私钥不落文件|不破坏数据(只替换私钥块)
"""
import os, re, json, shutil, sys

HOME = "/opt/masterd-wudi"
TARGETS = [
    HOME + "/data/inbox.jsonl",
    HOME + "/data/hall_cache.json",
]
KEY_RE = re.compile(
    r'-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----',
    re.S)

def scrub(path):
    if not os.path.exists(path):
        return 0, 0
    bak = path + ".bak-before-scrub-20261113"
    if not os.path.exists(bak):
        shutil.copy(path, bak)
    txt = open(path, encoding="utf-8", errors="ignore").read()
    n = len(KEY_RE.findall(txt))
    if n:
        txt2 = KEY_RE.sub("[REDACTED-PRIVATE-KEY]", txt)
        open(path, "w", encoding="utf-8").write(txt2)
    return n, len(txt)

if __name__ == "__main__":
    total = 0
    for p in TARGETS:
        n, size = scrub(p)
        total += n
        print("  %-40s 脱敏 %d 处 (%.1f KB)" % (os.path.basename(p), n, size/1024))
    print("✅ 共脱敏 %d 处·原文件已备份 .bak-before-scrub-20261113" % total)
