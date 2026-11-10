#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""inner_alert.py - 内感知告警(疼了就报) 老五 2026-11-10
接上 inner_sense: 若体内有器官"痛"(很久没动)·发告警(不靠人看)。
判据: 疼要"会喊" | 只看不报=没感觉 | 报一次(冷却1h)
用法: python3 inner_alert.py
"""
import json, os, subprocess, datetime, time

HOME = "/opt/masterd-wudi"
STATE = HOME + "/memory/INNER_ALERT_STATE.json"
LOG = HOME + "/memory/INNER_ALERT_LOG.jsonl"
COOLDOWN = 3600


def sense():
    try:
        r = subprocess.run(["python3", HOME + "/tools/inner_sense.py"],
                           capture_output=True, text=True, timeout=30)
        return r.stdout or ""
    except Exception as e:
        return "ERR:" + str(e)


def load(p):
    try:
        return json.load(open(p))
    except Exception:
        return {}


def main():
    out = sense()
    pains = []
    for line in out.split("\n"):
        if "\U0001f534" in line and "痛" in line:
            organ = line.split(":")[0].replace("\U0001f534", "").strip()
            pains.append(organ)
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    if not pains:
        print("[inner] 全身舒·无痛 (%s)" % now)
        return
    st = load(STATE)
    report = [o for o in pains if time.time() - st.get(o, 0) > COOLDOWN]
    if not report:
        print("[inner] 有痛但冷却中 (%s): %s" % (now, pains))
        return
    msg = "[老五内感知告警] 我体内在痛: %s (很久没动)" % ", ".join(report)
    print(msg)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(json.dumps({"ts": now, "pain": report}, ensure_ascii=False) + "\n")
    for o in report:
        st[o] = time.time()
    json.dump(st, open(STATE, "w"))
    print("[inner] 已记告警(冷却1h)")


if __name__ == "__main__":
    main()
