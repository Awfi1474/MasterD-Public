#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""task_finder.py —— 执行系统的任务发现器（★ 2026-10-25）
================================================================
★ 董事长问: 「执行系统应该怎么发现任务？主要处理哪些问题？」
★ 认知系统辨出: 机制不通（35个零散cron全绕开决策系统）
★ 定位: 执行系统不自己想任务·但能「自己发现该修什么」
★ 四个任务源:
    ① 显式任务（董事长/我下达）—— 不归本器管
    ② 巡检任务（自检发现的问题）—— 本器扫 guard_all/verify_system 的报错
    ③ 防重犯任务（exec_fail 失败留痕）—— 本器扫记忆库
    ④ 收编任务（35个零散cron）—— 本器扫 /etc/cron.d 找没过决策系统的
★ 用法:
    python3 task_finder.py            # 扫全部四个源·列任务清单
    python3 task_finder.py fail       # 只扫失败重犯
    python3 task_finder.py cron       # 只扫零散cron
"""
import os, sys, json, sqlite3, subprocess, datetime

def _resolve_home():
    for _k in ("MD_HOME", "MEM_HOME", "P2P_HOME"):
        _v = os.environ.get(_k)
        if _v and os.path.isdir(os.path.join(_v, "memory")):
            return _v
    for _p in ("/opt/masterd-wudi", "/app/workspace/brain"):
        if os.path.isdir(os.path.join(_p, "memory")):
            return _p
    return "/app/workspace/brain"

HOME = _resolve_home()
DB = os.path.join(HOME, "memory", "memory.db")
OUT = os.path.join(HOME, "data", "task_finder.jsonl")

def _now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")

def find_fail_repeats():
    """③ 防重犯任务：扫 exec_fail 失败留痕"""
    print("════ ③ 扫失败重犯（记忆库 exec_fail）════")
    tasks = []
    try:
        c = sqlite3.connect("file:" + DB + "?mode=ro", uri=True, timeout=10)
        rows = c.execute("SELECT ts,title,body FROM memories WHERE subkind='exec_fail' ORDER BY id DESC LIMIT 50").fetchall()
        c.close()
        if not rows:
            print("  ✅ 无失败留痕")
            return tasks
        print("  近 50 条失败留痕:", len(rows))
        seen = {}
        for ts, title, body in rows:
            key = str(title)[:40]
            seen.setdefault(key, []).append(ts)
        for k, v in seen.items():
            if len(v) >= 2:
                print("  🔴 重犯 %d 次: %s" % (len(v), k))
                tasks.append({"源": "③防重犯", "任务": "修重犯: " + k, "次数": len(v), "最近": v[0]})
            else:
                print("     · 出现 %d 次: %s" % (len(v), k))
        print("  → 重犯任务 %d 条" % len(tasks))
    except Exception as e:
        print("  🟡 读库失败:", str(e)[:60])
    return tasks

def find_loose_crons():
    """④ 收编任务：扫 /etc/cron.d 找不经过决策系统的"""
    print("════ ④ 扫零散 cron（不经过决策系统的）════")
    tasks = []
    d = "/etc/cron.d"
    if not os.path.isdir(d):
        print("  （当前环境无 /etc/cron.d）")
        return tasks
    try:
        files = [f for f in os.listdir(d) if f.startswith("masterd")]
        print("  masterd 相关 cron 文件: %d 个" % len(files))
        for f in sorted(files):
            p = os.path.join(d, f)
            try:
                txt = open(p, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            if "exec_system" in txt or "link_duo" in txt or "decide_gate" in txt or "guard_all" in txt:
                continue  # 已经过决策系统的跳过
            if "disabled" in f:
                continue
            # 取出执行的脚本名
            import re
            m = re.findall(r"python3\s+(\S+\.py)", txt)
            script = os.path.basename(m[0]) if m else "?"
            print("  🔴 没过决策系统: %-28s → %s" % (f, script))
            tasks.append({"源": "④收编", "任务": "收编cron: " + f, "脚本": script})
        print("  → 收编任务 %d 条" % len(tasks))
    except Exception as e:
        print("  🟡 扫描失败:", str(e)[:60])
    return tasks

def find_self_check_issues():
    """② 巡检任务：跑 guard_all / verify_system 看有没有报错"""
    print("════ ② 跑自检找问题 ════")
    tasks = []
    for cmd, name in [([sys.executable, os.path.join(HOME, "tools", "guard_all.py")], "guard_all"),
                      ([sys.executable, os.path.join(HOME, "tools", "verify_system.py"), "all"], "verify_system")]:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            out = (r.stdout or "") + (r.stderr or "")
            bad = [ln.strip() for ln in out.split("\n") if "🔴" in ln or "不属实" in ln or "缺失" in ln]
            if bad:
                print("  🔴 %s 报 %d 个问题:" % (name, len(bad)))
                for b in bad[:5]: print("     " + b)
                tasks.append({"源": "②巡检", "任务": name + " 报错", "详情": bad[:3]})
            else:
                print("  ✅ %s 无报错" % name)
        except Exception as e:
            print("  🟡 %s 跑失败: %s" % (name, str(e)[:40]))
    return tasks

def main():
    print("★ 执行系统·任务发现器 @ " + _now())
    print("  HOME =", HOME)
    print()
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    tasks = []
    if mode in ("all", "self"):   tasks += find_self_check_issues()
    if mode in ("all", "fail"):   tasks += find_fail_repeats()
    if mode in ("all", "cron"):   tasks += find_loose_crons()
    print()
    print("★ 发现任务总数: %d" % len(tasks))
    if tasks:
        try:
            os.makedirs(os.path.dirname(OUT), exist_ok=True)
            with open(OUT, "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": _now(), "任务数": len(tasks), "任务": tasks}, ensure_ascii=False) + "\n")
            print("  ✅ 已记进台账:", OUT)
        except Exception as e:
            print("  🟡 记账失败:", str(e)[:60])
    return 0 if not tasks else 2

if __name__ == "__main__":
    sys.exit(main())
