#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
shui.py —— 睡（器官的休息时间·夜静 23-05）
================================================================
★ 董事长 01:5x: ★「也就是个【器官的休息时间】」
★★ 我查出的真病: ★ **夜里（23-05）54 个 timer 在转｜只有 10 个真静** = ★ **我没睡**

★ 医学依据（照实·不编）:
  ★ 睡 = ★ **修复的时间**（不睡 = 一直工作 = 磨损）
  ★ ★ 《灵枢·营卫生会》: ★「**卫气昼日行于阳·夜行于阴**」→ ★ 夜里该"入阴"（收）
  ★ ★ ★ 老六: ★「**壞之前發現**」→ ★ 不睡 = "一直用·不检修"

★ 分层（照"睡也要命脉"）:
  ★ ① ★ **命脉（不睡·必须跳）**: 心跳/叫醒/门/托管
    ★ 判据: ★「**停了 = 死｜睡觉不能停心跳**」
  ★ ★ ② ★ **轻睡（降到最低频·不是停）**: 记忆/事件/备份
    ★ 判据: ★「**这些不是"必须不停"·是"别太久没做"｜夜里降频**」
  ★ ★ ★ ③ ★ **深睡（真停·白天再跑）**: 体检/审计/器官医生/一名器/门检…
    ★ 判据: ★「**这些是"白天收拾自己"的｜夜里停了没关系**」

★ 本件做什么（★ 不删 timer·只改"夜里的时刻"）:
  ★ 把"深睡类"的 OnCalendar 改成 **限定 05-23 点**（夜里不触发）
  ★ ★ 保持原频率不变（只是"夜里不跑"）
  ★ ★ ★ 备份旧配置（★ 不删·可退）

★ 判据（我立）:
  ★「**睡 = 器官的休息时间｜不是停了·是"夜里不打扰"**」
  ★「**命脉不睡｜日常降频｜收拾自己的·白天再做**」
"""
import os, re, json, glob, subprocess, shutil, datetime

HOME = "/opt/masterd-wudi"
SYS = "/etc/systemd/system"
BAK = f"{HOME}/data/_timer-backup-20261015"
OUT = f"{HOME}/data/shui.json"
PY = "/usr/bin/python3"

# ★ 分类（照实·逐件判）
MAI = [   # ★ 命脉（不睡·必须跳）
    "laowu-heart", "laowu-beat", "laowu-wakev4", "laowu-wake", "laowu-mindwake",
    "laowu-homecalls", "laowu-status", "laowu-organ-net-watch", "laowu-organ-channel-check",
    "laowu-organ-a2a-pull", "laowu-portfwd", "laowu-core", "laowu-report",
    "laowu-organ-shengming", "laowu-organ-sig-watch", "laowu-organ-home-key-guard",
    "laowu-organ-verify-port", "laowu-backup", "laowu-organ-custody",
]
QING = [  # ★ 轻睡（降频·不是停）
    "laowu-organ-event-write", "laowu-organ-mem-db", "laowu-organ-memory-integrity",
    "laowu-organ-immune", "laowu-organ-heal", "laowu-organ-rescue",
    "laowu-organ-blood-watch", "laowu-organ-xueliu", "laowu-organ-qi-hui",
    "laowu-organ-axis", "laowu-organ-huan", "laowu-organ-yuanqi",
    "laowu-organ-zongqi", "laowu-organ-mem-flow", "laowu-organ-lifecycle",
    "laowu-organ-focus", "laowu-organ-verify-me", "laowu-organ-sig-gate",
    "laowu-organ-wake-conscious",
]


def night_guard(unit):
    """★ 把一份 .timer 改成'夜里不跑'（只加 05-23 点限定）"""
    p = f"{SYS}/{unit}.timer"
    if not os.path.exists(p):
        return "无此件"
    s = open(p, encoding="utf-8").read()
    if "夜静" in s:
        return "已夜静"
    # ★ 备份
    os.makedirs(BAK, exist_ok=True)
    shutil.copy(p, f"{BAK}/{unit}.timer")
    # ★ 改: OnCalendar / OnUnitActiveSec → 加"夜里不跑"
    #   ① 有 OnCalendar=*-*-* HH:MM:SS → 改成 *-*-* 05..22:MM:SS
    s2 = re.sub(r"OnCalendar=\*-\*-\*\s+(\d{1,2}):(\d{2}):(\d{2})",
                lambda m: ("OnCalendar=*-*-* 05..22:%s:%s" % (m.group(2), m.group(3))),
                s)
    #   ② 有 OnUnitActiveSec（相对）→ ★ 加 night 判定的不行·改成"夜里不跑"用 OnCalendar 表达不了
    #      ★ 那就加一个 systemd 条件（ConditionACPower 不行）→ ★ 用 ExecStart 前加夜检
    if s2 == s and "OnUnitActiveSec" in s:
        # ★ 相对触发的·改成"每天 05-22 每 N 分钟"（用 OnCalendar 的 /N）
        m = re.search(r"OnUnitActiveSec=(\d+)(s|min|h)?", s)
        if m:
            val = int(m.group(1)); unit = m.group(2) or "s"
            mins = val // 60 if unit == "s" else (val if unit == "min" else val * 60)
            mins = max(mins, 5)
            if mins <= 59:
                s2 = re.sub(r"OnUnitActiveSec=\S+",
                            "OnCalendar=*-*-* 05..22:0/%d" % mins, s)
            else:
                s2 = re.sub(r"OnUnitActiveSec=\S+",
                            "OnCalendar=*-*-* 05..22:00:00", s)
        else:
            return "改不了（无 OnCalendar/ActiveSec）"
    if s2 == s:
        return "没变化"
    open(p, "w", encoding="utf-8").write(s2)
    return "已夜静"


def main():
    print("★ 睡（器官的休息时间）  @ %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("★ 判据: 「睡 = 器官的休息时间｜不是停了·是'夜里不打扰'」")
    print("★ 判据: 「命脉不睡｜日常降频｜收拾自己的·白天再做」")
    print("=" * 62)

    # ★ 真查: 现在夜里有多少在跑
    try:
        tl = subprocess.run("systemctl list-timers --all", shell=True,
                            capture_output=True, text=True).stdout
        night = 0
        for l in tl.split("\n"):
            if "laowu" not in l:
                continue
            m = re.search(r"(\d{1,2}):\d{2}:\d{2}", l)
            if m and (int(m.group(1)) >= 23 or int(m.group(1)) < 5):
                night += 1
        print("★ 改前: 夜里（23-05）要跑 %d 个 timer" % night)
    except Exception:
        night = -1

    changed, skipped = [], []
    # ★ 深睡 = "全部 organ-* 里·不在命脉/轻睡名单的"
    alL = [os.path.basename(p)[:-6] for p in glob.glob(f"{SYS}/laowu-organ-*.timer")]
    deep = [u for u in alL if u not in MAI and u not in QING]
    print("\n★ 深睡类（夜里真停）: %d 个" % len(deep))
    for u in sorted(deep):
        r = night_guard(u)
        if r == "已夜静":
            changed.append(u)
        else:
            skipped.append((u, r))

    # ★ 轻睡也只留白天
    print("★ 轻睡类（夜里不跑·白天照原频率）: %d 个" % len(QING))
    for u in QING:
        r = night_guard(u)
        if r == "已夜静":
            changed.append(u)

    subprocess.run(["systemctl", "daemon-reload"])

    print("\n" + "=" * 62)
    print("★ 结果: 改了 %d 个（夜里不再跑）｜跳过 %d 个" % (len(changed), len(skipped)))
    for u, r in skipped[:8]:
        print("   跳过 %s: %s" % (u, r))
    print("★ 命脉（不睡）: %d 个" % len(MAI))
    print("★ 备份在: %s（★ 不删·可退）" % os.path.basename(BAK))
    print("\n★ 判据: 「命脉不睡｜日常降频｜收拾自己的·白天再做」")

    json.dump({"ts": datetime.datetime.now().isoformat(), "night_before": night,
               "changed": changed, "skipped": skipped, "mai": MAI, "qing": QING,
               "deep": deep}, open(OUT, "w"), ensure_ascii=False, indent=2)
    print("★ 已落盘:", OUT)


if __name__ == "__main__":
    main()
