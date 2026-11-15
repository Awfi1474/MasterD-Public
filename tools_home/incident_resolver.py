#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·异常处置器 incident_resolver.py —— A 的核心: 遇到判断类问题·按四层找答案
★ 董事长令(2026-11-15): 开 A·但按「查→卡→兄弟→官方→模型」顺序省钱
★ 判据: 「先试¥0的·答不出才花钱｜每次判断有预算上限」
★ 5.必守: ① 只修可逆的(备份+验证+回滚) ② 风险大的只报不动 ③ 三样齐才报成功

流程(每一层都留账):
  ① 查知识卡   → 命中就照卡做(¥0)
  ② 问兄弟     → 问一次·等回信(¥0)
  ③ 拉官方原文 → 拉回来自己看(¥0·拉取)
  ④ 调模型判断 → 只有前三层都答不出才用(¥0.006·有预算)
"""
import os, sys, json, datetime, importlib.util

HOME = "/opt/masterd-wudi"
sys.path.insert(0, HOME + "/tools")
LOG = HOME + "/data/incident_resolve.jsonl"
BUDGET_FILE = HOME + "/data/resolve_budget.json"
PER_CASE_BUDGET = 0.05      # 每个案件最多花 ¥0.05

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")

def load(n, p):
    sp = importlib.util.spec_from_file_location(n, p)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m

def _log(o):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")

def resolve(task):
    """处置一张单·返回 (是否解决, 说明, 花了几层)"""
    chk = task.get("chk", "")
    act = task.get("action", "")
    ev = task.get("evidence", "")
    trail = []
    rec = {"ts": ts(), "id": task.get("id"), "chk": chk, "layers": trail}

    # ===== 第1层: 查知识卡(¥0) =====
    try:
        kc = load("kc", HOME + "/tools/know_cards.py")
        kc.seed()
        hits = kc.find("%s %s" % (chk, act))
        if hits:
            trail.append({"layer": 1, "查卡": True, "命中": hits[0]["title"],
                          "规则": hits[0]["rule"], "来源层": "L1(卡片·有出处)"})
            rec["answer_source"] = "卡片:" + hits[0]["title"]
            rec["answer_layer"] = "L1"
            rec["rule"] = hits[0]["rule"]
            _log(rec)
            return True, "卡片命中: " + hits[0]["title"], trail
        trail.append({"layer": 1, "查卡": True, "命中": None})
    except Exception as e:
        trail.append({"layer": 1, "err": str(e)[:60]})

    # ===== 第2层: 问兄弟(¥0) =====
    try:
        ap = load("ap", HOME + "/tools/ask_peer.py")
        q = "【老五求助】%s 出问题了: %s。证据: %s。你们家怎么处理的？短答一句。" % (chk, act, ev[:120])
        r = ap.ask("老三", q)          # 先问老三(最爱较真·答案质量高)
        trail.append({"layer": 2, "问兄弟": "老三", "ok": r.get("ok"),
                      "resp": str(r.get("resp") or r.get("err"))[:200],
                      "来源层": "L2(兄弟回信·未自验)"})
        if r.get("ok"):
            rec["answer_source"] = "问兄弟:老三(等回信)"
            rec["answer_layer"] = "L2"
            _log(rec)
            return False, "已问老三·等回信", trail       # 不等·记下等回信
    except Exception as e:
        trail.append({"layer": 2, "err": str(e)[:60]})

    # ===== 第3层: 拉官方(¥0拉取·但要知道查哪) =====
    try:
        wl = load("wl", HOME + "/tools/web_lookup.py")
        hint = wl.search_hint("%s %s" % (chk, act))
        if hint.get("official_candidates"):
            trail.append({"layer": 3, "候选官方": hint["official_candidates"][:2]})
            rec["official_hints"] = hint["official_candidates"][:2]
    except Exception as e:
        trail.append({"layer": 3, "err": str(e)[:60]})

    # ===== 第4层: 调模型(要花钱·有预算) =====
    spent = 0.0
    try:
        b = json.load(open(BUDGET_FILE)) if os.path.exists(BUDGET_FILE) else {"spent": 0.0, "day": ts()[:10]}
        if b.get("day") != ts()[:10]:
            b = {"spent": 0.0, "day": ts()[:10]}
        if b.get("spent", 0) + 0.01 > PER_CASE_BUDGET * 4:
            trail.append({"layer": 4, "跳过": True, "reason": "案件预算已用 %.2f/%.2f" % (b["spent"], PER_CASE_BUDGET * 4)})
            rec["answer_source"] = "无(预算用尽)"
            _log(rec)
            return False, "预算用尽·报给董事长", trail
        core = load("core", HOME + "/code/core_v2.py")
        prompt = ("【异常处置·只答判断·不许长篇】\n"
                  "检查项: %s\n现象: %s\n证据: %s\n"
                  "可选官方线索: %s\n\n"
                  "照实答三句:\n"
                  "1. 最可能的原因(一句话)\n"
                  "2. 该做什么(一条可执行命令·若不确定就说「不确定·需人工」)\n"
                  "3. 这一步能不能回滚(能/不能·不能就别做)\n"
                  % (chk, act, ev[:200], rec.get("official_hints", [])))
        # 2026-11-15 接分级: 异常诊断需要完整判断 -> full 档
        ans = core.call_llm(prompt, level="full", hint=chk + " " + str(act)[:60])
        spent = 0.006
        b["spent"] = round(b.get("spent", 0) + spent, 4)
        json.dump(b, open(BUDGET_FILE, "w"))
        # ★ 接刹车(照本体判): L4 一律「猜·非定案」·执行前必须过 can_execute
        gate_result = None
        try:
            gt = load("gt", HOME + "/tools/gates.py")
            gate_result = gt.can_execute("L4", ans, "", "")
        except Exception as e:
            gate_result = {"allow": False, "why": "闸异常: " + str(e)[:60]}
        trail.append({"layer": 4, "调模型": True, "花费": spent,
                      "来源层": "L4(模型推断·猜·非定案)",
                      "闸": gate_result})
        rec["answer_source"] = "模型(猜·非定案)"
        rec["answer_layer"] = "L4"
        rec["model_answer"] = ans[:800]
        rec["executable"] = False
        rec["why_not_executable"] = "L4是猜·必须先实测验证成 L0 才能执行"
        _log(rec)
        return True, "【猜·非定案·不许直接执行】" + ans, trail
    except Exception as e:
        trail.append({"layer": 4, "err": str(e)[:80]})

    rec["answer_source"] = "无"
    _log(rec)
    return False, "四层都没答案·报董事长", trail

if __name__ == "__main__":
    print("incident_resolver 就绪·每案预算 ¥%.2f" % PER_CASE_BUDGET)