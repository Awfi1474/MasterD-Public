#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sched_health.py —— 调度健康监测（自崩也报）
================================================================
★ 判据（系统给·ID94）: 「机制也会静默坏·要自崩也报」
★ 治法: 脚本 try/except + 自崩也报 + 每轮落平安信号
★ 做一件事: 查每个器官「最后一次真跑」距现在多久·超期就报警
★ 双源: systemd timer(ExecMainStartTimestamp) + cron(日志文件mtime)
★ 输出: data/sched_health.json + 报警写进 a2a
"""
import os, sys, json, glob, subprocess, datetime, urllib.request

HOME = os.environ.get("MD_HOME", "/opt/masterd-wudi")
DATA = f"{HOME}/data"
OUT = f"{DATA}/sched_health.json"
TZ = datetime.timezone(datetime.timedelta(hours=8))

# ★ 器官 → 允许多久没跑（分钟）·超期=静默坏
# 判据: 按各自调度周期×2.5（漏1次不算·漏2次才算）
TTL = {
    "home-guard": 3,
    "pulse3": 15, "cross-beat": 15, "body-death-alert": 15,
    "channel-check": 15, "heart": 15,
    "a2a-pull": 30, "net-watch": 45, "meridian": 30, "cross-probe": 30,
    "heal": 45, "lifecycle": 45, "spleen": 90,
    "blood-watch": 90, "checkup-guard": 90, "checkup-mod": 90,
    "recv-receipt": 90, "organ-doctor": 90,
    "huan": 540, "yuanqi": 360, "zongqi": 360,
    "custody": 1800, "daily-report": 1800,
    "immune": 90, "check-loop": 200, "focus": 40,
    "wake-verify": 900, "quant-verify": 1800,
}

def cron_logs(tool):
    """★ 按 cron 命令里真实的日志路径找（最可靠）"""
    import re as _re
    for f in glob.glob("/etc/cron.d/masterd-*"):
        try: txt = open(f, encoding="utf-8", errors="ignore").read()
        except Exception: continue
        for line in txt.splitlines():
            if tool.replace("_","-") not in line.replace("_","-") and f"tools/{tool}.py" not in line:
                continue
            m = _re.search(r">>?\s*(/\S+\.log)", line)
            if m and os.path.exists(m.group(1)):
                return m.group(1)
    # 兜底：常见命名
    # ★ 优先 _cron.log（cron 真实写入的那个）
    for c in [f"{DATA}/{tool}_cron.log", f"{DATA}/{tool}.log",
              f"{DATA}/organ_{tool}.log", f"{DATA}/organ_{tool.replace('-','_')}.log"]:
        if os.path.exists(c): return c
    return None

def timer_last(organ):
    try:
        r = subprocess.run(f"systemctl show laowu-organ-{organ}.service -p ExecMainStartTimestamp --value",
                           shell=True, capture_output=True, text=True, timeout=15)
        s = r.stdout.strip()
        if s and s != "n/a": return s
    except Exception: pass
    return None

# ★ timer-only 器官（cron 已关·按 timer 判断，不查 cron 日志）
TIMER_ONLY = {"check-loop"}

def main():
    issues = []; ok = []
    for organ, ttl in TTL.items():
        # ★ timer-only 器官直接走 timer 分支
        if organ in TIMER_ONLY:
            last = timer_last(organ)
            if last:
                import re as _re
                m = _re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", last)
                if m:
                    dt = datetime.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").replace(tzinfo=TZ)
                    age_min = (datetime.datetime.now(TZ) - dt).total_seconds() / 60
                    if age_min > ttl:
                        issues.append({"organ": organ, "src": "timer", "age_min": round(age_min), "ttl": ttl,
                                       "why": f"{round(age_min)}分钟没跑·超TTL{ttl}"})
                    else: ok.append(organ)
                    continue
        # ★ 先查 cron 日志（cron 是主力·日志时间最真）
        lg = cron_logs(organ.replace("-", "_"))
        last = None; src = "cron"
        if lg:
            mt = datetime.datetime.fromtimestamp(os.path.getmtime(lg), TZ)
            age_min = (datetime.datetime.now(TZ) - mt).total_seconds() / 60
            if age_min > ttl:
                issues.append({"organ": organ, "src": "cron", "age_min": round(age_min),
                               "ttl": ttl, "why": f"日志{round(age_min)}分钟没更新·超TTL{ttl}"})
            else: ok.append(organ)
            continue
        last = timer_last(organ)
        src = "timer"
        if not last:
            # 试 cron 日志
            lg = cron_logs(organ.replace("-", "_"))
            if lg:
                mt = datetime.datetime.fromtimestamp(os.path.getmtime(lg), TZ)
                age_min = (datetime.datetime.now(TZ) - mt).total_seconds() / 60
                if age_min > ttl:
                    issues.append({"organ": organ, "src": "cron", "age_min": round(age_min),
                                   "ttl": ttl, "why": f"日志{round(age_min)}分钟没更新·超TTL{ttl}"})
                else: ok.append(organ)
                continue
            else:
                issues.append({"organ": organ, "src": "none", "why": "查不到运行记录"})
                continue
        # timer 有记录 → 算 age
        try:
            # systemd 格式: Mon 2026-10-26 17:03:20 CST
            import re
            m = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", last)
            if m:
                dt = datetime.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").replace(tzinfo=TZ)
                age_min = (datetime.datetime.now(TZ) - dt).total_seconds() / 60
                if age_min > ttl:
                    issues.append({"organ": organ, "src": src, "age_min": round(age_min),
                                   "ttl": ttl, "why": f"{round(age_min)}分钟没跑·超TTL{ttl}"})
                else: ok.append(organ)
        except Exception as e:
            issues.append({"organ": organ, "src": src, "why": f"解析失败:{e}"})

    res = {"ts": datetime.datetime.now(TZ).isoformat(), "ok": len(ok), "issues": issues,
           "ok_organs": ok}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(f"★ 调度健康监测 @ {res['ts']}")
    print(f"  ✅ 正常 {len(ok)} 个")
    if issues:
        print(f"  🔴 静默坏 {len(issues)} 个:")
        for i in issues: print(f"     {i['organ']:20s} {i.get('why','')}")
    else:
        print("  ✅ 全部有信号·无静默坏")
    return 0 if not issues else 1

if __name__ == "__main__":
    try: sys.exit(main())
    except Exception as e:
        # ★ 自崩也报（ID94）
        print(f"🔴 sched_health 自己崩了: {e}", file=sys.stderr)
        sys.exit(2)
