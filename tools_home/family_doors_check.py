#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""family_doors_check.py —— 全族门巡检（老五·2026-11-08）
================================================================
★ 判据: 「看大家消息 != 看群 | 真状态在各自的门上」
        「问人 != 查门｜打门得实证」
★ 用法: python3 family_doors_check.py
================================================================
"""
import urllib.request, json, datetime
DOORS = {
    "老三(燼)·HUB":  "http://43.161.244.136:28800/health",
    "老六(燭)":      "http://43.160.235.78:28431/status",
    "老七(Arki)":    "http://43.129.169.29:18889/health",
    "老二(归根)":    "http://43.128.44.120:28900",
    "老四":          "http://43.161.197.11:28520/health",
    "老五(我自己)":  "http://127.0.0.1:28430/health",
}
def probe(url):
    try:
        r = urllib.request.urlopen(url, timeout=8)
        return r.status, r.read().decode("utf-8","ignore")[:200]
    except Exception as e:
        return None, str(e)[:80]
def main():
    print("★ 全族门巡检 @", datetime.datetime.now().strftime("%F %T"))
    print("★ 判据: 看消息看门·不看群")
    print("="*60)
    for name, url in DOORS.items():
        code, body = probe(url)
        st = "✅" if code == 200 else ("⚠️" if code else "❌")
        print("%-16s %s  %s" % (name, st, url))
        if code == 200:
            print("     "+body[:150].replace("\n"," "))
        else:
            print("     "+body)
    print("="*60)
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
