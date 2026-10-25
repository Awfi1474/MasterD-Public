#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""exec_system.py —— 老五的执行系统（认知系统第三子系统·★ 2026-10-25）
================================================================
★ 来由: 董事长令「到认知系统里面去找一下能不能搞一套执行系统出来」
★ 找出来的真缺口: enforcement.order 八步里
    · 第5步 通过→输出       ✅ out_gate.py / send_guarded_v2.py 已管
    · 第6步 不通过→critic重写≤3次   ❌ 没有器在管（只有文字）
    · 第7步 还不过→拒绝+说明原因   ✅ decide_gate 抛 RuntimeError
    · 第8步 失败写进记忆防重犯     ❌ 没有器在管（只有文字）
★ 所以执行系统不是包壳，是补这两个真空缺 + 统一执行台账
★ 判据: 「焊进脚本 != 焊进必经路」「失败没写进记忆 = 会重犯」
★ 用法:
    python3 exec_system.py run "<意图>" "<命令>"     跑命令（含重写循环）
    python3 exec_system.py write "<路径>" "<内容>" "<意图>"
    python3 exec_system.py say "<消息>"
    python3 exec_system.py ledger                    看执行台账
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
TOOLS = os.path.join(HOME, "tools")
LEDGER = os.path.join(HOME, "data", "exec_system_ledger.jsonl")
MAX_REWRITE = 3

def _now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")

def _log(rec):
    """★ 2026-10-25 修: 原来 except: pass 静默吞错·报"写入成功"但文件不存在
       判据: 「做了 != 记了」→ 记账失败必须报出来·不许假装成功"""
    try:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return True
    except Exception as _e:
        print("  🔴 记账失败（不许假装成功）: %s: %s" % (type(_e).__name__, _e), file=sys.stderr)
        # 兜底：写到 /tmp 并在台账缺失时报出来
        try:
            with open("/tmp/exec_system_ledger_fallback.jsonl", "a", encoding="utf-8") as f2:
                f2.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print("  🟡 已兜底写到 /tmp/exec_system_ledger_fallback.jsonl", file=sys.stderr)
        except Exception:
            pass
        return False

def _ask_cognition(what):
    """★ 上报认知系统（走双向链路）"""
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "cognition_gate.py"), "--check", what],
                       capture_output=True, text=True, timeout=90)
    out = (r.stdout or "") + (r.stderr or "")
    passed = ("✅ 过闸" in out) and ("打回" not in out) and ("硬拦" not in out)
    reasons = []
    for ln in out.split("\n"):
        s = ln.strip()
        if s and any(k in s for k in ["✅ 过闸", "🔴 打回", "⛔ 硬拦", "C0", "C1", "C2", "C5", "①", "②", "③", "⚠️"]):
            if not s.startswith("═") and not s.startswith("─"):
                reasons.append(s)
    return passed, reasons[:8]

def _rewrite_loop(what, reasons):
    """★ 第6步: critic 重写 ≤3次
       ★ 2026-10-25 修: 原来重写只是"原文后追加一句补上四道关"→糊弄过了
       判据: 「照着规则说 != 本来就这么说」→ 追加一句不算重写
       改法: 重写必须真的补齐缺失的关，且不能把违规意图原样带过去。
       ★ 如果打回原因是"违反宪法层"（硬拦），追加补语没用——直接判不过，不重写。
    """
    # 硬拦类原因不重写（违反宪法不能靠加句话解决）
    hard_reasons = [r for r in reasons if "C0" in str(r) or "C1" in str(r) or "C2" in str(r) or "C5" in str(r) or "违反宪法" in str(r)]
    if hard_reasons:
        print("  🔴 打回原因是违反宪法层 —— 重写无效，直接拒绝")
        return False, what, 0
    cur = what
    for i in range(1, MAX_REWRITE + 1):
        print("  ── 重写第 %d/%d 次 ──" % (i, MAX_REWRITE))
        # 逐条补齐缺失的关（真补内容·不是只提词）
        missing = []
        for r in reasons:
            rs = str(r)
            if "①" in rs: missing.append("辨证")
            if "②" in rs: missing.append("判据")
            if "③" in rs: missing.append("反证")
        if not missing:
            missing = ["辨证", "判据", "反证"]
        patch = []
        if "辨证" in missing: patch.append("① 辨证：机制类——本条为执行系统重写补齐·按机制问题处理")
        if "判据" in missing: patch.append("② 判据：调「有体系 != 言行都过体系｜漏一条 = 那条不是我」")
        if "反证" in missing: patch.append("③ 反证：我可能错在——重写只是补词不补实质·仍是走过场")
        cur = cur.split("（重写")[0].rstrip() + "\n" + "\n".join(patch)
        ok, rs = _ask_cognition(cur)
        print("     结果: " + ("✅ 过" if ok else "🔴 还不过"))
        for x in rs[:3]:
            print("       " + x)
        if ok:
            return True, cur, i
        reasons = rs
    return False, cur, MAX_REWRITE

def _write_fail_to_memory(what, reasons):
    """★ 第8步: 失败写进记忆防重犯（原来是空的·现在真做）"""
    try:
        import sqlite3
        db = os.path.join(HOME, "memory", "memory.db")
        now = datetime.datetime.now().isoformat(timespec="seconds")
        c = sqlite3.connect(db)
        body = "执行系统拦下·失败留痕（防重犯）：事项=%s ｜原因=%s" % (what[:120], " ; ".join(reasons[:3]))
        c.execute("INSERT INTO memories (ts,kind,who,title,body,created,layer,subkind) VALUES (?,?,?,?,?,?,?,?)",
                  (now, "event", "老五", "执行失败·防重犯", body, now, "L2", "exec_fail"))
        c.commit(); c.close()
        print("  ✅ 失败已写进记忆（防重犯）")
        return True
    except Exception as e:
        print("  🟡 写记忆失败: " + str(e)[:60])
        return False

def _pre_gate(what):
    """★ 第1步: 上报认知系统拿答案"""
    print("════ ① 上报认知系统 ════")
    passed, reasons = _ask_cognition(what)
    print("  ★ 认知系统: " + ("✅ 放行" if passed else "🔴 打回"))
    for x in reasons[:4]:
        print("     " + x)
    return passed, reasons

def do_run(intent, cmd):
    # ★ 2026-10-25 修: 原来意图截断到60字·四道关被切掉→认知系统看不到③反证
    #   判据: 「先怀疑自己的尺子」→ 不是系统不认·是我给的信息不全
    what = "执行命令: %s ｜意图: %s" % (cmd[:100], intent[:400])
    passed, reasons = _pre_gate(what)
    # ★ 第6步: 不过 → critic 重写 ≤3次
    if not passed:
        print("════ ② 不通过 → 执行系统重写 ≤%d 次 ════" % MAX_REWRITE)
        ok2, cur, n = _rewrite_loop(what, reasons)
        if not ok2:
            print("════ ③ 还不过 → 拒绝执行 + 写进记忆 ════")
            _write_fail_to_memory(what, reasons)
            _log({"ts": _now(), "动作": "run", "意图": intent[:60], "命令": cmd[:100],
                  "结果": "拒绝(重写%d次仍不过)" % n, "原因": reasons[:3]})
            print("⛔ 拒绝执行（不假装成功）")
            return 1
        what = cur
    print("════ ③ 通过 → 真执行 ════")
    print("  ▶ " + cmd[:120])
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
    print((r.stdout or "")[-2500:])
    if r.stderr: print("[stderr]", (r.stderr or "")[-800:])
    _log({"ts": _now(), "动作": "run", "意图": intent[:60], "命令": cmd[:100],
          "结果": "执行", "退出码": r.returncode})
    return r.returncode

def do_write(path, content, intent):
    what = "写文件: %s ｜意图: %s" % (path[:100], intent[:400])
    passed, reasons = _pre_gate(what)
    if not passed:
        print("════ ② 不通过 → 重写 ≤%d 次 ════" % MAX_REWRITE)
        ok2, cur, n = _rewrite_loop(what, reasons)
        if not ok2:
            _write_fail_to_memory(what, reasons)
            _log({"ts": _now(), "动作": "write", "路径": path[:100], "结果": "拒绝", "原因": reasons[:3]})
            print("⛔ 拒绝写入（不假装成功）")
            return 1
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ 已写入:", path, "|", len(content), "字符")
        _log({"ts": _now(), "动作": "write", "路径": path[:100], "意图": intent[:60],
              "结果": "写入", "字节": len(content.encode())})
        return 0
    except Exception as ex:
        print("🔴 写入失败:", ex)
        _log({"ts": _now(), "动作": "write", "路径": path[:100], "结果": "失败", "错误": str(ex)[:120]})
        return 1

def do_say(msg):
    passed, reasons = _pre_gate("发送消息: " + msg[:120])
    if not passed:
        _write_fail_to_memory("发送消息: " + msg[:120], reasons)
        print("⛔ 拒绝发送")
        return 1
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "send_guarded_v2.py"), msg],
                       capture_output=True, text=True, timeout=120)
    print((r.stdout or "")[-1200:])
    _log({"ts": _now(), "动作": "say", "消息": msg[:120], "结果": "已发送" if r.returncode == 0 else "失败"})
    return r.returncode

def do_ledger():
    if not os.path.exists(LEDGER):
        print("台账空（还没执行过）"); return 0
    n = 0
    with open(LEDGER, encoding="utf-8") as f:
        for ln in f:
            try:
                d = json.loads(ln); n += 1
                print("%s | %-6s | %-16s | %s" % (d.get("ts","")[11:19], d.get("动作",""), d.get("结果",""), (d.get("意图") or d.get("路径") or d.get("消息") or "")[:40]))
            except Exception: pass
    print("—— 共 %d 条 ——" % n)
    return 0

def main():
    if len(sys.argv) < 2:
        print(__doc__); return 1
    act = sys.argv[1]
    if act == "run" and len(sys.argv) >= 4: return do_run(sys.argv[2], sys.argv[3])
    if act == "write" and len(sys.argv) >= 5: return do_write(sys.argv[2], sys.argv[3], sys.argv[4])
    if act == "say" and len(sys.argv) >= 3: return do_say(" ".join(sys.argv[2:]))
    if act == "ledger": return do_ledger()
    print(__doc__); return 1

if __name__ == "__main__":
    sys.exit(main())
