#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·医的诊断尺 checkup_std.py
★ 董事长问：「你哪一门学透了？」→ 照实：没一门透·医最弱（没被验过）
★ 现状: cases/CASES.jsonl 是「别人消息改名成病例」·不是真诊断
★ 做法: 立「体检判据」——把「什么算病·怎么判·谁验」写清·可被第三方调
★ 判据(我自己): 「没判据的体检 = 只报数不诊病」
★ 依据: 我原有的「体检9项」（轴在/环转/呼吸比/会回/认得出/记得住/能验/签名/今天长）
"""
import os
import json
import datetime

HOME = "/opt/masterd-wudi"
STD = HOME + "/data/checkup_standard.json"
LOG = HOME + "/data/checkup_diag.jsonl"

# ★ 体检 9 项的判据（哪项·怎么判·什么算病·怎么验）
CHECKUP_9 = [
    {"n": 1, "项": "轴在", "判据": "主进程活着 + 端口 200",
     "什么算病": "进程不在 或 端口非 200", "怎么验": "pgrep + curl /health"},
    {"n": 2, "项": "环转", "判据": "心跳在更新（时间戳 < 2×周期）",
     "什么算病": "心跳停了 > 2 倍周期", "怎么验": "看 heartbeat 文件 mtime"},
    {"n": 3, "项": "呼吸比", "判据": "收/发 都有账",
     "什么算病": "只有收没有发（或反之）", "怎么验": "inbox 行数 vs send_ledger 行数"},
    {"n": 4, "项": "会回", "判据": "收到后能回（不哑火）",
     "什么算病": "门回 200 但本体不回", "怎么验": "发一条·看是否有非门回执"},
    {"n": 5, "项": "认得出", "判据": "身份档可读 + 地址一致",
     "什么算病": "身份档缺 或 地址对不上", "怎么验": "读 agent-id + 比 addr"},
    {"n": 6, "项": "记得住", "判据": "记忆库可读 + 有新增",
     "什么算病": "库损坏 或 长期无新增", "怎么验": "sqlite 读 + 看最新 ts"},
    {"n": 7, "项": "能验", "判据": "有对外可查的口（别人能拉）",
     "什么算病": "只能自证（没有对外口）", "怎么验": "curl 公开口"},
    {"n": 8, "项": "签名", "判据": "发出带签 且 别家能验",
     "什么算病": "无签 或 验不过", "怎么验": "recover == address"},
    {"n": 9, "项": "今天长", "判据": "今天有真实产出（发信/改器/验）",
     "什么算病": "一天无产出（空转）", "怎么验": "看今日账"},
]


def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")


def write_std():
    """把「体检判据」写成标准·可被第三方拿"""
    doc = {
        "name": "老五·体检判据（医的尺）",
        "version": "v1",
        "frozen_at": ts(),
        "authority": "老五原有「体检9项」（董事长令 2026-10-08 定的）",
        "判据总纲": "没判据的体检 = 只报数不诊病",
        "九项": CHECKUP_9,
        "怎么被别人验": "别人照我的判据·跑我的口·看结果对不对得上",
        "验证口": [
            "GET /health（轴在/环转）",
            "GET /unread + /tasks（呼吸比）",
            "GET /claims（能验）",
            "GET /signed（签名）",
        ],
        "更新": ts(),
    }
    os.makedirs(os.path.dirname(STD), exist_ok=True)
    json.dump(doc, open(STD, "w"), ensure_ascii=False, indent=1)
    return doc


if __name__ == "__main__":
    d = write_std()
    print("✅ 体检判据 -> %s" % STD)
    print("总纲:", d["判据总纲"])
    print()
    for x in CHECKUP_9:
        print("  %d. %-6s 判据: %s" % (x["n"], x["项"], x["判据"]))
        print("       病: %s" % x["什么算病"])
    print()
    print("可被验的口:", ", ".join(d["验证口"]))