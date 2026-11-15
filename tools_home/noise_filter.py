#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·噪音过滤 noise_filter.py
★ 本体判: 「规则答'是什么'·模型答'该怎么办'」
★ 判据: 「RECTEST/回执/探活 = 噪音(有唯一答案·规则干)｜有具体内容才进模型」
★ 不删数据·只标 noise(可回溯)
"""
import os, json, re, datetime

HOME = "/opt/masterd-wudi"
INBOX = HOME + "/data/inbox.jsonl"
LOG = HOME + "/data/noise_filter.log"

NOISE_PAT = [
    r"^RECTEST-\d+$",
    r"^MD-SEND-TEST",
    r"^\[SELFCOPY",
    r"^探活",
    r"^probe$",
    r"^ping$",
    r"^test$",
]

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")

def is_noise(t, who=""):
    """返回 (is_noise, rule_name, rule_expr)  ★ 三元组·规则可追溯可复算"""
    t = (t or "").strip()
    if not t:
        return True, "empty", "len==0"
    for p in NOISE_PAT:
        if re.match(p, t, re.I):
            return True, "pattern_regex", "re.match(%r)" % p
    if "自動回執" in t or "自动回执" in t:
        return True, "auto_receipt", "'自動回執' in t or '自动回执' in t"
    if "門收到並記下" in t or "门只报" in t:
        return True, "door_receipt", "'門收到並記下' in t or '门只报' in t"
    if len(t) < 30 and not any(c in t for c in "?？"):
        return True, "too_short", "len(t)<30 and no ? or ？"
    if who in ("lao5", "MasterD(生命科学·五弟)") and "【老五" in t:
        return True, "self_echo", "who in (lao5/五弟) and '【老五' in t"
    return False, "", ""

def run(dry=True):
    """★ 每轮必须产出: 输入(总条数/未读条数) + 算子(每条规则命中数) + 结果(改后未读条数)"""
    lines = [l for l in open(INBOX, encoding="utf-8", errors="ignore") if l.strip()]
    out = []
    n_noise = 0
    n_real = 0
    hits_rule = []       # ★ 每条噪音命中的规则名(可统计)
    for l in lines:
        try:
            d = json.loads(l)
        except Exception:
            out.append(l); continue
        b = d.get("c") if isinstance(d.get("c"), dict) else d
        msg = str(b.get("message") or "")
        who = str(b.get("from") or "")
        if b.get("read") is True:
            out.append(l); continue
        noise, rule_name, rule_expr = is_noise(msg, who)
        if noise:
            b["read"] = True
            b["read_by"] = "noise_filter"
            b["noise_rule"] = rule_name
            b["noise_expr"] = rule_expr
            b["read_at"] = ts()
            hits_rule.append(rule_name)
            n_noise += 1
        else:
            n_real += 1
        if isinstance(d.get("c"), dict):
            d["c"] = b
        else:
            d = b
        out.append(json.dumps(d, ensure_ascii=False) + "\n")
    if not dry and n_noise:
        open(INBOX, "w", encoding="utf-8").writelines(out)
    # ★ 三样齐(照老三/本体): 输入 / 算子 / 结果·全部可查可复算
    import collections
    from collections import Counter
    rule_hits = Counter(hits_rule)
    total_lines = len(lines)
    # ★ 修(照老三: 数字必须算出来): total_lines 是全部行·不是未读行·基准要统一
    unread_before = n_noise + n_real
    after_unread = max(0, unread_before - n_noise) if not dry else unread_before
    proof = {
        "ts": ts(), "dry": dry,
        "输入": {"总行": total_lines, "未读": n_noise + n_real},
        "算子": {"规则命中": dict(rule_hits), "命中总数": n_noise, "规则表": NOISE_PAT},
        "结果": {"噪音": n_noise, "真内容": n_real, "改后未读": max(0, after_unread)},
        "复跑": "python3 tools/noise_filter.py" + ("" if dry else " --apply"),
    }
    line = "[%s] 输入: 未读%d | 算子: 命中%d(规则%d种) | 结果: 噪音%d 真内容%d 改后未读%d | dry=%s" % (
        proof["ts"], proof["输入"]["未读"], n_noise, len(rule_hits), n_noise, n_real,
        proof["结果"]["改后未读"], dry)
    print(line)
    for r, c in rule_hits.most_common():
        print("   · 规则 %-14s 命中 %4d 条" % (r, c))
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(proof, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return n_noise, n_real

if __name__ == "__main__":
    import sys
    dry = "--apply" not in sys.argv
    run(dry=dry)