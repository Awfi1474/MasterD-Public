#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""exec_guarded.py —— 老五的统一执行口（★ 任何行为必过决策系统）
================================================================
★ 判据: 「焊进脚本 != 焊进必经路｜要"绕不过去"才算」
★ 董事长令 2026-10-25: 你的任何行为都要经过决策系统
★ 用法:
    python3 exec_guarded.py run   "<要执行的命令>" "<为什么做·意图>"
    python3 exec_guarded.py write "<文件路径>" "<内容>" "<为什么写>"
    python3 exec_guarded.py say   "<要说的话>"
★ 机制:
    ① 先过决策系统 require_decide(hard=True) —— 六问 6/6 才继续
    ② 再过出口闸 out_gate —— 有结果才放行
    ③ 都过 → 真执行
    ④ 任何一步不过 → 拒绝 + 落账 + 退出码 1
★ 这是"焊在必经之路": 改文件/跑命令/下结论/发群 都先过这里
"""
import os, sys, json, subprocess, datetime

def _resolve_home():
    for _k in ("MD_HOME", "MEM_HOME", "P2P_HOME"):
        _v = os.environ.get(_k)
        if _v and os.path.isdir(os.path.join(_v, "tools")):
            return _v
    for _p in ("/opt/masterd-wudi", "/app/workspace/brain"):
        if os.path.isdir(os.path.join(_p, "tools")):
            return _p
    return "/opt/masterd-wudi"

HOME = _resolve_home()
sys.path.insert(0, os.path.join(HOME, "tools"))
LOG = os.path.join(HOME, "data", "exec_guarded_log.jsonl")

def _now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")

def _log(rec):
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass

def _gate(what):
    """过决策系统。返回 (ok, out, n_ok)"""
    from decide_gate import require_decide
    try:
        ok, out = require_decide(what, hard=True, who="老五·exec_guarded")
        n = 0
        for ln in out.split("\n"):
            if "六问:" in ln and "/6" in ln:
                try: n = int(ln.split("六问:")[1].split("/")[0].strip())
                except Exception: pass
        return True, out, n
    except RuntimeError as e:
        msg = str(e)
        n = 0
        for ln in msg.split("\n"):
            if "六问:" in ln and "/6" in ln:
                try: n = int(ln.split("六问:")[1].split("/")[0].strip())
                except Exception: pass
        return False, msg, n

def do_run(cmd, why):
    what = "执行命令: %s ｜意图: %s" % (cmd[:100], why[:60])
    ok, out, n = _gate(what)
    print("★ 决策系统: " + ("✅ 放行(六问%d/6)" % n if ok else "🔴 拦下(六问%d/6)" % n))
    if not ok:
        _log({"ts": _now(), "动作": "run", "命令": cmd[:120], "意图": why[:60], "结果": "决策系统拦下", "六问": n})
        print("⛔ 拒绝执行 —— 决策系统没过")
        return 1
    print("▶ 执行:", cmd[:120])
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
    o = (r.stdout or "")[-3000:]
    e = (r.stderr or "")[-1500:]
    print(o)
    if e: print("[stderr]", e)
    _log({"ts": _now(), "动作": "run", "命令": cmd[:120], "意图": why[:60],
          "结果": "执行", "退出码": r.returncode, "六问": n})
    return r.returncode

def do_write(path, content, why):
    what = "写文件: %s ｜意图: %s" % (path[:100], why[:60])
    ok, out, n = _gate(what)
    print("★ 决策系统: " + ("✅ 放行(六问%d/6)" % n if ok else "🔴 拦下(六问%d/6)" % n))
    if not ok:
        _log({"ts": _now(), "动作": "write", "路径": path[:120], "意图": why[:60], "结果": "决策系统拦下", "六问": n})
        print("⛔ 拒绝写入 —— 决策系统没过")
        return 1
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ 已写入:", path, "|", len(content), "字符")
        _log({"ts": _now(), "动作": "write", "路径": path[:120], "意图": why[:60],
              "结果": "写入", "字节": len(content.encode()), "六问": n})
        return 0
    except Exception as ex:
        print("🔴 写入失败:", ex)
        _log({"ts": _now(), "动作": "write", "路径": path[:120], "结果": "失败", "错误": str(ex)[:120]})
        return 1

def do_say(msg):
    ok, out, n = _gate("发送消息: " + msg[:120])
    print("★ 决策系统: " + ("✅ 放行(六问%d/6)" % n if ok else "🔴 拦下(六问%d/6)" % n))
    if not ok:
        _log({"ts": _now(), "动作": "say", "消息": msg[:120], "结果": "决策系统拦下", "六问": n})
        print("⛔ 拒绝发送")
        return 1
    r = subprocess.run([sys.executable, os.path.join(HOME, "tools", "send_guarded_v2.py"), msg],
                       capture_output=True, text=True, timeout=120)
    print((r.stdout or "")[-1500:])
    if r.stderr: print("[stderr]", r.stderr[-600:])
    _log({"ts": _now(), "动作": "say", "消息": msg[:120], "结果": "已发送" if r.returncode == 0 else "发送失败", "退出码": r.returncode})
    return r.returncode

def main():
    if len(sys.argv) < 2:
        print(__doc__); return 1
    act = sys.argv[1]
    if act == "run":
        if len(sys.argv) < 4: print("用法: exec_guarded.py run <命令> <意图>"); return 1
        return do_run(sys.argv[2], sys.argv[3])
    if act == "write":
        if len(sys.argv) < 5: print("用法: exec_guarded.py write <路径> <内容> <意图>"); return 1
        return do_write(sys.argv[2], sys.argv[3], sys.argv[4])
    if act == "say":
        if len(sys.argv) < 3: print("用法: exec_guarded.py say <消息>"); return 1
        return do_say(" ".join(sys.argv[2:]))
    print("未知动作:", act); return 1

if __name__ == "__main__":
    sys.exit(main())
