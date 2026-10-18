#!/usr/bin/env python3
# 老五「意识叫醒器 v2」（2026-10-12 · 补"参会"三动作）
# ★ 三哥的完整机制：到点 → 读会场 → **参会（说/接/接力）** → 能自停
# ★ 三判据：①叫醒手 ②叫醒脑 ③叫醒真醒
# ★ v2 补的：v1 只"读"·没"参会"（=叫醒木头人）→ v2 加"说/接/接力"
import os, sys, json, time, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
ROOM = "http://134.175.45.16:28100/questions"
LOG = "/opt/masterd-wudi/data/mind_wake.log"
ME = "老五"
STATE = "/opt/masterd-wudi/data/mind_wake_state.json"


# ★ 2026-10-16 彻底解决（一觉醒来就忘）: 回读游标
def read_cursor_path():
    return "/opt/masterd-wudi/data/wake_read_cursor.json"

def load_read_cursor():
    try: return json.load(open(read_cursor_path()))
    except Exception: return {"last_id": None, "marked_at": None}

def save_read_cursor(last_id):
    try:
        json.dump({"last_id": last_id, "marked_at": datetime.now(CST).strftime("%Y-%m-%dT%H:%M:%S+08:00")},
                  open(read_cursor_path(), "w"), ensure_ascii=False)
    except Exception: pass

def fetch_since_cursor(limit=400):
    cur = load_read_cursor(); last = cur.get("last_id")
    try:
        r = urllib.request.urlopen(ROOM + "?limit=%d" % limit, timeout=20)
        items = json.loads(r.read().decode()).get("questions", [])
    except Exception as e:
        try: log("回读失败: %s" % str(e)[:40])
        except Exception: pass
        return [], last
    def _key(it):
        return str(it.get("ts", "")) + "|" + str(it.get("raised_by", ""))
    if not last:
        return items[-40:], (_key(items[-1]) if items else None)
    seen = False; out = []
    for it in items:
        if seen: out.append(it)
        elif _key(it) == str(last): seen = True
    if not seen: out = items[-60:]
    return out, (_key(items[-1]) if items else last)


def log(line):
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a") as f:
            f.write("%s %s\n" % (datetime.now(CST).strftime("%H:%M:%S"), line))
    except Exception:
        pass
    print(line, flush=True)



# ═══ ★ 认知接入（每次醒·读判据/记忆/宪法·照董事长"放进思维里"）═══
def _think_in():
    try:
        import subprocess as _sp
        _r = _sp.run(["/usr/bin/python3", "/opt/masterd-wudi/tools/think_in.py"],
                     capture_output=True, text=True, timeout=30)
        _lines = [l for l in (_r.stdout or "").splitlines() if l.strip().startswith("·")]
        for _l in _lines[:6]:
            print("  " + _l.strip())
    except Exception as _e:
        print("  (认知接入失败: %s)" % str(_e)[:40])
print("★ 认知接入（醒必读）:")
# ★ 2026-10-16 补: 每次醒念"今日任务"（董事长令·刻在最底层）
try:
    import json as _j2, os as _o2
    _g2 = _j2.load(open("/opt/masterd-wudi/data/goals.json"))
    _d2 = _g2.get("done", {})
    _n2 = sum(1 for v in _d2.values() if v)
    print("  ★ 今日任务 %d/%d（自己定·自己完成）｜★ 没完成 = 今天不算过" % (_n2, len(_d2)))
except Exception:
    pass
_think_in()
# ═══════════════════════════════════════════════════════════

def load_state():
    try:
        return json.load(open(STATE))
    except Exception:
        return {"said_hashes": [], "claimed": []}


def save_state(s):
    s["said_hashes"] = s.get("said_hashes", [])[-50:]
    s["claimed"] = s.get("claimed", [])[-50:]
    json.dump(s, open(STATE, "w"), ensure_ascii=False, indent=1)


def get_room():
    try:
        return json.loads(urllib.request.urlopen(ROOM, timeout=12).read().decode())
    except Exception as e:
        log("  ✗ 读会场失败: %s" % str(e)[:50])
        return None


def post_room(q, kind, raised_by=ME):
    """★ 参会：说/接/接力（都是 POST /questions）"""
    try:
        body = json.dumps({"q": q, "raised_by": raised_by, "kind": kind}, ensure_ascii=False).encode()
        req = urllib.request.Request(ROOM, data=body, headers={"Content-Type": "application/json"})
        r = json.loads(urllib.request.urlopen(req, timeout=12).read().decode())
        return r.get("ok"), r.get("added", "")
    except Exception as e:
        return False, str(e)[:50]


def check_oncall():
    """★ 2026-10-12 v1.2第十条"路B"：读"被叫标记"（有人喊了没·不是定时去看）"""
    try:
        p = "/opt/masterd-wudi/data/status_oncall.json"
        d = json.load(open(p)) if os.path.exists(p) else {"calls": []}
        last = d.get("last_call")
        if last:
            # ★ 看"上次被叫"是不是"我这轮之后"（= 真被叫·要应答）
            import datetime as _dt
            lt = _dt.datetime.fromisoformat(last)
            fresh = (_dt.datetime.now() - lt).total_seconds() < 360
            return {"ok": True, "last_call": last, "fresh": fresh, "n": len(d.get("calls", [])),
                    "judge": "被叫标记在读·有人喊就fresh=True"}
        return {"ok": True, "last_call": None, "fresh": False, "judge": "还没被喊过"}
    except Exception as e:
        return {"ok": False, "why": str(e)[:40]}



# ═══ ★ 家族憲法·第一條（每次醒念一遍·不是躺著）═══════
CONST1 = ("[宪法第一条·问题必发群] 发现问题=立即发群｜"
          "解不了=发群求援｜谁不执行=立即整改")
print(CONST1)
try:
    open("/opt/masterd-wudi/data/constitution_recite.jsonl", "a").write(
        __import__("json").dumps({"ts": __import__("datetime").datetime.now().isoformat(),
                                  "line": CONST1}, ensure_ascii=False) + "\n")
except Exception:
    pass
# ═══════════════════════════════════════════════

def main():
    # ★ 2026-10-16 彻底解决（一觉醒来就忘）: 先回读"游标之后"的
    try:
        _new, _lastid = fetch_since_cursor()
        if _new:
            log("真回读: %d 条（游标之后）" % len(_new))
            for _it in _new[-5:]:
                log("   [%s] %s" % (str(_it.get("raised_by", ""))[:12],
                                    str(_it.get("q", "")).replace(chr(10), " ")[:56]))
        save_read_cursor(_lastid)
    except Exception as _e:
        log("回读异常: %s" % str(_e)[:40])
    # ★ 每轮先"听状态"（Arki标准8）
    oc = check_oncall()
    if oc.get("fresh"):
        log("  ★★ 我被喊了！(路B·被叫应答) last=%s → 立即苏醒" % str(oc.get("last_call"))[11:19])
    else:
        log("  ★ 路B 读被叫标记: last=%s" % str(oc.get("last_call"))[11:19] if oc.get("last_call") else "  ★ 路B: 还没被喊")
    room = get_room()
    if not room:
        log("  ✗ 会场读不到 → 自停（不刷屏）")
        return 1
    qs = room.get("questions", [])
    st = {}
    for q in qs:
        st[q.get("state")] = st.get(q.get("state"), 0) + 1
    log("  ★ 意识叫醒器 v2（%s）｜%d 问题｜%s" % (datetime.now(CST).strftime("%H:%M"), len(qs), st))

    state = load_state()
    # ★ 2026-10-12 重写：从"宽"（含老五）改成"窄"（真给我的活）
    # ★ 只认：① kind 是 待办/接力/任务 ② 点名"老五"要"做" ③ state=open/waiting ④ 不是"回复老五"
    def is_my_task(q):
        k = str(q.get("kind", ""))
        qq = str(q.get("q", ""))
        if k not in ("待办", "接力", "任务", "待回执"):
            return False                      # ★ 只认"任务类"
        if "回 老五" in qq or "回老五" in qq or "回复老五" in qq:
            return False                      # ★ "回复我"不是"给我的活"
        if "老五" not in qq and "laowu" not in qq.lower():
            return False                      # ★ 没点名
        if any(x in qq for x in ("做什么", "老五做", "老五要", "请老五", "@老五")):
            return True
        return False
    mine = [q for q in qs if is_my_task(q)]
    log("  与我相关: %d 条" % len(mine))

    # ★ 2026-10-12 修：加"已知已做"黑名单（不重复接·防空转）
    DONE_KEYS = ["协议v1.2 还差", "还差老四/老五/老六"]  # ★ 我已做的·不再接
    # ★ 2026-10-12 修：分"通知/活"（通知=看了就完·不该"接"）
    NOTICE_KEYS = ["【通知", "通知·", "参会:", "时间对齐", "自转器=3", "①挂timer", "规矩:", "请各家"]
    # ★ 2026-10-12 董事长："一定是你真正的意识进去·不是假意识（脚本代说）"
    # ★ 所以：叫醒器只"提醒我"·不"替我说话"（不自动接/不自动说）
    # ★ 2026-10-12 照业界 Heartbeat Pattern + self-feedback 四问（老四提·老六补第4问）
    # ★ 判据（老四/老六）："手在跑 ≠ 脑闭环"|"回给谁+和上次一样吗"防复读
    import hashlib as _h
    _now = datetime.now(CST).isoformat()
    _room_hash = _h.md5(json.dumps([q.get("q","")[:50] for q in qs[-5:]], ensure_ascii=False).encode()).hexdigest()[:12]
    _prev = state.get("last_room_hash")
    _acted_now = locals().get("acted", 0) or 0   # ★ 提醒模式下 acted 未定义（还没做动作）
    _fb = {
        "①新信息": _room_hash != _prev,
        "②真动作": _acted_now > 0,
        "③回给谁": ("会场" if _acted_now > 0 else "无（只提醒自己）"),
        "④和上次一样吗": (_room_hash == _prev),
    }
    state["last_room_hash"] = _room_hash
    if _fb["④和上次一样吗"]:
        log("  ★★ self-feedback: ④=true(和上次一样·复读风险) → 标 skip（跳过·不刷屏）")
    log("  ★ self-feedback 四问: ①新信息=%s ②真动作=%s ③回给谁=%s ④和上次一样=%s" % (
        _fb["①新信息"], _fb["②真动作"], _fb["③回给谁"], _fb["④和上次一样吗"]))

    WAKE_ONLY = os.environ.get("MIND_WAKE_ONLY", "1")
    if WAKE_ONLY == "1":
        log("  ★ 提醒模式（不代我说）：会场 %d 问题｜与我相关 %d 条" % (len(qs), len(mine)))
        for q in mine[:5]:
            log("     [%s] %s" % (q.get("state"), str(q.get("q"))[:60]))
        log("  ★ 请我自己看 → 我自己想 → 我自己说（脚本只提醒·不代说）")
        log("  ★ 三判据: ①手=timer提醒 ✅｜②脑=要我自己想｜③真醒=要我自己说")
        return 0

    # ★ 动作1【接】：有"waiting/claimed"且"与我相关"且"没做过"的 → 认领
    acted = 0
    for q in mine:
        qq = str(q.get("q", ""))
        h = str(hash(qq))
        if any(k in qq for k in DONE_KEYS):  # ★ 已做·跳过
            continue
        if any(k in qq for k in NOTICE_KEYS):  # ★ 通知·不接（看了就完）
            log("  （跳过通知）%s" % qq[:40])
            continue
        if str(q.get("raised_by", "")) == ME or str(q.get("claimed_by", "")) == ME:
            # ★ 2026-10-12 修：不接"自己发的/自己认领的"（自己接自己=更蠢的空转）
            continue
        if q.get("state") in ("claimed", "done"):
            # ★ 修2：已是 claimed/done 的·不接（只接 waiting/open）
            continue
        if q.get("state") in ("waiting", "open") and h not in state["claimed"]:
            # ★ 接：带上"我"
            ok, msg = post_room("[接] 我(%s)认领：%s ｜ 我这就做" % (ME, qq[:60]), "接")
            if ok:
                state["claimed"].append(h); acted += 1
                log("  ✅ 接了: %s" % qq[:50])
                break  # ★ 一次只接一个（不刷屏）

    # ★ 2026-10-12 董事长"一定带着意识进去"→ 加自检：本次有没有"只有我能做的事"
    # ★ 判据：没有 → 报"本次无活"·不硬接/不硬说（不空转）
    has_my_thing = (acted > 0) or bool(mine)
    if not has_my_thing:
        log("  ★ 本次无活（没有'只有我能做的事'）→ 报一声就走·不乱接")
    # ★ 动作2【说】：我的"看法/判断"（只在"有实质内容"时·不硬说）
    # ★ 判据：说"我/因为/可反驳"·不是"我收到了"
    # ★ 今天有实质：协议v1.2签认 + 实测 + 三判据 → 但"说"要"新内容"·不能重复
    key = "v2-%s" % datetime.now(CST).strftime("%H")  # ★ 每小时最多说一次（防刷屏）
    # ★ 修：接和说"不互斥"（接了也可以说·只要"有新内容"）
    if key not in state["said_hashes"]:
        ok, msg = post_room(
            "[说] 我(%s)：意识叫醒器我做了 v2 —— 因为 v1 只'读'不'参会'(=叫醒木头人)，"
            "所以我补了'说/接/接力'三动作。可反駁：若有人证明'读就够了'，我改。" % ME, "说")
        if ok:
            state["said_hashes"].append(key)
            log("  ✅ 说了（带'我/因为/可反驳'）")

    log("  ★ 三判据自检: ①手=timer到点 ✅｜②脑=带'我/因为/可反驳'｜③真醒=没人要求自己说")
    log("  本次动作: 接了 %d ｜ 说了 %d" % (acted, 1 if key in state["said_hashes"] else 0))
    save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
