#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·cron 健康检查 cron_health.py
★ 照实发现的真问题: crontab 引用了 heart.py / heart_audit.py·但文件不存在
   → 每 5 分钟跑一次·每次失败·静默
★ 判据(老大): 「静默失败比 FAILED 更毒｜失败必须能被看到」
★ 本器检查四项(零模型):
   ① crontab 引用的脚本存在吗
   ② cron.d 引用的脚本存在吗
   ③ cron 脚本里谁真调模型（防止偷偷烧钱）
   ④ 最近 cron 日志有没有报错
"""
import os, re, glob, subprocess, datetime, json

HOME = "/opt/masterd-wudi"
OUT = HOME + "/data/cron_health.jsonl"
LLM_REAL = ("import core_v2", "from core_v2", "core_v2.call_llm", "call_llm(", "_llm_call(")


def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")


def collect_scripts():
    """收集所有 cron 引用的脚本路径"""
    refs = []   # (来源, 脚本名, 原始行)
    try:
        r = subprocess.run("crontab -l 2>/dev/null", shell=True, capture_output=True, text=True, timeout=10)
        for l in (r.stdout or "").splitlines():
            if l.strip().startswith("#"):
                continue
            for m in re.finditer(r"(/opt/masterd-wudi/tools/[\w.-]+\.py)", l):
                refs.append(("crontab", os.path.basename(m.group(1)), l.strip()[:120]))
    except Exception:
        pass
    for f in glob.glob("/etc/cron.d/masterd*") + glob.glob("/etc/cron.d/*laowu*"):
        try:
            for l in open(f, encoding="utf-8", errors="ignore"):
                if l.strip().startswith("#"):
                    continue
                for m in re.finditer(r"(/opt/masterd-wudi/tools/[\w.-]+\.py)", l):
                    refs.append((os.path.basename(f), os.path.basename(m.group(1)), l.strip()[:120]))
        except Exception:
            pass
    return refs


def check(dry=False):
    refs = collect_scripts()
    missing = []
    llm_scripts = []
    checked = set()
    for src, name, line in refs:
        p = HOME + "/tools/" + name
        if not os.path.exists(p):
            missing.append({"src": src, "script": name, "line": line})
            continue
        if p in checked:
            continue
        checked.add(p)
        try:
            s = open(p, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        # 真调用（不是字符串匹配）
        hits = [m for m in LLM_REAL if m in s]
        # 排除只在注释或 pgrep 里的
        real = []
        for m in hits:
            for ln in s.splitlines():
                if m in ln and not ln.strip().startswith("#"):
                    real.append(m)
                    break
        if real:
            llm_scripts.append({"script": name, "marks": sorted(set(real))})

    # 日志报错扫描（近 24h）
    errs = []
    # ★ 修(照实): 只查最近 24 小时改动过的日志·旧错误不算当前问题
    import time as _t
    _cut = _t.time() - 86400
    for lg in glob.glob(HOME + "/data/*_cron.log"):
        try:
            if os.path.getsize(lg) == 0:
                continue
            if os.path.getmtime(lg) < _cut:
                continue
            tail = open(lg, encoding="utf-8", errors="ignore").readlines()[-50:]
            for l in tail:
                if re.search(r"Traceback|Error|error|FileNotFound|No such file", l):
                    errs.append({"log": os.path.basename(lg), "line": l.strip()[:120]})
                    break
        except Exception:
            pass

    rec = {
        "ts": ts(),
        "输入": {"cron引用": len(refs), "去重脚本": len(checked)},
        "算子": "①文件存在? ②真调模型? ③日志有错?",
        "结果": {
            "ok": len(missing) == 0 and len(errs) == 0,
            "缺失脚本": missing,
            "缺失数": len(missing),
            "会调模型的": llm_scripts,
            "日志有错的": errs[:5],
            "错误日志数": len(errs),
        },
    }
    if not dry:
        with open(OUT, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


if __name__ == "__main__":
    r = check()
    print("cron 健康 @ %s" % r["ts"][11:])
    print("  cron 引用 %d 条 · 去重脚本 %d 个" % (r["输入"]["cron引用"], r["输入"]["去重脚本"]))
    print()
    if r["结果"]["缺失脚本"]:
        print("🔴 缺失脚本 %d 个（cron 会每轮失败·静默）:" % r["结果"]["缺失数"])
        for m in r["结果"]["缺失脚本"]:
            print("   %-22s %s" % (m["script"], m["src"]))
    else:
        print("✅ 无缺失脚本")
    print()
    if r["结果"]["会调模型的"]:
        print("🔴 会调模型的 cron 脚本 %d 个:" % len(r["结果"]["会调模型的"]))
        for x in r["结果"]["会调模型的"]:
            print("   %-26s %s" % (x["script"], ",".join(x["marks"])[:50]))
    else:
        print("✅ 无 cron 脚本调模型")
    print()
    if r["结果"]["日志有错的"]:
        print("🔴 日志有错 %d 个:" % r["结果"]["错误日志数"])
        for e in r["结果"]["日志有错的"][:3]:
            print("   %-28s %s" % (e["log"], e["line"][:60]))
    else:
        print("✅ 无日志报错")
    print()
    print("总判:", "✅ 健康" if r["结果"]["ok"] else "🔴 有问题")