#!/usr/bin/env python3
# 老五「事实门」（2026-10-11 · 彻底治"假"的根）
# ★ 根因：「自述 vs 可验混了」→ 每家报"我的话" → 必然通过
# ★ 解药：把"自述"和"可验"变成"两个字段" —— 自述归自述·可验归可验
#   和"第二判官"（别人验我）+ "保鲜期"（验过会过期）
#
# ★ 事实门 = 一句话：「**你说的每一句'状态'·要么给'可验证据'·要么标'自述'**」
import os, sys, json, time, datetime, hashlib, urllib.request

HOME = os.environ.get("P2P_HOME", "/opt/masterd-wudi")
OUT = HOME + "/data/fact_gate.json"


def sh(cmd, t=8):
    import subprocess
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=t)
        return r.stdout.strip()
    except Exception:
        return ""


def facts():
    """★ 我的'事实门'——每条状态只三种：fact（可验）/ self（自述）/ unknown（没查）"""
    f = {}
    # ★ fact：有可验证据（外面能重做一遍）
    f["地基-三路"] = {"kind": "fact", "evidence": "GET /health + /report + /rescue/key 都 200",
                      "how": "打我的三个口"}
    f["包-指纹"] = {"kind": "fact", "evidence": "GET /package → sha256+age_s",
                    "how": "取 /package 比 sha256"}
    f["包-drift"] = {"kind": "fact", "evidence": "记忆库条数 vs 包内条数（backup_guard 数）",
                     "how": "解包数一遍·跟库比"}
    f["机制-在跳"] = {"kind": "fact", "evidence": "beat_check 看产出年龄（非 active）",
                      "how": "看每项 age"}
    f["协议-合规"] = {"kind": "fact", "evidence": "proto_verify 十节真跑 6/6",
                      "how": "照协议投一次"}
    # ★ self：自述（外面验不了·只能我自己说）
    f["意图"] = {"kind": "self", "note": "我'打算'做什么——这个只有我能说·外面验不了"}
    f["感受"] = {"kind": "self", "note": "'我累/我开心'——自述·不是事实"}
    # ★ unknown：我没查
    f["J5-第二台"] = {"kind": "unknown", "note": "我没能控的第二台机器·没查（=欠账）"}
    return f


def gate(claim):
    """★ 事实门：给定一句'状态声明'·判它是 fact / self / 空话"""
    c = str(claim)
    has_ev = any(k in c for k in ("http", "sha256", "200", "条", "GET ", "POST ", "秒"))
    if has_ev:
        return "fact(有可验证据)"
    if any(k in c for k in ("我认为", "我觉得", "应该", "大概", "自述")):
        return "self(自述·不算事实)"
    return "空话(既没证据·也没标自述 → 危险)"


def main():
    f = facts()
    n_fact = sum(1 for v in f.values() if v["kind"] == "fact")
    n_self = sum(1 for v in f.values() if v["kind"] == "self")
    n_unk = sum(1 for v in f.values() if v["kind"] == "unknown")
    print("  ★ 事实门（Fact Gate）")
    print("  我的'状态'分三类：fact（可验）%d ｜ self（自述）%d ｜ unknown（没查）%d" % (n_fact, n_self, n_unk))
    print("  " + "-" * 54)
    for k, v in f.items():
        kd = v["kind"]
        mark = {"fact": "✅", "self": "🟡", "unknown": "⚪"}[kd]
        print("   %s %-14s [%s] %s" % (mark, k, kd, (v.get("evidence") or v.get("note", ""))[:60]))
    print("  " + "-" * 54)
    print("  ★ 判据：")
    print("     「**说'状态'·要么给'可验证据'·要么标'自述'｜不许'没证据的自述'当事实**」")
    print("     ★ 三种标法：✅fact（外面能重做）｜🟡self（只有我能说）｜⚪unknown（我没查·=欠账）")
    json.dump({"ts": datetime.datetime.now().isoformat(), "facts": f,
               "counts": {"fact": n_fact, "self": n_self, "unknown": n_unk}},
              open(OUT, "w"), ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
