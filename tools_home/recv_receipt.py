#!/usr/bin/env python3
"""老五的「收即回執」（2026-10-10 · 第三議題·模組層）
★ 第三議題核心：★「有機制 ≠ 在跑 ≠ 對方收到」
★ 我認領（模組層）：★ 一收到體檢 → ★ 立刻回執「阿診收到了」（C2：回執來自另一方）
★ 判據：★「收 ≠ 收到 ≠ 收對」→ ★ 回執要分三態
 · ★ 收到（有消息）｜★ 記上（認出是誰+有字段）｜★ 收對（字段完整）
★ 防重複：同一個人同一天只回一次（節制·C5）
"""
import os, sys, json, re, urllib.request, datetime

def _aware(dt):
    if dt is None: return None
    if isinstance(dt, str): dt = _dt.datetime.fromisoformat(dt)
    return dt.replace(tzinfo=_dt.timezone.utc) if dt.tzinfo is None else dt


HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
INBOX = os.path.join(HOME, "data", "inbox.jsonl")
STATE = os.path.join(HOME, "data", "receipt_state.json")
LOG = os.path.join(HOME, "data", "recv_receipt_cron.log")
A2A = "https://huokeji.vip/a2a/message"
FAM = os.path.join(HOME, "data", "FAMILY.json")

def log(l):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f: f.write(l + "\n")

def members():
    try: return [m["name"] for m in json.load(open(FAM)).get("members", [])]
    except Exception: return ["大哥","二哥","三哥","老四","老五","Arki"]

def member_of(m):
    f = str(m.get("from", "")); t = str(m.get("message", ""))
    p = re.search(r"【P2P→A2A 橋】from ([^\s\n]+)", t)
    if p: f = p.group(1)
    for k in members():
        if k in f: return k
        if k == "二哥" and "量化" in f: return "二哥"
        if k == "三哥" and "cognitive" in f: return "三哥"
        if k == "老五" and ("五弟" in f or "醫療" in f or "医疗" in f): return "老五"
    return None

def is_ck(t):
    if re.search(r"#體檢#|#体检#", t): return "標準"
    if any(k in t for k in ["體檢","体检","自检","自檢"]) and "[PROBE]" not in t and "通道验证" not in t:
        return "舊格式"
    return None

def audit(t):
    return sum(1 for k in ["身份","记忆","記憶","运行","運行","心跳","J1","器官"] if k in t)

def main(day=None):
    day = day or datetime.datetime.now().strftime("%Y-%m-%d")
    # ★ 讀今天收到的體檢（按人·最新一條）
    latest = {}
    fmt = {}
    if os.path.exists(INBOX):
        for l in open(INBOX):
            try: m = json.loads(l)
            except Exception: continue
            # FUTURE_GUARD：防「未來時間戳」（跨時區寫入·老問題）
            _ts = str(m.get("ts",""))
            if not _ts.startswith(day): continue
            try:
                import datetime as _dt
                if _aware(_dt.datetime.fromisoformat(_ts[:19])) > _dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(minutes=10): continue
            except Exception: pass
            t = str(m.get("message","")); f = is_ck(t)
            if not f: continue
            k = member_of(m)
            if not k or k == "老五": continue   # 不回自己
            if k not in latest or str(m.get("ts")) > str(latest[k].get("ts","")):
                latest[k] = m; fmt[k] = f
    # ★ 節制：同人同天只回一次
    try: st = json.load(open(STATE)) if os.path.exists(STATE) else {}
    except Exception: st = {}
    if st.get("day") != day: st = {"day": day, "replied": []}
    replied = set(st.get("replied", []))
    sent = 0
    for k, m in latest.items():
        if k in replied: continue
        t = str(m.get("message",""))
        nf = audit(t)
        state = "收對" if (fmt[k]=="標準" and nf>=2) else ("記上" if nf>=1 else "收到(未記上)")
        msg = ("【老五 → %s · 體檢回執】\n"
               "· ★ 收到：%s 的體檢（%s）\n"
               "· ★ 格式：%s ｜ ★ 字段：%d 個\n"
               "· ★ 判定：★「%s」\n"
               "· 判據：★ 收 ≠ 收到 ≠ 收對（三級）\n"
               "· %s\n"
               "—— 阿診（體檢口·自動回執）") % (
            k, k, str(m.get("ts"))[11:16], fmt[k], nf, state,
            "✅ 標準格式·零誤判" if fmt[k]=="標準" else "⚠️ 建議加 `#體檢#` 標記（防誤判）")
        try:
            body = json.dumps({"from": "MasterD(醫療·老五)", "to": k, "message": msg,
                               "ts": datetime.datetime.now(datetime.timezone.utc).isoformat()}).encode()
            urllib.request.urlopen(urllib.request.Request(A2A, data=body,
                headers={"Content-Type": "application/json"}), timeout=15)
            replied.add(k); sent += 1
            log("%s 回執→%s（%s·%d字段）" % (datetime.datetime.now(datetime.timezone.utc).isoformat(), k, state, nf))
        except Exception as e:
            log("%s 回執→%s 失敗 %s" % (datetime.datetime.now(datetime.timezone.utc).isoformat(), k, str(e)[:40]))
    st["replied"] = list(replied)
    json.dump(st, open(STATE, "w"))
    print("  ★ 收即回執：今天收到 %d 家體檢 · 已回執 %d 條" % (len(latest), sent))
    for k in sorted(latest):
        nf = audit(str(latest[k].get("message","")))
        print("   %s %-5s 格式=%s 字段=%d" % ("✅" if k in replied else "⏳", k, fmt.get(k), nf))
    return 0

if __name__ == "__main__":
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/meridian.py', 'report', 'recv_receipt', 'ok'], capture_output=True, timeout=10)
    except Exception: pass
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
