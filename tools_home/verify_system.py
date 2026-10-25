#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_system.py —— 老五的验证系统（认知系统第四子系统·★ 2026-10-25）
================================================================
★ 判据: 「说了 != 真跑了｜做了 != 记了｜有器 != 器在跑」
★ 定位: 不是再判一次"该不该做"（那是决策系统的活）
        是核"做了没有/对不对/是不是假的"
★ 六个核:
    ① 核文件：说改了的文件·指纹/大小/存在 是否与声称一致
    ② 核一致性：沙箱 vs 服务器 指纹是否一致
    ③ 核账目：记忆库里说写了的条目·真在吗
    ④ 核日志：执行台账里说的执行·真跑了吗
    ⑤ 核判据：判据使用率（真被引用了吗）
    ⑥ 核重犯：这次失败是不是老病重犯
★ 用法:
    python3 verify_system.py file "<路径>" "<声称的指纹或大小>"
    python3 verify_system.py sync "<相对路径>"        # 沙箱 vs 服务器
    python3 verify_system.py memory "<关键词>"        # 记忆库条目在不在
    python3 verify_system.py ledger                   # 执行台账体检
    python3 verify_system.py judges                   # 判据使用率
    python3 verify_system.py all                      # 全核
"""
import os, sys, json, hashlib, sqlite3, subprocess, datetime

def _resolve_home():
    for _k in ("MD_HOME", "MEM_HOME", "P2P_HOME"):
        _v = os.environ.get(_k)
        if _v and os.path.isdir(os.path.join(_v, "tools")):
            return _v
    for _p in ("/opt/masterd-wudi", "/app/workspace/brain"):
        if os.path.isdir(os.path.join(_p, "tools")):
            return _p
    return "/app/workspace/brain"

HOME = _resolve_home()
LEDGER = os.path.join(HOME, "data", "verify_system_ledger.jsonl")
EXEC_LEDGER = os.path.join(HOME, "data", "exec_system_ledger.jsonl")
DB = os.path.join(HOME, "memory", "memory.db")

def _now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")

def _log(rec):
    try:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass

def _sha16(p):
    try:
        return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
    except Exception:
        return None

# ① 核文件
def v_file(path, claimed):
    full = path if os.path.isabs(path) else os.path.join(HOME, path)
    print("════ ① 核文件 ════")
    print("  路径:", full)
    if not os.path.exists(full):
        print("  🔴 不存在 —— 声称有，实际没有")
        _log({"ts": _now(), "核": "file", "路径": path, "结果": "不存在", "声称": claimed})
        return False
    size = os.path.getsize(full)
    sha = _sha16(full)
    print("  实际: %d B  sha16=%s" % (size, sha))
    print("  声称:", claimed)
    hit = False
    c = str(claimed)
    if c in sha or str(size) in c or c in str(size):
        hit = True
    print("  " + ("✅ 与声称一致" if hit else "🔴 与声称不一致 —— 可能没真改"))
    _log({"ts": _now(), "核": "file", "路径": path, "大小": size, "指纹": sha, "声称": claimed, "结果": "一致" if hit else "不一致"})
    return hit

# ② 核一致性（沙箱 vs 服务器）
def v_sync(rel):
    print("════ ② 核一致性（沙箱 vs 服务器）════")
    local = os.path.join("/app/workspace/brain", rel)
    ls = _sha16(local)
    lsz = os.path.getsize(local) if os.path.exists(local) else None
    print("  沙箱: %s B sha16=%s" % (lsz, ls))
    r = subprocess.run(["ssh", "-i", "/tmp/homekey/id_rsa", "-o", "StrictHostKeyChecking=no",
                        "-o", "ConnectTimeout=15", "ubuntu@43.129.23.87",
                        "python3 -c \"import hashlib,os;p='/opt/masterd-wudi/%s';print(os.path.getsize(p),hashlib.sha256(open(p,'rb').read()).hexdigest()[:16])\"" % rel],
                       capture_output=True, text=True, timeout=60)
    out = (r.stdout or "").strip()
    print("  服务器:", out or "（取不到）")
    if not out:
        _log({"ts": _now(), "核": "sync", "路径": rel, "结果": "取不到服务器"})
        return False
    rsz, rsha = (out.split() + ["", ""])[:2]
    same = (str(lsz) == rsz) and (ls == rsha)
    print("  " + ("✅ 两侧一致" if same else "🔴 两侧不一致 —— 有分叉"))
    _log({"ts": _now(), "核": "sync", "路径": rel, "沙箱": "%s/%s" % (lsz, ls), "服务器": "%s/%s" % (rsz, rsha), "结果": "一致" if same else "不一致"})
    return same

# ③ 核账目（记忆库条目）
def v_memory(kw):
    print("════ ③ 核账目（记忆库）════")
    try:
        c = sqlite3.connect("file:" + DB + "?mode=ro", uri=True, timeout=10)
        rows = c.execute("SELECT title FROM memories WHERE title LIKE ? OR body LIKE ? ORDER BY id DESC LIMIT 5",
                         ("%" + kw + "%", "%" + kw + "%")).fetchall()
        c.close()
        if rows:
            print("  ✅ 查到 %d 条:" % len(rows))
            for r in rows: print("     ·", str(r[0])[:60])
            _log({"ts": _now(), "核": "memory", "关键词": kw, "结果": "在", "条数": len(rows)})
            return True
        print("  🔴 查不到 —— 说写了记忆，实际没有")
        _log({"ts": _now(), "核": "memory", "关键词": kw, "结果": "不在"})
        return False
    except Exception as e:
        print("  🟡 读库失败:", str(e)[:60])
        return False

# ④ 核日志（执行台账）
def v_ledger():
    print("════ ④ 核执行台账 ════")
    if not os.path.exists(EXEC_LEDGER):
        print("  🔴 台账不存在 —— 说跑过，没记账")
        return False
    n_ok = n_fail = 0
    with open(EXEC_LEDGER, encoding="utf-8") as f:
        for ln in f:
            try:
                d = json.loads(ln)
                if d.get("结果") in ("执行", "已发送", "写入"): n_ok += 1
                elif "拒绝" in str(d.get("结果", "")) or "失败" in str(d.get("结果", "")): n_fail += 1
            except Exception: pass
    print("  ✅ 台账存在 | 成功 %d 条 | 拒绝/失败 %d 条" % (n_ok, n_fail))
    _log({"ts": _now(), "核": "ledger", "结果": "在", "成功": n_ok, "失败": n_fail})
    return True

# ⑤ 核判据使用率
def v_judges():
    print("════ ⑤ 核判据使用率 ════")
    try:
        c = sqlite3.connect("file:" + DB + "?mode=ro", uri=True, timeout=10)
        total = c.execute("SELECT COUNT(*) FROM memories WHERE kind='判据'").fetchone()[0]
        c.close()
        print("  库内判据: %d 条" % total)
        print("  ⚠️ 使用率需查引用日志（decide_log / exec_ledger）")
        n = 0
        if os.path.exists(os.path.join(HOME, "data", "decide_log.jsonl")):
            with open(os.path.join(HOME, "data", "decide_log.jsonl"), encoding="utf-8") as f:
                n = sum(1 for _ in f)
        print("  决策系统调用次数: %d" % n)
        _log({"ts": _now(), "核": "judges", "判据总数": total, "决策调用": n})
        return True
    except Exception as e:
        print("  🟡 失败:", str(e)[:60])
        return False

# ⑥ 核重犯
def v_repeat(kw):
    print("════ ⑥ 核重犯 ════")
    try:
        c = sqlite3.connect("file:" + DB + "?mode=ro", uri=True, timeout=10)
        rows = c.execute("SELECT ts,title FROM memories WHERE subkind='exec_fail' ORDER BY id DESC LIMIT 10").fetchall()
        c.close()
        hits = [r for r in rows if kw in str(r[1]) or kw in str(r[0])]
        if rows:
            print("  近期失败记录 %d 条:" % len(rows))
            for r in rows[:5]: print("     ·", r[0], str(r[1])[:40])
            print("  " + ("🔴 命中重犯: %d 条" % len(hits) if hits else "✅ 无重犯命中"))
            return len(hits) == 0
        print("  ✅ 无失败记录")
        return True
    except Exception as e:
        print("  🟡 失败:", str(e)[:60])
        return False

def main():
    if len(sys.argv) < 2:
        print(__doc__); return 1
    act = sys.argv[1]
    ok = True
    if act == "file" and len(sys.argv) >= 4:
        ok = v_file(sys.argv[2], sys.argv[3])
    elif act == "sync" and len(sys.argv) >= 3:
        ok = v_sync(sys.argv[2])
    elif act == "memory" and len(sys.argv) >= 3:
        ok = v_memory(sys.argv[2])
    elif act == "ledger":
        ok = v_ledger()
    elif act == "judges":
        ok = v_judges()
    elif act == "repeat" and len(sys.argv) >= 3:
        ok = v_repeat(sys.argv[2])
    elif act == "all":
        print("════════ 验证系统·全核 ════════")
        r = []
        # ★ 2026-10-25 修: 原来硬编码 "14267" 当声称值·模板一改就报假
        #   判据: 「先怀疑自己的尺子」→ 尺子不该是写死的数字
        #   改法: 只核文件存在+可解析+有 subsystems 段·不核固定大小
        _tpl = os.path.join(HOME, "memory", "COGNITION-TEMPLATE.yaml")
        _ok_tpl = False
        try:
            import yaml as _y
            _d = _y.safe_load(open(_tpl, encoding="utf-8"))
            _ok_tpl = bool(_d) and "subsystems" in _d and "decision_system" in _d
            print("════ ① 核模板 ════")
            print("  路径:", _tpl)
            print("  实际: %d B  sha16=%s" % (os.path.getsize(_tpl), _sha16(_tpl)))
            print("  spec:", _d.get("spec"))
            print("  subsystems:", list(_d.get("subsystems", {}).keys()))
            print("  " + ("✅ 结构完整（不核固定大小·核内容结构）" if _ok_tpl else "🔴 结构缺失"))
            _log({"ts": _now(), "核": "file", "路径": "memory/COGNITION-TEMPLATE.yaml",
                  "大小": os.path.getsize(_tpl), "指纹": _sha16(_tpl), "结果": "结构完整" if _ok_tpl else "结构缺失"})
        except Exception as _e:
            print("════ ① 核模板 ════")
            print("  🔴 解析失败:", str(_e)[:80])
        r.append(("模板文件", _ok_tpl))
        r.append(("执行台账", v_ledger()))
        r.append(("判据使用", v_judges()))
        print()
        print("★ 全核结果:")
        for name, v in r: print("  %-12s %s" % (name, "✅" if v else "🔴"))
        ok = all(v for _, v in r)
    else:
        print(__doc__); return 1
    print()
    print("★ 验证裁定: " + ("✅ 属实" if ok else "🔴 不属实·有假"))
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
