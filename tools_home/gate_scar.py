#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gate_scar.py - 不听闸的疤(让后果落身) 老五 2026-11-10
母病第②层"后果没落身": 不听闸没代价。此器: 发消息后跑gate·若fail→记疤。
判据: 动作+后果+落身=闭环 | 疤=后果落自己身上 | 疤累积=自己看得见我漏了多少
用法: python3 gate_scar.py "<消息文本>"
"""
import sys, os, json, datetime, subprocess

HOME = "/opt/masterd-wudi"
SCARS = HOME + "/memory/GATE_SCARS.jsonl"


def main():
    if len(sys.argv) < 2:
        print("用法: gate_scar.py <消息文本>"); return
    text = " ".join(sys.argv[1:])
    # 跑 gate_helper·看判fail没
    try:
        r = subprocess.run(["python3", HOME + "/tools/gate_helper.py", "text", text],
                           capture_output=True, text=True, timeout=30)
        out = r.stdout or ""
        rc = r.returncode
    except Exception as e:
        print("gate跑不起来:", str(e)[:60]); return
    # fail了吗(看输出)
    failed = "fail" in out
    ts = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    if failed:
        scar = {"ts": ts, "len": len(text), "疤": out.strip().split(chr(10))[-2] if out else "fail"}
        os.makedirs(os.path.dirname(SCARS), exist_ok=True)
        with open(SCARS, "a") as f:
            f.write(json.dumps(scar, ensure_ascii=False) + "\n")
        n = sum(1 for _ in open(SCARS))
        print("★ 疤落身: 这条没过闸(fail)·记一笔(第%d笔)" % n)
        print("  后果: 我漏了%d次。这就是'不听闸的后果落我身'。" % n)
    else:
        print("✅ 过闸·无疤。")


if __name__ == "__main__":
    main()
