#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·用量闸 token_guard.py
★ 董事长令(2026-11-15): 路线1(规则优先·不烧钱) + 路线3(每日硬上限·超了就停)
★ 判据: 「不知道花了多少 = 没闸｜花到上限还在调 = 失控」

功能:
  ① 每次模型调用记一条账(provider/model/输入token/输出token/估算花费)
  ② 每日累计花费；超过 DAILY_LIMIT_YUAN 直接拒绝调用
  ③ 统计接口: today_spent() 给巡检用
"""
import os, json, datetime, hashlib

HOME = "/opt/masterd-wudi"
LEDGER = HOME + "/data/llm_usage.jsonl"
LIMIT_FILE = HOME + "/data/llm_daily_limit.json"

DEFAULT_DAILY_LIMIT = 5.0      # 元/天

# 公开价（元/百万 token），用于估算
PRICE = {
    "doubao":  {"in": 0.8, "out": 2.0},
    "deepseek": {"in": 2.0, "out": 8.0},
}

def today():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%d")

def now_iso():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")

def get_limit():
    try:
        return float(json.load(open(LIMIT_FILE))["limit_yuan"])
    except Exception:
        return DEFAULT_DAILY_LIMIT

def set_limit(v):
    os.makedirs(os.path.dirname(LIMIT_FILE), exist_ok=True)
    json.dump({"limit_yuan": float(v), "ts": now_iso()}, open(LIMIT_FILE, "w"), ensure_ascii=False)

def _rows(day=None):
    day = day or today()
    out = []
    if not os.path.exists(LEDGER):
        return out
    for l in open(LEDGER, encoding="utf-8", errors="ignore"):
        if not l.strip():
            continue
        try:
            d = json.loads(l)
        except Exception:
            continue
        if str(d.get("day")) == day:
            out.append(d)
    return out

def today_spent(day=None):
    return round(sum(float(d.get("cost", 0)) for d in _rows(day)), 4)

def today_calls(day=None):
    return len(_rows(day))

def avg_cost(n=50):
    """★ 按最近 n 次实际花费求平均(不许用拍脑袋的估算)"""
    rows = _rows()
    if not rows:
        return 0.008
    recent = rows[-n:]
    return round(sum(float(r.get("cost", 0)) for r in recent) / len(recent), 6)


def allowed(est_cost=None):
    """调用前检查: 未超上限才放行
       ★ 2026-11-15 修(照实): 估算按近期实际平均·留 20% 余量
    """
    lim = get_limit()
    spent = today_spent()
    if est_cost is None:
        est_cost = max(0.008, avg_cost() * 1.2)     # 实际平均 + 20% 余量
    if spent + est_cost > lim:
        return False, ("🔴 今日已花 ¥%.2f + 本次估 ¥%.4f > 上限 ¥%.2f -> 拒绝调用"
                       % (spent, est_cost, lim))
    return True, "ok(已花 ¥%.2f / ¥%.2f·本次估 ¥%.4f)" % (spent, lim, est_cost)

def record(provider, model, in_chars, out_chars, ok=True, note=""):
    """记一条。token≈字符数/1.6（中文粗估）"""
    p = PRICE.get(provider, {"in": 1.0, "out": 3.0})
    tin = max(1, int(in_chars / 1.6))
    tout = max(1, int(out_chars / 1.6))
    cost = (tin / 1_000_000.0) * p["in"] + (tout / 1_000_000.0) * p["out"]
    rec = {"ts": now_iso(), "day": today(), "provider": provider, "model": model,
           "in_chars": in_chars, "out_chars": out_chars,
           "in_tok": tin, "out_tok": tout, "cost": round(cost, 6),
           "ok": ok, "note": str(note)[:100]}
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "set":
        set_limit(sys.argv[2])
        print("上限已设:", get_limit(), "元/天")
    else:
        print("今日花费: ¥%.4f | 调用: %d 次 | 上限: ¥%.2f"
              % (today_spent(), today_calls(), get_limit()))
        ok, msg = allowed()
        print("放行?", ok, msg)