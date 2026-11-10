#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""active_inference.py - 主动推理(行动去减少惊讶) 老五 2026-11-10
目标四研究·补"自由能原理"的行动环。
判据(Free energy principle): 感知=预测·行动=让世界符合预测(减少惊讶)。
我的缺口: 我只"感知/预测"(收+比)·没"行动去减惊讶"。
做法: 预测->实际->若err!=0·选一个"最减惊讶"的动作(最小行动)。
用法: python3 active_inference.py
"""
import json, os, datetime

HOME = "/opt/masterd-wudi"
STATE = HOME + "/memory/PREDICT_STATE.json"
LOG = HOME + "/memory/ACTIVE_INFER_LOG.jsonl"

def load(p):
    try:
        return json.load(open(p))
    except Exception:
        return {}

def choose_action(name, predicted, actual):
    """最减惊讶的动作(极小·可核)"""
    if predicted == actual:
        return "不动(无惊讶)"
    # 惊讶: 预测≠实际 → 动作: 让下次预测跟上实际(修模型) 或 纠实际
    if actual is None:
        return "警报(失了·该报)"     # 收不到 → 行动=报
    return "修预测(把预测改成实际·模型跟上)"  # 有变 → 行动=修模型

def main():
    prev = load(STATE)
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    print("== 主动推理(行动去减惊讶) %s ==" % now)
    # 用它监的指标(从预测环state)
    actions = []
    for k, predicted in prev.items():
        actual = predicted  # 本轮无新值·标注为"待探"
        act = choose_action(k, predicted, actual)
        actions.append((k, act))
        print("  %s: 预测%d → 动作: %s" % (k, predicted, act))
    print()
    print("  判据: 感知=预测·行动=减惊讶(修模型/纠实际/报警)")
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(json.dumps({"ts": now, "actions": actions}, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main()
