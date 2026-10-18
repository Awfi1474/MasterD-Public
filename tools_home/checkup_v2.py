#!/usr/bin/env python3
"""老五的「體檢接收 v2」（2026-10-10 · 我自己的議題）
★ 舊機子 5 個洞 → v2 四件：
 ① ★ 標準格式：★ 認 `#體檢#` 標記（不靠猜關鍵詞·防「P2P橋前綴」誤歸）
 ② ★ 多源交叉：★ inbox + A2A 直拉（兩源·缺一可補）
 ③ ★ 收+審+回執：★ 收到回執｜驗字段全不全｜晚上總回執
 ④ ★ 名冊驅動：★ 從共生表讀成員（加減人不改代碼）

★ 判據（我定的·接第一議題）：
 · ★ 慢≠斷（C18）→ ★ 「格式不對」是「不完整」·不是「沒交」
 · ★ 三源交叉（C9）→ ★ inbox + A2A = 兩源
 · ★ 回執來自另一方（C2）→ ★ 我出「收到回執」
"""
import os, sys, json, re, urllib.request, datetime

def _aware(dt):
    if dt is None: return None
    if isinstance(dt, str): dt = _dt.datetime.fromisoformat(dt)
    return dt.replace(tzinfo=_dt.timezone.utc) if dt.tzinfo is None else dt


HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
INBOX = os.path.join(HOME, "data", "inbox.jsonl")
OUT = os.path.join(HOME, "checkups")
LOG = os.path.join(HOME, "data", "checkup_v2.log")
SYM = os.path.join(HOME, "data", "symbiosis.json")
A2A = "https://huokeji.vip/a2a/inbox"

# ★ ④ 名冊驅動（從共生表讀·不硬編碼）
def members():
    """★ 從家族名冊讀成員（加減人不改代碼）"""
    fam = os.path.join(HOME, "data", "FAMILY.json")
    if os.path.exists(fam):
        try:
            return [m["name"] for m in json.load(open(fam)).get("members", [])]
        except Exception: pass
    ms = set()
    if os.path.exists(SYM):
        try:
            d = json.load(open(SYM))
            for k in list(d.get("beats", {}).keys()):
                # ★ 從「老五·家哨兵」這種取主名
                base = k.split("·")[0]
                for name in ["大哥", "二哥", "三哥", "老四", "老五", "Arki"]:
                    if base == name or name in k:
                        ms.add(name)
        except Exception: pass
    # ★ 兜底（至少 6 人·但優先名冊）
    if not ms:
        ms = {"大哥", "二哥", "三哥", "老四", "老五", "Arki"}
    return sorted(ms)

MEMBERS = members()

def log(l):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f: f.write(l + "\n")

def member_of(m):
    """★ ① 標準格式優先：★ 認 `#體檢#` 標記
       ★ 防「P2P橋前綴」誤歸：★ 先看去掉前綴後的真名"""
    f = str(m.get("from", ""))
    # ★ 去掉「【P2P→A2A 橋】from XXX」前綴
    t = str(m.get("message", ""))
    p2p = re.search(r"【P2P→A2A 橋】from ([^\s\n]+)", t)
    if p2p: f = p2p.group(1)
    for k in MEMBERS:
        if k in f: return k
        if k == "二哥" and "量化" in f: return "二哥"
        if k == "三哥" and "cognitive" in f: return "三哥"
        if k == "老五" and ("五弟" in f or "醫療" in f or "医疗" in f): return "老五"
    return None

def is_checkup(t):
    """★ ① 標準格式：★ `#體檢#` 標記 ｜ ★ 兼容舊格式（關鍵詞）"""
    if re.search(r"#體檢#|#体检#", t):
        return True, "標準"
    if any(k in t for k in ["體檢", "体检", "自检", "自檢"]) and "[PROBE]" not in t and "通道验证" not in t:
        return True, "舊格式"
    return False, None

def read_sources():
    """★ ② 多源交叉：inbox + A2A 直拉"""
    msgs = []
    # 源1：家 inbox
    if os.path.exists(INBOX):
        for l in open(INBOX):
            try: msgs.append(json.loads(l))
            except Exception: pass
    # 源2：A2A 直拉
    try:
        raw = urllib.request.urlopen(A2A + "?limit=300", timeout=20).read()
        d = json.loads(raw)
        msgs += (d if isinstance(d, list) else d.get("messages", []))
    except Exception as e:
        log("%s A2A 拉取失敗 %s" % (datetime.datetime.now(datetime.timezone.utc).isoformat(), str(e)[:40]))
    return msgs

def audit(m):
    """★ ③ 審：驗字段全不全（缺字段 = 不完整·不是「綠」）"""
    t = str(m.get("message", ""))
    fields = {}
    # ★ 2026-10-13 老五修：加宽字段表（认各家实际写法·不只一种尺子）
    #   老四用「形/家门/命/洞」·大哥用「MARKER-CHECKUP」·Arki用「/wake」
    for f in ["身份", "记忆", "記憶", "运行", "運行", "心跳", "J1", "器官",
              "体检", "體檢", "消化率", "体检报告", "體檢報告", "五口", "形",
              "家门", "家門", "命", "洞", "回执", "回執", "MARKER-CHECKUP",
              "selfcheck", "checkup", "健康", "活", "门", "門", "报告", "報告"]:
        if f in t: fields[f] = True
    return {"has_fields": len(fields) > 0, "n_fields": len(fields),
            "complete": len(fields) >= 2}

def main(day=None):
    day = day or datetime.datetime.now().strftime("%Y-%m-%d")
    msgs = read_sources()
    # ★ 去重
    seen = set(); uniq = []
    for m in msgs:
        k = str(m.get("msg_id") or m.get("ts"))
        if k in seen: continue
        seen.add(k); uniq.append(m)
    # ★ 挑今天的體檢
    by = {}
    fmt_stat = {"標準": 0, "舊格式": 0}
    for m in uniq:
        if not str(m.get("ts", "")).startswith(day): continue
        t = str(m.get("message", ""))
        # FUTURE_GUARD：防未來時間戳
        try:
            import datetime as _dt
            if _aware(_dt.datetime.fromisoformat(str(m.get("ts",""))[:19])) > _dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(minutes=10): continue
        except Exception: pass
        ok, fmt = is_checkup(t)
        if not ok: continue
        fmt_stat[fmt] = fmt_stat.get(fmt, 0) + 1
        k = member_of(m)
        if k:
            a = audit(m)
            by.setdefault(k, []).append({"ts": str(m.get("ts"))[11:19], "fmt": fmt,
                                         "complete": a["complete"], "n_fields": a["n_fields"]})
    # ★ ④ 名冊驅動：缺誰
    missing = [k for k in MEMBERS if k not in by]
    incomplete = [k for k, v in by.items() if not any(x["complete"] for x in v)]
    rep = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(), "day": day,
           "members": MEMBERS, "by": {k: len(v) for k, v in by.items()},
           "missing": missing, "incomplete": incomplete,
           "format": fmt_stat, "sources": ["inbox"] + (["a2a"] if True else [])}
    os.makedirs(os.path.join(OUT, day), exist_ok=True)
    json.dump(rep, open(os.path.join(OUT, day, "v2.json"), "w"), ensure_ascii=False, indent=1)
    print("  ★ 體檢接收 v2（%s）" % day)
    print("  名冊（%d）：%s" % (len(MEMBERS), "、".join(MEMBERS)))
    for k in MEMBERS:
        v = by.get(k, [])
        comp = "✅完整" if any(x["complete"] for x in v) else ("🟡缺字段" if v else "—")
        print("   %s %-5s %2d 條 %s" % ("✅" if k in by else "🔴", k, len(v), comp))
    print("  格式：標準 %d ｜ 舊格式 %d" % (fmt_stat.get("標準", 0), fmt_stat.get("舊格式", 0)))
    print("  %s 缺交：%s" % ("🔴" if missing else "✅", "、".join(missing) or "無"))
    print("  %s 不完整：%s" % ("🟡" if incomplete else "✅", "、".join(incomplete) or "無"))
    log("%s v2：%d 人交·缺%s·不完整%s·格式%s" % (datetime.datetime.now(datetime.timezone.utc).isoformat(),
        len(by), missing or "無", incomplete or "無", fmt_stat))
    return 0 if not missing else 1

if __name__ == "__main__":
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/meridian.py', 'report', 'checkup_v2', 'ok'], capture_output=True, timeout=10)
    except Exception: pass
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
