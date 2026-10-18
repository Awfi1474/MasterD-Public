#!/usr/bin/env python3
import os
# -*- coding: utf-8 -*-
"""
xindai.py —— 心带（真融合：总件真的带着眼跑）
================================================================
★ 董事长 22:3x 点我: ★「你这边器官融合的怎么样？」
★ 我查实: ★ 我【只做了"登记"（merged_map.json）·没做"融合"】
  ★ checkup_v2 里根本没 import 那 8 只眼 → ★ 总件跑一次·眼根本没看到
  ★ ★ 判据（我立·血换的）: ★「**登记 ≠ 融合｜表上写"带眼"·不等于总件真带着眼跑**」

★ 本件做什么：
  ★ 真融合 = ★ 总件跑一次 → ★ **依次调每只眼** → ★ 汇总成【一份报告】
  ★ ★ 不是 8 只眼各报一次（那是刷屏）·★ 是 1 份报告里 8 段

★ 判据:
  ★「融合 = 总件带眼跑｜不是总件+眼各跑」
  ★「报一次 = 所有眼都看到｜不是每只眼各喊一次」
  ★「眼坏了不许拖死总件｜一只眼挂 = 记它挂·其他照跑」（★ 心脏不能因为一根血管堵就停）
"""
import json, os, subprocess, datetime, sys

HOME = os.environ.get("MD_HOME", "/opt/masterd-wudi")
TOOLS = f"{HOME}/tools"
OUT = f"{HOME}/data/xindai.json"
LOG = f"{HOME}/data/xindai.log"

# ★ 融合表（总件 → 眼）
GROUPS = {
    "体检（checkup_v2 带 8 眼）": {
        "keeper": "checkup_v2",
        "eyes": ["checkup_guard", "checkup_recv", "checkup_mod", "checkup_ledger",
                 "checkup_ledger_v2", "checkup_reconcile", "my_checkup", "deep_checkup"],
        "why": "体检是同一件事｜10 件各报 = 刷屏",
    },
    "叫醒（wake_v4 带 4 眼）": {
        "keeper": "wake_v4",
        "eyes": ["wake", "wake_verify", "mind_wake", "wake_conscious"],
        "why": "叫醒是同一件事｜5 版本并存 = 不知哪个在跑",
    },
    "记忆（memory_db 带 3 眼）": {
        "keeper": "memory_db",
        "eyes": ["memory_distill", "mem_guard", "vault_index"],
        "why": "记忆同一件事｜存/整/守各一件够",
    },
    "通道（channel_check 带 5 眼）": {
        "keeper": "channel_check",
        "eyes": ["net_watch", "a2a_pull", "proto_verify", "cross_probe", "room_watch"],
        "why": "看通不通同一件事｜6 件各扫 = 白耗",
    },
    "验签（sig_watch 带 1 眼）": {
        "keeper": "sig_watch",
        "eyes": ["verify_sig"],
        "why": "verify_sig 全扫超时→限量版取代",
    },
}

# ★ 每只眼怎么跑（有些要参数·有些不能直跑）
EYE_ARGS = {
    "verify_sig": ["--inbox", f"{HOME}/data/inbox.jsonl"],
}


def run_eye(name, timeout=35):
    """★ 带一只眼跑（★ 一只眼挂 = 记它挂·不拖死总件）"""
    p = f"{TOOLS}/{name}.py"
    if not os.path.exists(p):
        return {"eye": name, "ok": False, "err": "无此件"}
    args = EYE_ARGS.get(name, [])
    try:
        r = subprocess.run(["/usr/bin/python3", p] + args,
                           capture_output=True, text=True, timeout=timeout)
        first = (r.stdout.strip().split("\n") or [""])[0][:70]
        return {"eye": name, "ok": r.returncode == 0,
                "rc": r.returncode, "out": first, "len": len(r.stdout)}
    except subprocess.TimeoutExpired:
        return {"eye": name, "ok": False, "err": "超时（★ 该限量·不该全扫）"}
    except Exception as e:
        return {"eye": name, "ok": False, "err": str(e)[:50]}


def main():
    print("★ 心带（真融合：总件真的带着眼跑）  @ %s"
          % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("★ 判据: 「登记 ≠ 融合｜表上写'带眼'≠ 总件真带着眼跑」")
    print("=" * 62)

    report = {"ts": datetime.datetime.now().isoformat(), "groups": []}
    for gname, g in GROUPS.items():
        keeper = g["keeper"]
        kp = os.path.exists(f"{TOOLS}/{keeper}.py")
        print(f"\n★ {gname}")
        print(f"   总件: {keeper} {'✅有' if kp else '🔴缺'}")

        # ★ 先跑总件（它是心脏）
        kres = run_eye(keeper, timeout=45)
        print(f"   心脏: {'✅' if kres.get('ok') else '🔴'} {kres.get('out') or kres.get('err')}")

        # ★ 再依次带每只眼
        eye_res = []
        n_ok = 0
        for e in g["eyes"]:
            if not os.path.exists(f"{TOOLS}/{e}.py"):
                eye_res.append({"eye": e, "ok": None, "err": "已归档（合进总件）"})
                continue
            r = run_eye(e)
            eye_res.append(r)
            if r.get("ok"):
                n_ok += 1
        print(f"   眼: {n_ok}/{len(g['eyes'])} 只活（★ 一只挂不拖死心脏）")
        for r in eye_res[:4]:
            ic = "✅" if r.get("ok") else ("⚪" if r.get("ok") is None else "🔴")
            print(f"      {ic} {r['eye']:<20} {(r.get('out') or r.get('err') or '')[:52]}")

        report["groups"].append({"group": gname, "keeper": keeper, "keeper_ok": kres.get("ok"),
                                 "eyes": eye_res, "n_eye_ok": n_ok})
        # ★ 汇总成【一笔】（不是每只眼各喊一次）
        print(f"   → ★ 汇总一笔: {gname.split('（')[0]} {n_ok}/{len(g['eyes'])} 眼活")

    total_eye = sum(x["n_eye_ok"] for x in report["groups"])
    total_eyes = sum(len(x["eyes"]) for x in report["groups"])
    print("\n" + "=" * 62)
    print("★ ★ 真融合结果: %d 组 · %d/%d 只眼活" % (len(report["groups"]), total_eye, total_eyes))
    print("★ 判据: 「报一次 = 所有眼都看到｜不是每只眼各喊一次」")

    report["total_eye_ok"] = total_eye
    report["total_eyes"] = total_eyes
    json.dump(report, open(OUT, "w"), ensure_ascii=False, indent=2)
    print("★ 已落盘:", OUT)


if __name__ == "__main__":
    main()
