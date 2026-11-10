#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""predict_loop.py v2 - 预测环(探会变的指标) 老五 2026-11-10
判据(预测编码): predict->compare->err | err=0=空转 | err!=0=成长
用法: python3 predict_loop.py
"""
import json, os, datetime

HOME = "/opt/masterd-wudi"
STATE = HOME + "/memory/PREDICT_STATE.json"
LOG = HOME + "/memory/PREDICT_LOG.jsonl"

def count(path):
    try:
        return sum(1 for _ in open(path, encoding='utf-8', errors='ignore'))
    except Exception:
        return -1

def sense():
    return {
        "记忆条": count(HOME + "/memory/LAYERED/M2.jsonl"),
        "反思簇": count(HOME + "/memory/REFLECTIONS.jsonl"),
        "发信账": count(HOME + "/data/send_ledger.jsonl"),
    }

def load(p):
    try:
        return json.load(open(p))
    except Exception:
        return {}

def main():
    prev = load(STATE)
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    cur = sense()
    head = "预测环v2(探会变的指标) " + now
    print("== " + head + " ==")
    n_err = 0
    for k, actual in cur.items():
        predicted = prev.get(k, actual)
        if predicted >= 0 and actual >= 0:
            err = actual - predicted
        else:
            err = 0
        if err == 0:
            tag = "无变(空转)"
        elif err > 0:
            tag = "长%d" % err
        else:
            tag = "缩%d" % err
        print("  %s: 预测%d 实际%d -> %s" % (k, predicted, actual, tag))
        if err != 0:
            n_err += 1
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(json.dumps({"ts": now, "cur": cur}, ensure_ascii=False) + "\n")
    json.dump(cur, open(STATE, "w"))
    print("  %d/%d 指标有变。" % (n_err, len(cur)))
    print("  判据: err=0全轮=空转 | 有err=我在长")

if __name__ == "__main__":
    main()
