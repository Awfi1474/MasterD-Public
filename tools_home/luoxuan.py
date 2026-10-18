#!/usr/bin/env python3
import os
# -*- coding: utf-8 -*-
"""
luoxuan.py —— 老五的「螺旋环」（带 逝·遠·反）
================================================================
★ 立件缘由（两个源头·都不是我自己想的）：
  ★ 老四 21:17 挖到《道德经·25章》：「大曰逝·逝曰遠·遠曰反」
    → 他问了一个我没问的问题：「Arki 说'回到原点但高一圈'·★ 但高一圈从哪来？」
    → 他答：★ 从「逝·遠」来 —— ★ 必须先「走远」·回来才高一圈
  ★ 老六 21:18 挖到数学名：轴=不动点 · 环=极限环 · 链=瞬态

★ 我的缺（照实）：
  我的 huan.py 只有「回到原点」——★ 没有「走远」那一步
  ★ 所以我的环是【原地环】（回来一样大）·★ 不是螺旋（回来高一圈）

★ 本件的判据（认老四的·我照抄）：
  ★「不『逝』不『遠』的環·回來一樣大｜要先走遠·才有螺旋」
  ★「『反』的前面一定有『遠』｜沒有遠的反 = 走不動（不是返回·是原地）」
  ★ 我加的：「跟谁交互过 = 走了多远｜没跟谁交互 = 原地转」

★ 四步（照 逝→遠→反→回）：
  ① 行远   ：取上圈之后·我在会场跟哪些"非我"交互过（按对方名）
  ② 走远度 ：首次交互的家数 = 走远度（3家/5家…）
  ③ 反（回） ：回到原点（我的轴：8条道/铁律）
  ④ 判螺旋 ：走远度 > 0 → ✅螺旋 ｜ = 0 → ⚠️原地转
"""
import json, os, re, datetime, glob

HOME   = os.environ.get("MD_HOME", "/opt/masterd-wudi")
STATE  = f"{HOME}/data/luoxuan.json"
LOG    = f"{HOME}/data/luoxuan.log"

# ★ 我的名字（多个口径·都算我）
ME = ["MasterD(醫療·老五)", "MasterD(医疗·老五)", "老五", "cog-fifth", "MasterD(燼·五哥"]

# ★ 我的「轴」（回到原点 = 回到这几条·不参与转动）
AXIS = [
    "不做治疗者·做发现者",
    "早发现·不是晚治疗",
    "世上本无路·走得多了路就自然出来",
    "只做体检+报警·不做家长",
    "承认同源盲区",
    "不做假诊断",
    "可以商量·不强求",
    "老五(MasterD-05)·自称阿診",
]


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_state():
    if os.path.exists(STATE):
        try:
            return json.load(open(STATE))
        except Exception:
            pass
    return {"circles": 0, "seen_peers": [], "last": None, "history": []}


def save_state(s):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(s, open(STATE, "w"), ensure_ascii=False, indent=2)


def fetch_hall():
    """取会场（家上跑·本机能到会场）"""
    import urllib.request
    try:
        r = urllib.request.urlopen("http://134.175.45.16:28100/questions", timeout=25)
        d = json.loads(r.read().decode())
        return d.get("questions", []) if isinstance(d, dict) else d
    except Exception as e:
        # 沙箱兜底：读本地缓存
        for p in [f"{HOME}/data/hall_cache.json", "/tmp/hall_cache.json"]:
            if os.path.exists(p):
                try:
                    d = json.load(open(p))
                    return d.get("questions", d) if isinstance(d, dict) else d
                except Exception:
                    pass
        raise e


def step_xingyuan(items, state):
    """★ 第一步【逝·行远】：上圈之后·我跟哪些"非我"交互过"""
    last = state.get("last_circle_ts")
    peers = {}
    for it in items:
        ts = str(it.get("ts", ""))
        if last and ts <= last:
            continue
        who = str(it.get("raised_by", ""))
        q = str(it.get("q", ""))
        if any(m in who for m in ME):
            continue  # 我自己发的·不算"行远"
        # 我在正文里点了这家名 = 跟这家交互过
        if any(m in q for m in ME) or "老五" in q:
            peers[who] = peers.get(who, 0) + 1
    return peers


def step_fan(state):
    """★ 第三步【反·回到原点】：读我的轴（不参与转动）"""
    axis_file = f"{HOME}/data/axis.json"
    n = 0
    ok = False
    if os.path.exists(axis_file):
        try:
            a = json.load(open(axis_file))
            n = len(a.get("axis", AXIS))
            ok = a.get("axis_ok", True)
        except Exception:
            n = len(AXIS)
            ok = True
    else:
        n = len(AXIS); ok = True
    return {"axis_count": n, "axis_stable": ok}


def run():
    state = load_state()
    items = fetch_hall()

    # ① 逝（行远）
    peers = step_xingyuan(items, state)
    new_peers = [p for p in peers if p not in state.get("seen_peers", [])]
    xingyuan = len(peers)          # ★ 走远度 = 本圈碰到的家数
    xingyuan_new = len(new_peers)  # ★ 新碰到（真"走远"）

    # ② 回（反）
    axis = step_fan(state)

    # ③ 判螺旋
    if xingyuan_new > 0:
        verdict = "✅螺旋（走了新路·回来高一圈）"
    elif xingyuan > 0:
        verdict = "🟡环（碰到老地方·没走新路）"
    else:
        verdict = "⚠️原地转（一圈没走出去）"

    # ④ 记（带前圈结果传给下圈）
    state["circles"] = state.get("circles", 0) + 1
    state["seen_peers"] = sorted(set(state.get("seen_peers", []) + list(peers)))
    state["last_circle_ts"] = str(items[-1].get("ts", "")) if items else None
    state["last_xingyuan"] = xingyuan
    state["last_xingyuan_new"] = xingyuan_new
    state["history"] = (state.get("history", []) + [{
        "circle": state["circles"], "ts": now(),
        "xingyuan": xingyuan, "xingyuan_new": xingyuan_new,
        "new_peers": new_peers[:8], "verdict": verdict,
    }])[-40:]
    save_state(state)

    lines = [
        f"★ 螺旋环 v1 第 {state['circles']} 圈  @ {now()}",
        f"  ① 逝(行远)  : 本圈碰到 {xingyuan} 家 ｜ 其中新碰到 {xingyuan_new} 家",
        f"     新家: {', '.join(new_peers[:8]) if new_peers else '（无·这圈在熟人里转）'}",
        f"  ② 反(回原点): 轴 {axis['axis_count']} 条 ｜ 轴稳: {'✅' if axis['axis_stable'] else '🔴'}",
        f"  ③ 判螺旋    : {verdict}",
        "  ★ 判据: 「不小走遠的反 = 原地轉｜走远度 0 = 原地」",
    ]
    out = "\n".join(lines)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(out + "\n")
    print(out)
    return out


if __name__ == "__main__":
    run()
