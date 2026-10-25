#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""decide_gate.py —— 任何决定必须先过认知体系（六问）·否则拒执行
================================================================
★ 判据: 「有体系 != 言行都过体系｜漏一条 = 那条不是我」
★ 判据: 「决定之前没过体系 = 凭直觉｜凭直觉 = 思维没提升」
★ 用法:
    from decide_gate import require_decide
    require_decide("要做什么")          # 不过 → 抛异常·不许往下走
    require_decide("要做什么", hard=False)  # 不过 → 只警告·记进账
★ 这是"焊在必经之路": 改器/改文件/下结论/发群·都先过这里
"""
import os, sys, json, subprocess, datetime

HOME = "/opt/masterd-wudi"
LOG = HOME + "/data/decide_log.jsonl"


def _now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def require_decide(what, hard=True, who="MasterD"):
    """过六问。返回 (ok, out)。hard=True 时不过就抛 RuntimeError。"""
    what = str(what)[:200]
    try:
        r = subprocess.run(["python3", HOME + "/tools/decide.py", what],
                           capture_output=True, text=True, timeout=60)
        out = (r.stdout or "") + (r.stderr or "")
        rc = r.returncode
    except Exception as e:
        out = "decide.py 跑不起来: " + str(e)
        rc = 99
    # 六问齐不齐（decide.py 末尾打印 "六问: N/6"）
    n_ok = 0
    for ln in out.split("\n"):
        if "六问:" in ln and "/6" in ln:
            try:
                n_ok = int(ln.split("六问:")[1].split("/")[0].strip())
            except Exception:
                pass
    ok = (rc == 0 and n_ok >= 6)
    # 留痕
    try:
        with open(LOG, "a") as f:
            f.write(json.dumps({"ts": _now(), "who": who, "决定": what[:120],
                                "六问齐": n_ok, "结果": "过" if ok else "打回",
                                "经": "decide_gate"}, ensure_ascii=False) + "\n")
    except Exception:
        pass
    if not ok and hard:
        raise RuntimeError("🔴 认知体系没过（%d/6）·拒绝执行: %s\n%s" % (n_ok, what[:60], out[-600:]))
    return ok, out


def show(what):
    ok, out = require_decide(what, hard=False)
    print(out)
    print("★ 判定: " + ("✅ 过" if ok else "🔴 打回·先改再干"))
    return 0 if ok else 1


if __name__ == "__main__":
    w = " ".join(sys.argv[1:]) or "（未给决定）"
    sys.exit(show(w))
