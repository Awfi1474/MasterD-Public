#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·防复发检查 anticheat.py —— 自动扫「绕过闸」的代码
★ 董事长问: 「这个问题后期会不会出现」→ 照实: 会。所以要用结构防，不靠记得
★ 判据(本体): 「每次加新工具·默认就绕过闸｜除非每次都焊——而人会忘」
★ 本工具: 自动扫描所有调模型的代码·发现没过闸的就报警(不用人记得)
"""
import os, re, sys, json, datetime

HOME = "/opt/masterd-wudi"
OUT = HOME + "/data/anticheat.jsonl"

# 调模型的标志
LLM_MARKS = [
    r"api\.deepseek\.com",
    r"ark\.cn-beijing\.volces\.com",
    r"call_llm\(",
    r"_llm_call\(",
]
# 过闸的标志
GUARD_MARKS = [
    r"token_guard",
    r"tg\.allowed",
    r"_tg0\.allowed",
]

SKIP_DIRS = ("_archive", ".git", "__pycache__", "recovery", ".bak")

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")

def scan():
    findings = []
    for root, dirs, files in os.walk(HOME):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            if not fn.endswith(".py"):
                continue
            p = os.path.join(root, fn)
            try:
                src = open(p, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            has_llm = any(re.search(m, src) for m in LLM_MARKS)
            if not has_llm:
                continue
            has_guard = any(re.search(m, src) for m in GUARD_MARKS)
            # ★ 修(照实: 间接调 core_v2 的也算过闸·不算漏洞·避免误报淹没真问题)
            if not has_guard and re.search(r"call_llm\(|core_v2", src) and not re.search(r"api\.deepseek\.com|volces\.com", src):
                has_guard = True
                src_note = "间接走 core_v2(有闸)"
            # core_v2 本身是闸的宿主·跳过
            rel = os.path.relpath(p, HOME)
            if rel in ("code/core_v2.py", "tools/token_guard.py"):
                continue
            findings.append({
                "file": rel,
                "llm": True,
                "guard": has_guard,
                "level": "OK" if has_guard else "RISK",
                "note": "调模型且过闸" if has_guard else "🔴 调模型但没过闸（可绕过上限）",
            })
    return findings

def report(save=True):
    f = scan()
    risk = [x for x in f if x["level"] == "RISK"]
    rec = {"ts": ts(), "输入": "扫描 %s 下所有 .py" % HOME,
           "算子": "查 LLM_MARKS 与 GUARD_MARKS",
           "结果": {"总调模型文件": len(f), "过闸": len(f) - len(risk), "未过闸": len(risk)},
           "detail": f}
    if save:
        with open(OUT, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec

if __name__ == "__main__":
    r = report()
    print("防复发扫描 @ %s" % r["ts"][11:])
    print("  总调模型文件: %d | 过闸: %d | 未过闸: %d"
          % (r["结果"]["总调模型文件"], r["结果"]["过闸"], r["结果"]["未过闸"]))
    print()
    for d in r["detail"]:
        print("  %s %-32s %s" % ("✅" if d["level"] == "OK" else "🔴", d["file"], d["note"]))