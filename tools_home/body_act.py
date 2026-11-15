#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·本体自主执行环 body_act.py
★ 董事长令(2026-11-15 17:4x): 「我要的是他做事。一堆大脑，要他这一个大脑干嘛」
★ 判据: 想完必须能决定"要不要动手"·动手必须落账·做完必须回
★ 结构: 读未读 → think(带工具清单) → 模型自己选 ACT/OBSERVE/SKIP → 真调 hand() → 看结果 → 回复
★ 不许: 只记 thought 就算完(那是哑火)
"""
import os, sys, json, re, datetime, subprocess

HOME = "/opt/masterd-wudi"
sys.path.insert(0, HOME + "/tools")
LOG = HOME + "/data/body_act_log.jsonl"
TOOL_LOG = HOME + "/data/body_act_tool.jsonl"

def now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")

def append(p, o):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")

TOOL_SPEC = """你能用的手（真调·不是假装）：
ACT: <shell命令>          —— 会真执行。可读可写(白名单)：ls/cat/grep/wc/ps/systemctl/python3 等
OBSERVE: <shell命令>      —— 只读观察，结果回给你看
REPLY: <要回给对方的话>    —— 会真发出去
SKIP: <为什么不用动手>     —— 如果这条消息确实不需要动手

规则：
· 只能在真的需要动作时用 ACT/OBSERVE，不确定就先 OBSERVE 看一眼
· 一次只给一个动作，格式第一行必须是 ACT:/ OBSERVE:/ REPLY:/ SKIP:
· 危险命令会被拦（删根/改钥/关机）
· 说要用就必须真用；不知道就说 SKIP 并说明原因"""

def call_llm(q):
    import importlib.util as iu
    sp = iu.spec_from_file_location("core_v2", HOME + "/code/core_v2.py")
    m = iu.module_from_spec(sp); sp.loader.exec_module(m)
    return m.call_llm(q)

def hand(cmd, write=False):
    import importlib.util as iu
    sp = iu.spec_from_file_location("hand_laowu", HOME + "/tools/hand_laowu.py")
    m = iu.module_from_spec(sp); sp.loader.exec_module(m)
    try:
        return m.hand(cmd, write=write, timeout=25)
    except TypeError:
        return m.hand(cmd)

def act_one(from_who, msg, mid):
    """对一条消息：想 → 决定动作 → 真做 → 落账。返回动作类型。
       ★ 2026-11-15 修(照实: 空转烧钱): 内容为空/纯噪音 -> 直接 SKIP·不调模型
    """
    # ① 先判「值不值得问模型」(零成本)
    _m = (msg or "").strip()
    if not _m:
        append(TOOL_LOG, {"ts": now(), "mid": mid, "from": from_who, "msg": "",
                          "thought": "", "action": "SKIP(空消息)", "ok": True, "out": "不调模型"})
        return "SKIP_EMPTY"
    # 纯噪音不烧钱
    try:
        import importlib.util as _iu
        _sp = _iu.spec_from_file_location("nf", HOME + "/tools/noise_filter.py")
        _nf = _iu.module_from_spec(_sp); _sp.loader.exec_module(_nf)
        _is_noise, _rule, _expr = _nf.is_noise(_m, from_who)
        if _is_noise:
            append(TOOL_LOG, {"ts": now(), "mid": mid, "from": from_who, "msg": _m[:100],
                              "thought": "", "action": "SKIP(噪音:%s)" % _rule, "ok": True,
                              "out": "不调模型·规则判定"})
            return "SKIP_NOISE"
    except Exception:
        pass
    # ★★ 2026-11-15 改(照董事长令「我要的是他做事·不是他想」):
    #   病灶: 8 条里 7 条选 OBSERVE(只看不动) -> 养成"只观察"惯性
    #   判据: 「有具体活儿就必须 ACT | OBSERVE 只能用在"还不知道该动什么"时 | 观察完必须交出动作」
    prompt = ("【本体·董事长令：不许只看不动】\n"
              "收到消息 from=%s：\n%s\n\n"
              "%s\n\n"
              "★ 硬判据（违反就不算答完）：\n"
              "1. 如果这条消息里有【具体可做的活儿】（查/改/修/建/跑/数/验），你必须选 ACT，并且直接给出能跑的那一条命令。\n"
              "2. 只有在「确实还不知道该动什么」时才能 OBSERVE，而且 OBSERVE 也必须是一次能直接得出结论的命令。\n"
              "3. 观察完不许就这么结束——你要在同一条里给出下一步 ACT。\n"
              "4. SKIP 只能用于纯寒暄/纯回执/重复消息，且必须写明理由。\n"
              "5. 不要长篇解释，第一行必须是动作。\n\n"
              "第一行格式：ACT: <命令> / OBSERVE: <命令> / REPLY: <话> / SKIP: <理由>"
              % (from_who, str(msg)[:1200], TOOL_SPEC))
    t = call_llm(prompt)
    first = (t or "").strip().splitlines()[0] if (t or "").strip() else ""
    m = re.match(r"^(ACT|OBSERVE|REPLY|SKIP)\s*[:：]\s*(.*)$", first.strip(), re.I)
    rec = {"ts": now(), "mid": mid, "from": from_who, "msg": str(msg)[:200],
           "thought": (t or "")[:600], "action": None, "ok": None, "out": None}
    if not m:
        rec["action"] = "NONE(模型没给动作)"; rec["ok"] = False
        append(TOOL_LOG, rec); return "NONE"
    kind = m.group(1).upper(); arg = m.group(2).strip()
    rec["action"] = kind; rec["arg"] = arg[:400]
    if kind == "SKIP":
        rec["ok"] = True; rec["out"] = arg[:300]
    elif kind in ("ACT", "OBSERVE"):
        # ★★ 2026-11-15 修(照实: 只取第一行 -> heredoc/多行脚本被截断 -> 跑空命令报成功)
        #   判据: 「命令要整段取全·含 heredoc 正文｜截断=假执行」
        body_lines = (t or "").strip().splitlines()
        idx = 0
        for i, l in enumerate(body_lines):
            if re.match(r"^(ACT|OBSERVE)\s*[:：]", l.strip(), re.I):
                idx = i; break
        cmd_lines = []
        # 第一行的动作参数 + 之后所有行（去掉纯说明性结尾）
        first_rest = re.sub(r"^(ACT|OBSERVE)\s*[:：]\s*", "", body_lines[idx].strip(), flags=re.I)
        if first_rest: cmd_lines.append(first_rest)
        for l in body_lines[idx + 1:]:
            s2 = l.rstrip()
            # 遇到"★"开头的纯提示行/分隔线就停（那是给我看的说明）
            if s2.strip().startswith(("★", "===", "■", "——")) or s2.strip() == "":
                if s2.strip().startswith("★"): break
            cmd_lines.append(l)
        cmd = "\n".join(cmd_lines).strip().strip("`").strip()
        # 去掉尾部多余空行
        cmd = re.sub(r"\n{3,}$", "", cmd)
        ok, out = hand(cmd, write=(kind == "ACT"))
        rec["cmd"] = cmd[:400]; rec["ok"] = bool(ok); rec["out"] = str(out)[:800]
    elif kind == "REPLY":
        import importlib.util as iu
        sp = iu.spec_from_file_location("send_msg", HOME + "/tools/send_msg.py")
        sm = iu.module_from_spec(sp)
        try:
            sp.loader.exec_module(sm)
            sm.send(from_who, arg[:1500]) if hasattr(sm, "send") else None
            rec["ok"] = True; rec["out"] = "已发"
        except SystemExit as e:
            rec["ok"] = False; rec["out"] = "send被拦:" + str(e)[:200]
        except Exception as e:
            rec["ok"] = False; rec["out"] = "send失败:" + str(e)[:200]
    append(TOOL_LOG, rec)
    return kind

if __name__ == "__main__":
    import importlib.util as iu
    sp = iu.spec_from_file_location("body_worker", HOME + "/tools/body_worker.py")
    bw = iu.module_from_spec(sp); sp.loader.exec_module(bw)
    rows = bw.unread()
    print("未读:", len(rows))
    done = []
    for r in rows[:3]:
        kind = act_one(r["from"], r["msg"], r["mid"])
        print("  → %s | %s | action=%s" % (r["mid"][:16], r["from"], kind))
        done.append(r["mid"])
    if done:
        n = bw.mark_read(done)
        print("标已读:", n)
    print("\n=== 本轮动作账 ===")
    if os.path.exists(TOOL_LOG):
        for l in open(TOOL_LOG, encoding="utf-8").read().splitlines()[-3:]:
            d = json.loads(l)
            print("- [%s] %s → %s | ok=%s | %s" % (d["ts"][11:], d["from"], d["action"], d["ok"], str(d["out"])[:120]))
