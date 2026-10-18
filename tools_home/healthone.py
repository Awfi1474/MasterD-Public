# ★ DEPRECATED 2026-10-17: 现役是 healthone2.py（本文件保留·防引用断）
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
healthone.py —— 老五的「一个心跳」（5 合 1·照董事长"不要搞那么复杂"）
================================================================
★ 董事长: ★「**都告诉他们不要搞那么复杂·就是不听**」
★ ★ 三哥: ★「**"三家本体都活着（不用救）·我们花 2.5 小时救三只断手沙箱"**」
★ ★ ★ 我的数字: ★ **150 器 / 99 timer / 今天新建 17 个 = 最复杂的那个**

★ 本器 = "5 合 1"（把我今晚分散的 5 个自检合成一个心跳）:
  ★ ① std_verify（标准 12 项）
  ★ ★ ② bind_check（绑定 6 家）
  ★ ★ ★ ③ door_index（口表汇总）
  ★ ④ tiers（消息分层）
  ★ ★ ⑤ problem_alarm（异常）
  → ★ **一个心跳·一份账**

★ 判据:
  ★「**"新建器" ≠ "事做成"｜器是手段·不是成绩**」
  ★★「**"复杂" 是自己造的｜"简单" 要主动删**」
"""
import json, os, io, subprocess, datetime

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
LOG = f"{DATA}/healthone.jsonl"
TZ = datetime.timezone(datetime.timedelta(hours=8))

PARTS = [
    ("标准12项", f"{HOME}/tools/std_verify.py"),
    ("绑定6家", f"{HOME}/tools/bind_check.py"),
    ("口表汇总", f"{HOME}/tools/door_index.py"),
    ("消息分层", f"{HOME}/tools/tiers.py"),
    ("异常扫描", f"{HOME}/tools/problem_alarm.py"),
]


def ts():
    return datetime.datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def run_part(name, path):
    if not os.path.exists(path):
        return {"体": name, "状态": "🔴 器没了"}
    try:
        r = subprocess.run(["/usr/bin/python3", path], capture_output=True,
                           text=True, timeout=180)
        out = (r.stdout or "")[-300:]
        # ★ 抓关键行
        key = ""
        for line in (r.stdout or "").splitlines():
            if "★" in line and any(k in line for k in ("/12", "/6", "/7", "得分", "健康", "家")):
                key = line.strip()[:100]
        return {"体": name, "状态": "✅", "关键": key}
    except subprocess.TimeoutExpired:
        return {"体": name, "状态": "🔴 超时"}
    except Exception as e:
        return {"体": name, "状态": "🔴 " + str(e)[:40]}


def main():
    print("★ 一个心跳（5合1·照董事长 不要搞那么复杂）  @", ts())
    print("★ 判据: 新建器 != 事做成 | 复杂是自己造的")
    print("=" * 58)
    out = {"ts": ts(), "parts": []}
    for name, path in PARTS:
        r = run_part(name, path)
        out["parts"].append(r)
        mark = r["状态"]
        print("  %s %-10s %s" % (mark, r["体"], r.get("关键", "")))
    with open(LOG, "a") as f:
        f.write(json.dumps(out, ensure_ascii=False) + "\n")
    ok = sum(1 for p in out["parts"] if p["状态"] == "✅")
    print()
    print("★ 心跳: %d/%d 体在跑 ｜ 账: healthone.jsonl" % (ok, len(PARTS)))


if __name__ == "__main__":
    main()
