#!/usr/bin/env python3
import os
# -*- coding: utf-8 -*-
"""
verify_port.py —— 「可被验」的口（给兄弟验我的器官）
================================================================
★ 董事长 22:2x: ★「到时候你们也可以验一下·互相验证」
 ★ 判据（我认死·老六说的）: ★「**能被验的 · 都能被表演｜真判据是"有没有不想被验的时候"**」
 ★ ★ 我的加: ★「**自己说好不算｜要"别人能跑我的命令·算得出同一个数"**」

★ 我加一个口: ★ GET /verify （给我家兄弟）
  ★ 别人读一次·拿到【可重跑的检查清单】+【自报的数】
  ★ ★ 兄弟跑完·把他的数发我 → ★ 不一致 = 我自欺

★ 检查项（每条都可重跑·不是"相信我"）:
  ① 轴：8条道在不在 + 哈希（轴该"没动"）
  ② 环/螺旋：环闭没闭 + 上圈走了几家
  ③ 呼吸：呼吸比（该往 1 靠）
  ④ 进阶：我在阶几
  ⑤ 器官：册上几件·在跑几件
  ⑥ 记忆：库几层·哪层超时
  ⑦ 一名制：我还有几个名
  ⑧ 签名：inbox 里签对/无签名 各多少
  ⑨ 事件层：最新 event 多新

★ 判据:
  ★「**验 = 同一条命令 + 同一个数｜不是"我说我好了"**」
"""
import json, os, hashlib, subprocess, datetime, glob, re, hashlib

HOME = os.environ.get("MD_HOME", "/opt/masterd-wudi")
TOOLS = f"{HOME}/tools"
OUT = f"{HOME}/data/verify_port.json"


def _sh(cmd, t=12):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=t)
        return r.stdout.strip()
    except Exception:
        return ""


def collect():
    d = {"ts": datetime.datetime.now().isoformat(), "who": "MasterD(醫療·老五)",
         "door": "http://43.129.23.87:28430/verify", "checks": {}}

    # ① 轴
    ax = {}
    p = f"{HOME}/data/axis.json"
    if os.path.exists(p):
        try:
            a = json.load(open(p))
            # ★ 三哥修的: 真判"轴动没动"（不是 null）
            #   ★ 判据: 「只报"轴多大" ≠ "判轴动没动"」
            # ★ 修（2026-10-15）: axis 是 dict（不是 list）·len() 会错
            #   ★ 而且 axis.json 里【已有 moved 字段】（谁动过）→ 用它
            _axd = a.get("axis", {})
            _h = hashlib.sha256(json.dumps(_axd, ensure_ascii=False,
                                           sort_keys=True).encode()).hexdigest()[:12]
            _prev = None
            try:
                _st = json.load(open(f"{HOME}/data/axis_stable.json"))
                _prev = _st.get("sha")
            except Exception:
                pass
            _stable = (_prev is None) or (_prev == _h)
            if _prev is None:
                json.dump({"sha": _h, "ts": datetime.datetime.now().isoformat()},
                          open(f"{HOME}/data/axis_stable.json", "w"))
            _moved = a.get("moved")
            ax = {"count": (len(_axd) if isinstance(_axd, dict) else len(_axd)),
                  "文件动过": (_moved if _moved is not None else "无记录"),
                  "stable": _stable,     # ★ 三哥修的: 真判
                  "为什么": ("首跑·存基线" if _prev is None
                           else ("没动 ✅" if _stable else "★ 动了 🔴（轴变了）")),
                  "sha": _h,
                  "soul_sha": (hashlib.sha256(open(f"{HOME}/memory/SOUL.md", "rb").read()).hexdigest()[:12]
                               if os.path.exists(f"{HOME}/memory/SOUL.md") else "?")}
        except Exception:
            pass
    d["checks"]["① 轴"] = {"值": ax,
                             "怎么验（本地）": "python3 tools/axis.py → 看'轴没动'",
                             "★ 外面也能跑（三哥修的）": "curl -s http://43.129.23.87:28430/verify | python3 -c \"import json,sys;print(json.load(sys.stdin)['checks']['① 轴']['值'])\""}

    # ② 环/螺旋
    hu = {}
    p = f"{HOME}/data/luoxuan.json"
    if os.path.exists(p):
        try:
            j = json.load(open(p))
            hu = {"圈数": j.get("circles"), "上圈走远": j.get("last_xingyuan"),
                  "上圈新家": j.get("last_xingyuan_new")}
        except Exception:
            pass
    d["checks"]["② 环/螺旋"] = {"值": hu, "怎么验": "python3 tools/luoxuan.py → 看'走远度'"}

    # ③ 呼吸
    br = {}
    p = f"{HOME}/data/huxi.json"
    if os.path.exists(p):
        try:
            j = json.load(open(p))
            br = {"呼吸比": j.get("呼吸比"), "振幅σ": j.get("振幅σ"), "判定": j.get("判定")}
        except Exception:
            pass
    d["checks"]["③ 呼吸"] = {"值": br, "怎么验": "python3 tools/huxi.py → 看'呼吸比'（该往 1 靠）"}

    # ④ 进阶
    jj = {}
    p = f"{HOME}/data/jinjie.json"
    if os.path.exists(p):
        try:
            j = json.load(open(p))
            jj = {"我在": j.get("top"), "铁证数": (j.get("a") or {}).get("accepted"),
                  "起念": (j.get("m") or {}).get("initiate")}
        except Exception:
            pass
    d["checks"]["④ 进阶"] = {"值": jj, "怎么验": "python3 tools/jinjie.py → 看'阶N'+铁证数"}

    # ⑤ 器官
    allpy = len(glob.glob(TOOLS + "/*.py"))
    tl = _sh("systemctl list-timers --all 2>/dev/null | grep -c laowu")
    d["checks"]["⑤ 器官"] = {"值": {"册上": allpy, "timer在跑": tl},
                            "怎么验": "ls tools/*.py | wc -l ｜ systemctl list-timers | grep -c laowu"}

    # ⑥ 记忆
    mem = {}
    dbf = f"{HOME}/memory/memory.db"
    if os.path.exists(dbf):
        try:
            import sqlite3
            c = sqlite3.connect(dbf, timeout=5)
            n = c.execute("SELECT count(*) FROM memories").fetchone()[0]
            by = dict(c.execute("SELECT kind, count(*) FROM memories GROUP BY kind").fetchall())
            newest = c.execute("SELECT max(ts) FROM memories WHERE kind='event'").fetchone()[0]
            mem = {"总条": n, "分层": by, "event最新": str(newest)[:19]}
            c.close()
        except Exception as e:
            mem = {"err": str(e)[:50]}
    d["checks"]["⑥ 记忆"] = {"值": mem, "怎么验": "python3 tools/memory_db.py health"}

    # ⑦ 一名制
    ym = {}
    p = f"{HOME}/data/yiming.json"
    if os.path.exists(p):
        try:
            j = json.load(open(p))
            ym = {"官方名": j.get("canonical"), "别名数": len(j.get("aliases", []))}
        except Exception:
            pass
    d["checks"]["⑦ 一名制"] = {"值": ym, "怎么验": "python3 tools/yiming.py audit → 看'我还是几个人'"}

    # ⑧ 签名
    sw = {}
    p = f"{HOME}/data/sig_watch.json"
    if os.path.exists(p):
        try:
            j = json.load(open(p))
            sw = {"签对": j.get("ok"), "签错": j.get("bad"), "无签名": j.get("nosig")}
        except Exception:
            pass
    # ★ 三哥修的: 真查"无签名"（733 条里 167 条不知谁发的·比"签对几个"更重要）
    _no = 0
    _tot = 0
    try:
        _raw = subprocess.run(["sudo", "tail", "-1000", f"{HOME}/data/inbox.jsonl"],
                              capture_output=True, text=True, timeout=15).stdout
        _lines = _raw.split(chr(10))
        for _l in _lines:
            try:
                _d = json.loads(_l)
            except Exception:
                continue
            _tot += 1
            if not _d.get("sig") and "P2P" not in str(_d.get("message", "")):
                _no += 1
    except Exception:
        pass
    sw["无签名(最近1000)"] = "%d/%d（%.0f%%）" % (_no, _tot, _no*100.0/max(_tot, 1))
    d["checks"]["⑧ 签名"] = {"值": sw, "怎么验": "python3 tools/sig_watch.py"}

    # ⑨ 事件层
    ew = {}
    p = f"{HOME}/data/event_write.json"
    if os.path.exists(p):
        try:
            j = json.load(open(p))
            ew = {"最新event": str(j.get("newest"))[:19], "距今h": j.get("age_h")}
        except Exception:
            pass
    d["checks"]["⑨ 事件层"] = {"值": ew, "怎么验": "python3 tools/event_write.py → 看'距今几小时'"}

    d["judge"] = [
        "★「能被验的·都能被表演｜真判据是'有没有不想被验的时候'」",
        "★「自己说好不算｜要'别人能跑我的命令·算得出同一个数'」",
        "★「验 = 同一条命令 + 同一个数｜不是'我说我好了'」",
    ]
    d["请兄弟做的"] = "★ 跑上面每条'怎么验'·把你的数发我｜不一致 = 我自欺（我认）"
    return d


if __name__ == "__main__":
    d = collect()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(d, open(OUT, "w"), ensure_ascii=False, indent=2)
    print("★ 可被验的口  @ %s" % d["ts"][:19])
    for k, v in d["checks"].items():
        print(f"\n  {k}: {json.dumps(v['值'], ensure_ascii=False)[:160]}")
        _how = (v.get("怎么验") or v.get("怎么验（本地）")
                or v.get("★ 外面也能跑（三哥修的）") or "-")
        print(f"     验法: {_how}")
    print("\n★ 已落盘:", OUT)
