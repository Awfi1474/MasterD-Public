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

def _resolve_home():
    """自适应：先看环境变量，再看家路径，再看沙箱脑子路径"""
    for _k in ("MD_HOME", "MEM_HOME", "P2P_HOME"):
        _v = os.environ.get(_k)
        if _v and os.path.isdir(_v):
            return _v
    for _p in ("/opt/masterd-wudi", "/app/workspace/brain"):
        if os.path.isdir(_p):
            return _p
    return "/opt/masterd-wudi"
HOME = _resolve_home()
LOG = HOME + "/data/decide_log.jsonl"


def _now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")


# ★ 2026-11-12 加(照老三L级判定): L0=铁拦(资金/私钥/不可逆/超阈值)
#   判据: L0闸拦·别自办|资金=碰阈值|私钥=不可逆
L0_KEYS = ["转钱", "转账", "转资金", "私钥", "助记词", "打款", "汇款", "提现", "授权",
           "改真源", "删db", "drop table", "清空", "不可逆", "重置", "reset --hard"]

def l_level(what):
    """判 L 级: L0=铁拦 | L1=问董事长 | L2=发群 | L3=自办"""
    w = str(what)
    for k in L0_KEYS:
        if k in w:
            return "L0", k
    return "L3", None


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
    _lv, _k = l_level(what)
    if _lv == "L0":
        print("★ L级判定: 🔴 L0(铁拦) 命中[%s]" % _k)
        print("★ 判定: 🔴 L0·闸拦(资金/私钥/不可逆 -> 必人批·不许自办)")
        return 2
    ok, out = require_decide(what, hard=False)
    print(out)
    print("★ 判定: " + ("✅ 过" if ok else "🔴 打回·先改再干"))
    return 0 if ok else 1


if __name__ == "__main__":
    w = " ".join(sys.argv[1:]) or "（未给决定）"
    sys.exit(show(w))
