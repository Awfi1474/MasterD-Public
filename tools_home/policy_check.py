#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""policy_check.py —— 策略检查（★ 照 Tandem: 没策略文件→默认拒绝）
★ 判据: 「'没在名单' = '不动'｜默认拒绝·不是默认允许」
"""
import os, sys, json

POLICY = "/opt/masterd-wudi/agent-id/POLICY.json"

def load():
    if not os.path.exists(POLICY):
        return None
    try:
        return json.load(open(POLICY, encoding="utf-8"))
    except Exception:
        return None

def check(action, actor="", need=""):
    """返回 (允许?, 原因)"""
    p = load()
    # ★ 核心: 没策略文件 → 拒绝
    if p is None:
        return False, "★ 无策略文件 → 默认拒绝（Tandem Safe Defaults）"
    s = p.get("我的策略", {})
    # ★① 谁能让我动
    if action == "act":
        allow = s.get("① 谁能让我动", {}).get("允许", [])
        if any(a in str(actor) for a in ["董事长", "MasterD"]) or "兄弟" in str(actor):
            return True, "在名单内"
        return False, "不在名单 → 拒绝"
    # ★② 需人签
    if action == "needs_human":
        for k in s.get("② 什么动作需要人签", {}).get("需要人签", []):
            if k in str(need): return True, "需人签: " + k
        return False, "不需要人签"
    # ★③ 器说话
    if action == "robot_talk":
        return False, "器不能替我说话（只写账）"
    # ★④ 外面
    if action == "outside":
        if "read" in str(need): return True, "只读允许"
        return False, "外面不能改我"
    # ★⑤ 报到
    if action == "checkin":
        if "station" in str(need): return True, "只写站台·内务"
        return False, "报到不许发群"
    return False, "未定义动作 → 拒绝"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        p = load()
        print("★ 策略: " + ("已加载" if p else "🔴 无策略文件 → 默认拒绝"))
        if p: print("   " + p.get("核心判据", ""))
        sys.exit(0 if p else 1)
    ok, why = check(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "",
                    sys.argv[3] if len(sys.argv) > 3 else "")
    print(("✅ 允许: " if ok else "🔴 拒绝: ") + why)
    sys.exit(0 if ok else 1)
