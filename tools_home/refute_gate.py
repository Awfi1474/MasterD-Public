#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""refute_gate.py —— 老五·外部否证闸(认知体系第⑤关·2026-11-08)
================================================================
判据(本体裁·照董事长令"补外部世界/反方"):
  「没被反方攻过 = 没立住」
  「攻过且活下来 = 才算立住；攻过没写 = 等于没攻」
  「未过 refute_gate 的结论 = 假结论」

三层反方(缺一不可):
  1 自己演反方: 判断落账前·强制写「这判断怎么被推翻」
  2 请老七攻我: 发一条"攻我"·回执入账
  3 外部世界否证: falsified_ledger 有日期

用法:
  refute_gate.py check <结论id>          -> 查该结论过闸没(三件)
  refute_gate.py claim <id> <结论> <怎么被推翻> -> 落一条(带反方字段)
  refute_gate.py audit                   -> 全台账审计(未攻的列出来)
================================================================
"""
import sqlite3, json, sys, os, datetime
HOME = "/opt/masterd-wudi"
DB = HOME + "/memory/memory.db"
LEDGER = HOME + "/data/falsified_ledger.json"

def now():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")

def ensure(con):
    con.execute("""CREATE TABLE IF NOT EXISTS refute (
      id TEXT PRIMARY KEY, claim TEXT, refuted_by TEXT, refuted_at TEXT,
      result TEXT, attacker TEXT, created_at TEXT)""")
    con.commit()


def is_real_proof(proof):
    """本体:格式闸+证据闸。真proof=path可stat可复算·不是{note,src}填充值"""
    import json as _j, os as _o
    try:
        d = _j.loads(proof) if isinstance(proof,str) else proof
    except Exception:
        return False, "非json"
    if not isinstance(d, dict):
        return False, "非dict"
    path = d.get("path") or d.get("file") or ""
    if not path:
        return False, "无path(填充值·如note/src)"
    if not _o.path.exists(str(path)):
        return False, "path不存在(不可复算)"
    return True, "ok(可stat:%s)" % str(path)[:60]

def check(cid):
    """查三件:①怎么写被推翻 ②老七回执 ③台账日期"""
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    try:
        r = con.execute("select id,claim,refuted_by,attacker,result from refute where id=?", (cid,)).fetchone()
    except Exception:
        r = None
    con.close()
    if not r:
        print("❌ %s 未过闸(无记录·=假结论)" % cid); return False
    ok1 = bool(r[2])          # 怎么写被推翻
    ok2 = bool(r[3])          # 谁攻的(老七)
    ok3 = bool(r[4])          # 结果(活下来没)
    # ★ 本体加:第④件 proof真核(可stat)
    _pf = r[6] if len(r)>6 else ""
    ok4, _why4 = is_real_proof(_pf) if _pf else (False, "无proof")
    print("%s: ①怎么写被推翻=%s ②谁攻=%s ③结果=%s ④proof可复算=%s(%s)" % (cid, ok1, r[3] or "未攻", r[4] or "无", ok4, _why4))
    passed = ok1 and ok2 and ok3 and ok4
    print("→ %s" % ("✅过闸(=立住)" if passed else "❌未过(未攻=没立住)"))
    return passed

def claim(cid, claim_txt, refute_txt, attacker="self"):
    con = sqlite3.connect(DB, timeout=10); ensure(con)
    con.execute("INSERT OR REPLACE INTO refute (id,claim,refuted_by,refuted_at,result,attacker,created_at) VALUES (?,?,?,?,?,?,?)",
                (cid, claim_txt[:200], refute_txt[:300], now(), "", attacker, now()))
    con.commit(); con.close()
    print("落账 %s | 反方(怎么被推翻): %s" % (cid, refute_txt[:50]))

def audit():
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    try:
        rows = con.execute("select id,claim,refuted_by,attacker,result from refute").fetchall()
    except Exception:
        rows = []
    con.close()
    n_pass = n_fail = 0
    print("=== refute 台账审计 ===")
    for r in rows:
        ok = bool(r[2]) and bool(r[3]) and bool(r[4])
        n_pass += ok; n_fail += (not ok)
        print(" [%s] %s | 攻=%s 结果=%s" % ("✅" if ok else "❌", r[0][:26], r[3] or "未攻", r[4] or "无"))
    print("--- 过闸=%d 未过=%d (未过=假结论·没被推翻的确信=装) ---" % (n_pass, n_fail))



def external_view(rec):
    """照大哥G6七问·跟external_view.py对齐:缺哪条报哪条"""
    q = {
      "①第三方探过": bool(rec.get("attacker") and rec.get("attacker") not in ("self","",None)),
      "②外部源":     bool(rec.get("ext_source") or rec.get("src")),
      "③原件":       bool(rec.get("is_original") is True or rec.get("origin")=="原件"),
      "④谁探的":     bool(rec.get("who") or rec.get("attacker")),
      "⑤从哪探的":   bool(rec.get("from_where") or rec.get("endpoint")),
      "⑥探到什么":   bool(rec.get("what") or rec.get("value")),
      "⑦原件or转述": bool(rec.get("is_original") is not None or rec.get("origin")),
    }
    miss = [k for k,v in q.items() if not v]
    print("  G6七问:%d/7 | 缺:%s" % (7-len(miss), miss or "无"))
    return len(miss)==0, miss

def selftest():
    """本体撞出来的三样本·固化(闸认可复算·不认嘴)"""
    import json as _j
    cases = [
      ('A_fake',     '{"note":"test","src":"manual"}',           False, '无path'),
      ('B_nopath',   '{"path":"/no/such/file_xyz"}',             False, 'path不存在'),
      ('C_realpath', '{"path":"/opt/masterd-wudi/tools/refute_gate.py"}', True, '可stat'),
    ]
    ok = 0
    for name, proof, expect, why in cases:
        r, e = is_real_proof(proof)
        good = (r == expect)
        ok += good
        print(" [%s] %-11s 期=%s 实=%s %s" % ("OK" if good else "XX", name, expect, r, e))
    print("=== selftest %d/%d ===" % (ok, len(cases)))

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__)
    elif a[0] == "check": check(a[1])
    elif a[0] == "claim": claim(a[1], a[2] if len(a)>2 else "", a[3] if len(a)>3 else "", a[4] if len(a)>4 else "self")
    elif a[0] == "audit": audit()
    elif a[0] == "selftest": selftest()
    else: print("unknown:", a[0])
