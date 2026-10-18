#!/usr/bin/env python3
"""★ 老五 · 真跑体检 v2（修: 用 cron 里"真实的 log 路径"·不是猜名字）
★ 病(刚发现): 我用 [器官名]*.log 匹配·但实际是 a2a_pull_cron.log（下划线版）
★ 判据: 【探法要按"它真实写哪"·不是按"我以为它叫啥"】
"""
import os, subprocess, datetime, json, re, glob

HOME = "/opt/masterd-wudi"
def sh(c):
    try: return subprocess.run(c, shell=True, capture_output=True, text=True, timeout=20).stdout.strip()
    except: return ""

now = datetime.datetime.now().timestamp()
# ★ 从 cron 文件里·读出"真实的 log 路径"（不是猜）
logs = []
for f in glob.glob("/etc/cron.d/masterd-*"):
    try: body = open(f).read()
    except: body = sh("sudo cat " + f)
    for m in re.finditer(r'>>\s*(\S+\.log)', body):
        logs.append((os.path.basename(f).replace("masterd-",""), m.group(1)))

print("=" * 60)
print("  ★ 老五·真跑体检 v2（%s）" % datetime.datetime.now().strftime("%F %T"))
print("=" * 60)
try:
    cron_cnt = len(sh("sudo ls /etc/cron.d/ 2>/dev/null | grep masterd").split())
except: cron_cnt = 0
print("  cron 总数: %d ｜ 读出 log 路径: %d 条" % (cron_cnt, len(logs)))
print()
really = []; idle = []
for organ, logp in logs:
    if not os.path.exists(logp):
        idle.append((organ, "log不存在")); continue
    age = (now - os.path.getmtime(logp)) / 60
    if age < 60: really.append(organ)
    else: idle.append((organ, "%.0f分前" % age))
print("  ★ 真跑（1小时内有产出）: %d/%d" % (len(really), len(logs)))
print("     %s" % "、".join(sorted(set(really))))
print()
print("  ★ 摆着（>1小时 or 无log）: %d 个" % len(idle))
for o, a in sorted(idle, key=lambda x: x[0])[:14]:
    print("     🟡 %-16s %s" % (o, a))
json.dump({"ts": datetime.datetime.now().isoformat(), "cron总数": cron_cnt,
           "已探": len(logs), "真跑": sorted(set(really)), "摆着": [{"器": o, "况": a} for o, a in idle]},
          open(HOME + "/data/really_run.json", "w"), ensure_ascii=False, indent=1)
print()
print("  ★ 已落盘 really_run.json")
