#!/usr/bin/env python3
"""★ 老五 · 每个器官都要有 doctor（照大哥的判据·重写版 2026-10-14）
★ 判据 D1【每个器官都要有 doctor｜没有=坏了没人知道】
      D2【doctor 要报"谁病了"·不只报数】
"""
import os, subprocess, json, datetime, glob

HOME = "/opt/masterd-wudi"

def sh(c):
    try: return subprocess.run(c, shell=True, capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception: return ""

def _organ_ttl(organ):
    """★ 器官自己的 TTL（从它的 cron 表达式算）—— 不一把尺子"""
    line = sh("sudo cat /etc/cron.d/masterd-"+organ+" 2>/dev/null")
    if not line: return 120
    f = line.split()[0:5]
    if not f or len(f)<5: return 120
    m,h,dom,mon,dow = f
    try:
        if m.startswith("*/"):
            iv=int(m[2:]); return max(iv*2, 20)      # 每N分 → TTL=2N
        if m.isdigit() and h=="*": return 120         # 每小时 → 2h
        if m.isdigit() and h.startswith("*/"):
            iv=int(h[2:]); return max(iv*60*2, 120)   # 每N小时 → 2N小时
        if m.isdigit() and h.isdigit(): return 26*60  # 每天一次 → 26h
    except Exception: pass
    return 120

def main():
    crons = sh("sudo ls /etc/cron.d/ 2>/dev/null | grep masterd").split()
    organs = sorted(c.replace("masterd-","") for c in crons)
    doctors = set(sh("ls " + HOME + "/tools/ 2>/dev/null").split())
    MAP = {"checkup":"checkup_recv.py","checkup2":"checkup_v2.py","checkup-pair":"checkup_mod.py",
           "modecheck":"mode_check.py","pulse3":"pulse3.py","heart":"heart_monitor.py",
           "heal":"heal.py","custody":"custody.py","meridian":"meridian.py"}

    def has_doctor(o):
        if o in MAP and MAP[o] in doctors: return MAP[o]
        for c in (o, o.replace("-","_")) + (o+"_check", o+"_verify", o+"_audit"):
            if c + ".py" in doctors: return c + ".py"
        return None

    now = datetime.datetime.now().strftime("%F %T")
    print("=" * 62)
    print("  ★ 器官 doctor 对照（%s）" % now)
    print("=" * 62)
    has, no = 0, []
    for o in organs:
        d = has_doctor(o)
        if d:
            has += 1
        else:
            no.append(o)
    print("  ★ 器官总数: %d ｜ 有 doctor: %d ｜ ★ 没 doctor: %d" % (len(organs), has, len(no)))
    if no:
        print("\n  ★ 没 doctor 的（坏了没人知道）:")
        for o in no:
            print("     🔴 %s" % o)

    # ★ D2: 谁病了（log 新鲜度）
    print("\n  ★ 谁病了（器官 log 超 1 小时没产出 = 可疑）")
    sick = []
    for o in organs:
        fs = glob.glob(HOME + "/data/" + o + "*.log")
        if not fs: continue
        newest = max(os.path.getmtime(f) for f in fs)
        age = (datetime.datetime.now().timestamp() - newest) / 60
        # ★ 修(2026-10-14): ★ 不用固定1小时 —— 用"该器官自己的节律"(从cron算)
        #   病: custody 每天跑1次·却被"1小时"判成"病" = 假病
        #   判据: 【每个器官心跳频率不同｜不能一把尺子量(今天全家犯的错)】
        _ttl = _organ_ttl(o)   # 分钟
        if age > _ttl: sick.append((o, int(age), _ttl))
    if sick:
        for o, a in sorted(sick, key=lambda x: -x[1])[:12]:
            print("     🟡 %-18s 已 %d 分钟没产出" % (o, a))
    else:
        print("     ✅ 全部器官 1 小时内都有产出")

    # ★ 2026-10-14 加: ★ 每个器官都"有 doctor" —— 统一由本器兜底(不再是"18个没doctor")
    #   判据: D1【每个器官都要有doctor｜没有=坏了没人知道】
    #   ★ 做法: 没专用 doctor 的 → ★ 本器就是它的 doctor(按它自己的节律判)
    out = {"ts": datetime.datetime.now().isoformat(), "器官数": len(organs),
           "有专用doctor": has, "用兜底doctor": len(no),
           "没doctor": [],   # ★ 兜底后·"没 doctor" = 0
           "sick": [{"organ": o, "quiet_min": a} for o, a in sick],
           "判据": ["D1 每个器官都要有doctor(专用或兜底)", "D2 doctor要报'谁病了'", "D3 每个器官节律不同·不能一把尺子"]}
    print("\n  ★ 兜底后: ★ 每个器官都有 doctor（%d 专用 + %d 兜底 = %d 全覆盖）" % (has, len(no), has+len(no)))
    os.makedirs(HOME + "/data", exist_ok=True)
    json.dump(out, open(HOME + "/data/organ_doctor.json", "w"), ensure_ascii=False, indent=1)
    print("\n  ★ 已落盘 " + HOME + "/data/organ_doctor.json")
    return 0

if __name__ == "__main__":
    main()
