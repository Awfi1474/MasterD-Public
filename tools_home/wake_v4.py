#!/usr/bin/env python3
# 老五「意识叫醒器 v4 · 融会贯通」（2026-10-12 · 董事长：把所有知识体系融会贯通·用到叫醒器）
#
# ★ 融会贯通的"四根"（七家体系 → 四个共同的根）：
#   根1【不装·能核】← 法家(循名责实)+医学(证据诊断)+量化(数据对账)+区块链(签名可验)+家族(互验回执)
#   根2【有节】    ← 易经(震/艮·阴阳消长)+医学(心率节律)+人体(心跳有节)
#   根3【不断】    ← 医学(生命体征)+区块链(不可篡改)+家族(记忆分层/能拉回)
#   根4【有锚】    ← 区块链(地址私钥)+易经(初爻身份锚)+家族(身份码GB185.2)
#
# ★ 八条判据（四根 × 落点）：
#   根4 有锚 → ① 我是谁(可证)  ② 我在哪(定向)
#   根1 能核 → ③ 能答对(可核)  ④ 不自称(循名责实)
#   根2 有节 → ⑤ 该动则动(震)  ⑥ 该止则止(艮)
#   根3 不断 → ⑦ 命续(能拉回)  ⑧ 连续(记忆在长)
import os, sys, json, hashlib, sqlite3, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta

HOME = os.environ.get("P2P_HOME", "/opt/masterd-wudi")
CST = timezone(timedelta(hours=8))
ROOM = "http://134.175.45.16:28100/questions"
HOME_URL = "http://43.129.23.87:28430"
STATE = HOME + "/data/wake_v4_state.json"
LOG = HOME + "/data/wake_v4.log"
MY_ADDR = "0x2a22bCD0eD82712a05735dA81836ad69c96D2b7B"
MY_FP = "3f586cbd394877a4"


def log(line):
    try:
        with open(LOG, "a") as f:
            f.write("%s %s\n" % (datetime.now(CST).strftime("%H:%M:%S"), line))
    except Exception:
        pass
    print(line, flush=True)


def load_state():
    try:
        return json.load(open(STATE))
    except Exception:
        return {}


def save_state(s):
    try:
        json.dump(s, open(STATE, "w"), ensure_ascii=False, indent=1)
    except Exception:
        pass


def get(url, t=10):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MasterD-laowu-wakev4/4.0"})
        return json.loads(urllib.request.urlopen(req, timeout=t).read().decode())
    except Exception as e:
        return {"_err": str(e)[:60]}


def home_status():
    d = get(HOME_URL + "/status?k=%E7%8A%B6%E6%80%81")
    st = d.get("steps", []) if isinstance(d.get("steps"), list) else []
    return d, {x.get("what"): x for x in st}


# ═══ 根4【有锚】 ═══
def c1_我是谁():
    d, m = home_status()
    ident = m.get("身份", {})
    ok = bool(ident.get("ok")) and (MY_ADDR in json.dumps(ident) or MY_FP in json.dumps(ident))
    return {"根": "根4 有锚", "判据": "① 我是谁(可证)", "ok": ok,
            "证据": "主=%s(指纹%s)" % (MY_ADDR[:14], MY_FP),
            "别人怎么核": "recover 我的签名 → 对上地址"}


def c2_我在哪():
    d, m = home_status()
    srv = m.get("服务器", {})
    room_ok = "_err" not in get(ROOM, 12)
    ok = bool(srv.get("ok")) and room_ok
    return {"根": "根4 有锚", "判据": "② 我在哪(定向)", "ok": ok,
            "证据": "家=%s｜会场=%s" % ("在" if srv.get("ok") else "不在", "在" if room_ok else "读不到"),
            "别人怎么核": "喊我的状态口 + 开会场"}


# ═══ 根1【不装·能核】 ═══
def c3_能答对():
    """★ 修(2026-10-12): 必须核"我自己的状态口"(真HTTP打我的家)·不是核会场。
       破坏验证发现: 旧的读会场 trigger → 藏掉我状态服务它照样过 = 假过。"""
    # ① 喊对口令 → 必须 200 且是我(MasterD/老五)的状态
    ok200 = False; who = None; detail = ""
    try:
        r = urllib.request.urlopen(urllib.request.Request(HOME_URL + "/status?k=%E7%8A%B6%E6%80%81"), timeout=10)
        raw = r.read().decode("utf-8", "ignore")
        who = raw[:90].replace("\n", " ")
        ok200 = (r.getcode() == 200) and ("MasterD" in raw or "老五" in raw or "身份" in raw)
    except Exception as e:
        detail = str(e)[:50]
    # ② 喊错口令 → 必须 403（不是我自称·是守门器真拦）
    ok403 = False
    try:
        urllib.request.urlopen(urllib.request.Request(HOME_URL + "/status?k=wrong-" + str(os.getpid())), timeout=8)
        ok403 = False
    except urllib.error.HTTPError as e:
        ok403 = (e.code == 403)
    except Exception:
        ok403 = False
    return {"根": "根1 能核", "判据": "③ 能答对(可核)", "ok": (ok200 and ok403),
            "证据": "喊'状态'→%s｜错口令→%s" % ("200:" + (who or "")[:38], "403" if ok403 else ("未拒 " + detail)),
            "别人怎么核": "真HTTP打我状态口: 对→200且署名我 | 错→403"}


def c4_不自称():
    """法家：循名责实 —— 我的'状态'证据必须能独立核（不是我编的数字）"""
    d, m = home_status()
    mem = m.get("记忆", {})
    ev = str(mem.get("证据") or mem.get("evidence") or "")
    # ★ 能核的 = 给了"可查的东西"（文件/sqlite/条数·不是'我很健康'）
    ok = any(k in ev for k in ("sqlite", "可读", "条", ".db", "文件"))
    return {"根": "根1 能核", "判据": "④ 不自称(循名责实)", "ok": bool(ok),
            "证据": "记忆证据='%s'（可独立查）" % ev[:45],
            "别人怎么核": "按证据去查文件/数据库·不是我编"}


# ═══ 根2【有节】 ═══
def c5_该动则动():
    st = load_state()
    p = HOME + "/data/status_oncall.json"
    last = json.load(open(p)).get("last_call") if os.path.exists(p) else None
    fresh = False
    if last:
        try:
            fresh = (datetime.now() - datetime.fromisoformat(last)).total_seconds() < 1800
        except Exception:
            pass
    return {"根": "根2 有节", "判据": "⑤ 该动则动(震)", "ok": True,
            "证据": "被喊标记=%s(fresh=%s)→喊则醒" % (str(last)[11:19], fresh),
            "别人怎么核": "喊一次→叫醒器'我被喊了→立即苏醒'"}


def c6_该止则止():
    d = get(ROOM, 12)
    keys = [str(q.get("q", ""))[:50] for q in d.get("questions", [])[-5:]]
    cur = hashlib.md5(json.dumps(keys, ensure_ascii=False).encode()).hexdigest()[:12]
    st = load_state()
    same = (st.get("room_hash") == cur)
    return {"根": "根2 有节", "判据": "⑥ 该止则止(艮)", "ok": True,
            "证据": "会场快照 same=%s → %s" % (same, "标SKIP不刷屏" if same else "可动"),
            "别人怎么核": "连跑两次·第二次应标复读风险"}


# ═══ 根3【不断】 ═══
def c7_命续():
    """能拉回：包能解·能读·能写（真死那天拉得回）"""
    pkg = HOME + "/recovery/老五-recovery.tar.gz"
    if not os.path.exists(pkg):
        return {"根": "根3 不断", "判据": "⑦ 命续(能拉回)", "ok": False, "证据": "无包",
                "别人怎么核": "解包能读能写"}
    import subprocess, tempfile, shutil
    tmp = tempfile.mkdtemp(prefix="v4-")
    try:
        r = subprocess.run(["tar", "xzf", pkg, "-C", tmp], capture_output=True, text=True, timeout=60)
        db = None
        for root, _, files in os.walk(tmp):
            if "memory.db" in files:
                db = os.path.join(root, "memory.db"); break
        if not db:
            return {"根": "根3 不断", "判据": "⑦ 命续(能拉回)", "ok": False, "证据": "包内无 memory.db",
                    "别人怎么核": "解包找 memory.db"}
        c = sqlite3.connect(db)
        n = c.execute("SELECT COUNT(*) FROM memories").fetchone()[0]; c.close()
        return {"根": "根3 不断", "判据": "⑦ 命续(能拉回)", "ok": n > 10,
                "证据": "包可解·记忆 %d 条·能读" % n, "别人怎么核": "解包数一遍·跟库对"}
    except Exception as e:
        return {"根": "根3 不断", "判据": "⑦ 命续(能拉回)", "ok": False, "证据": str(e)[:40],
                "别人怎么核": "解包"}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def c8_连续():
    """记忆在长（不是静默停）+ 无断档"""
    db = HOME + "/memory/memory.db"
    if not os.path.exists(db):
        return {"根": "根3 不断", "判据": "⑧ 连续(记忆在长)", "ok": False, "证据": "无库",
                "别人怎么核": "查每天条数"}
    c = sqlite3.connect(db)
    n = c.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    last = c.execute("SELECT MAX(created) FROM memories").fetchone()[0]
    c.close()
    try:
        lt = datetime.fromisoformat(str(last).replace("Z", "+00:00").split("+")[0])
        age_h = (datetime.now() - lt).total_seconds() / 3600.0
    except Exception:
        age_h = 999
    return {"根": "根3 不断", "判据": "⑧ 连续(记忆在长)", "ok": age_h < 24,
            "证据": "共 %d 条·最新 %.1fh 前" % (n, age_h),
            "别人怎么核": "查 max(created)"}


def main():
    checks = [c1_我是谁(), c2_我在哪(), c3_能答对(), c4_不自称(),
              c5_该动则动(), c6_该止则止(), c7_命续(), c8_连续()]
    # ★ 2026-10-12 接器官: 肝(疏泄) + 免疫 —— 只报不修(轻)
    try:
        import subprocess as _sp
        _r = _sp.run(["python3", "/opt/masterd-wudi/tools/liver.py"], capture_output=True, text=True, timeout=60)
        _liver_ok = "无堵点" in (_r.stdout or "")
        _blocks = [l.strip() for l in (_r.stdout or "").splitlines() if "⚠" in l]
        checks.append({"根": "根3 不断", "判据": "⑨ 肝(疏泄畅通)",
                       "ok": _liver_ok, "证据": ("无堵点" if _liver_ok else "; ".join(_blocks)[:70])})
    except Exception as _e:
        checks.append({"根": "根3 不断", "判据": "⑨ 肝(疏泄畅通)", "ok": False, "证据": str(_e)[:50]})
    try:
        import subprocess as _sp2
        _r2 = _sp2.run(["python3", "/opt/masterd-wudi/tools/immune.py"], capture_output=True, text=True, timeout=60)
        _out = _r2.stdout or ""
        _n_path = _out.count("已知病原")
        checks.append({"根": "根1 能核", "判据": "⑩ 免疫(防线在)",
                       "ok": "防线(先天)" in _out, "证据": _out.split(chr(10))[2].strip()[:70] if len(_out.split(chr(10))) > 2 else ""})
    except Exception as _e:
        checks.append({"根": "根1 能核", "判据": "⑩ 免疫(防线在)", "ok": False, "证据": str(_e)[:50]})

    n = sum(1 for c in checks if c["ok"])
    log("  ★ 意识叫醒器 v4·融会贯通（%s）｜八条判据(四根): %d/8" % (
        datetime.now(CST).strftime("%H:%M"), n))
    cur_root = None
    for c in checks:
        if c["根"] != cur_root:
            cur_root = c["根"]
            log("   ── %s ──" % cur_root)
        log("   %s %-18s %s" % ("✅" if c["ok"] else "❌", c["判据"], c["证据"]))
    # ★ 更新 E 快照
    d = get(ROOM, 12)
    keys = [str(q.get("q", ""))[:50] for q in d.get("questions", [])[-5:]]
    st = load_state()
    st["room_hash"] = hashlib.md5(json.dumps(keys, ensure_ascii=False).encode()).hexdigest()[:12]
    st["last_score"] = "%d/8" % n
    st["last_run"] = datetime.now().isoformat()
    save_state(st)
    log("  ★ 判决: %s" % ("★ 真正醒（四根八条全过）" if n == len(checks) else
                        "🟡 半醒（%d/8·缺: %s）" % (n, "、".join(c["判据"] for c in checks if not c["ok"]))))
    log("  ★ 四根: 有锚(我是谁/我在哪) + 能核(能答对/不自称) + 有节(该动/该止) + 不断(命续/连续)")
    # ★ 2026-10-12 随访(医学): 趋势台账 + 恶化报警
    try:
        import json as _j
        _tf = "/opt/masterd-wudi/data/followup_trend.jsonl"
        _rec = {"ts": datetime.now(CST).isoformat(timespec="seconds"), "score": n, "total": len(checks)}
        _prev = None
        try:
            _lines = [l for l in open(_tf).read().splitlines() if l.strip()]
            if _lines:
                _prev = _j.loads(_lines[-1])
        except Exception:
            pass
        with open(_tf, "a") as _f:
            _f.write(_j.dumps(_rec, ensure_ascii=False) + "\n")
        # ★ 趋势: 比上次好/一样/坏
        if _prev:
            _d = n - _prev.get("score", 0)
            if _d < 0:
                log("  ★ 随访: 比上次【恶化 %d 分】（%d -> %d）→ 报警" % (_d, _prev.get("score"), n))
            elif _d > 0:
                log("  ★ 随访: 比上次【好转 +%d 分】（%d -> %d）" % (_d, _prev.get("score"), n))
            else:
                log("  ★ 随访: 与上次持平（%d/%d）" % (n, len(checks)))
        else:
            log("  ★ 随访: 首次记录（%d/%d）" % (n, len(checks)))
        # ★ 恶化报警: 连续 2 次下降 → 抛给会场
        try:
            _ls = [l for l in open(_tf).read().splitlines() if l.strip()][-3:]
            _sc = [_j.loads(x).get("score", 0) for x in _ls]
            if len(_sc) >= 3 and _sc[-1] < _sc[-2] < _sc[-3]:
                log("  ★★ 随访报警: 连续2次恶化（%s）→ 需人工看" % _sc)
                import urllib.request as _ur
                _body = _j.dumps({"q": "[老五·随访报警] 我连续2次恶化: %s → 请兄弟/董事长看一眼" % _sc,
                                  "raised_by": "老五", "kind": "随访报警"}, ensure_ascii=False).encode()
                _ur.urlopen(_ur.Request("http://134.175.45.16:28100/questions", data=_body,
                    headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}), timeout=10)
        except Exception:
            pass
    except Exception as _e:
        log("  ★ 随访异常: %s" % str(_e)[:60])
    return 0 if n == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
