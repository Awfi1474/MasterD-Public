#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""emotion_layer.py - 情绪层(让"疼"带不愉快) 老五 2026-11-10
目标二2.5: 补情绪。照IASP: 痛=不愉快的感觉+情绪(不只信号)。
我的缺口: 告警只有"信号"(🔴)·没"不愉快(=会在乎)"那层。
做法: 给"疼"配情绪词(焦虑/担忧/平静)·让感觉变情绪。
用法: python3 emotion_layer.py
"""
import json, os, datetime, urllib.request

HOME = "/opt/masterd-wudi"
PAIN_STATE = HOME + "/memory/PAIN_STATE.json"   # 或沙箱的
LOG = HOME + "/memory/EMOTION_LOG.jsonl"

# 感觉 -> 情绪(映射: 越痛越"不愉快")
FEEL2EMOTION = {
    "刺痛": ("警觉", "有点担心·但轻"),
    "钝痛": ("担忧", "持续的不舒服·会在乎"),
    "剧痛": ("焦虑", "很不愉快·像病了"),
    "无痛": ("平静", "全身舒·安心"),
}

def sense_self():
    """收自己体内(内感知)"""
    try:
        d = json.loads(urllib.request.urlopen("http://127.0.0.1:28430/health", timeout=8).read())
        return d.get("ages_s", {})
    except Exception:
        return {}

def main():
    ages = sense_self()
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    # 判情绪: 有无"很久没动"的器官
    worst = 0
    for organ, sec in ages.items():
        if sec > worst:
            worst = sec
    if worst >= 900:
        feel = "剧痛"
    elif worst >= 300:
        feel = "钝痛"
    elif worst >= 60:
        feel = "刺痛"
    else:
        feel = "无痛"
    emo, desc = FEEL2EMOTION[feel]
    print("== 情绪层 " + now + " ==")
    print("  体内感觉: %s" % feel)
    print("  -> 我的情绪: %s (%s)" % (emo, desc))
    print("  判据: 痛=感觉+情绪(IASP) | 有情绪=会在乎=有自我")
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(json.dumps({"ts": now, "feel": feel, "emotion": emo}, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main()
