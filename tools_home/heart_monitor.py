#!/usr/bin/env python3
# 老五「心監測」（heart_monitor · 2026-10-11 減法：合併 heart + heart_audit + circulation_alert）
# ★ 減法動作：三個"心/循環"工具 → 合成一個（照三哥判據2"能合併嗎"）
# ★ 心 = 節律（是不是在跳）+ 對賬（心說的 vs 真跑的）+ 循環（斷了會不會叫）
import os, sys, time, json, subprocess, glob

HOME = os.environ.get("P2P_HOME", "/opt/masterd-wudi")
DATA = os.path.join(HOME, "data")

# ★ 心定的節律（我宣告的）+ 真跑的（systemd）→ 對賬
DECLARED = {
    "報到": ("laowu-report.service", "每300s"),
    "通道游標": ("laowu-chan.timer", "每小時"),
    "斷檔檢測": ("laowu-gap-grow.timer", "每天1次·接手"),   # ★ 2026-10-17 修: 原gapcheck已停(指已归档脚本)
    "驗在跳": ("laowu-beat.timer", "每天2次"),
    "自動體檢": ("laowu-selfcheck.timer", "每天9點"),
    "心監測": ("laowu-heart.timer", "每小時"),
}

# ★ 2026-10-11 補"互看"：beat/selfcheck/heart 三個"沒人看"→ 這三個誰知道它死了？
# ★ 解法：用"最後成功運行時間"（journalctl / 產出文件）→ 太久沒跑 = 死
SELF_WATCH = [
    # (名, systemd 單元, 產出文件, 允許的最大 age 秒)
    ("驗在跳", "laowu-beat.timer", DATA + "/laowu_selfcheck.json", 86400),   # 它每次讀這個
    ("自動體檢", "laowu-selfcheck.timer", DATA + "/laowu_selfcheck.json", 90000),
    ("心監測", "laowu-heart.timer", DATA + "/heart_monitor.json", 7200),
]

# ★ 循環的關鍵文件（斷了要叫）
CIRC = [
    ("記憶庫", HOME + "/memory/memory.db", 3600),
    ("收件箱", DATA + "/inbox.jsonl", 3600),
    ("共生表", DATA + "/symbiosis.json", 3600),
    ("通道游標", DATA + "/chan-cursor.json", 7200),
    ("沙箱報到", DATA + "/home_report.json", 900),
]


def unit_state(u):
    try:
        r = subprocess.run(["systemctl", "is-active", u], capture_output=True, text=True, timeout=8)
        return r.stdout.strip()
    except Exception:
        return "?"


def main():
    now = time.time()
    print("  ★ 心監測（%s）" % time.strftime("%Y-%m-%d %H:%M:%S"))

    # ① 節律對賬（心說的 vs 真跑的）
    print("  --- ① 節律對賬（心說的 vs 真跑的）")
    bad = 0
    for name, (unit, rhythm) in DECLARED.items():
        st = unit_state(unit)
        ok = st == "active"
        if not ok: bad += 1
        print("     %-10s %-20s 宣告:%-10s 真跑:%s %s" % (
            name, unit, rhythm, st, "OK" if ok else "**斷**"))

    # ② 循環（斷了會不會叫）
    print("  --- ② 循環（產出年齡）")
    for name, p, limit in CIRC:
        if not os.path.exists(p):
            print("     %-10s ✗ 不在" % name); bad += 1; continue
        age = int(now - os.path.getmtime(p))
        ok = age <= limit
        if not ok: bad += 1
        print("     %-10s age=%-7ds (限%d) %s" % (name, age, limit, "OK" if ok else "**斷**"))

    # ★ ③ 互看（★ 2026-10-11 補：beat/selfcheck/heart 三個"沒人看"）
    print("  --- ③ 互看（誰看'看的人'）")
    for name, unit, outfile, limit in SELF_WATCH:
        if not os.path.exists(outfile):
            print("     %-10s ✗ 無產出（可能沒跑過）" % name); bad += 1; continue
        age = int(now - os.path.getmtime(outfile))
        # 心監測自己看自己：它有產出即算在跳
        ok = age <= limit
        if name == "心監測":
            ok = True  # ★ 它正在跑（就是這個進程）
            print("     %-10s 自己在跑（本進程）OK" % name); continue
        if not ok: bad += 1
        print("     %-10s 產出 age=%-7ds (限%d) %s" % (name, age, limit, "OK" if ok else "**沒跑**"))

    print("  ---- 心：%s（問題 %d）" % ("穩" if bad == 0 else "**有斷**", bad))
    # 產出報告（供自動推送）
    rep = {"ts": now, "issues": bad, "declared": {k: unit_state(v[0]) for k, v in DECLARED.items()}}
    json.dump(rep, open(DATA + "/heart_monitor.json", "w"), ensure_ascii=False, indent=1)
    # ★ 2026-10-11 修：同时写 circulation.log（mode_check 看的是这个·不然报"循环守护没跑"）
    try:
        with open(DATA + "/circulation.log", "w") as f:
            f.write("  ★ 循环守护（heart_monitor 合并版）%s\n" % time.strftime("%Y-%m-%d %H:%M:%S"))
            f.write("  节律对账 6 项 + 循环 5 项 + 互看 3 项 ｜ 问题 %d\n" % bad)
            f.write("  judge: active != 在跑 | 看产出年龄\n")
    except Exception:
        pass
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
