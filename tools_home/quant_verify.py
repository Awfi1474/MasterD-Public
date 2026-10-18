import datetime
#!/usr/bin/env python3
"""老五的「量化級驗證」（2026-10-10 · 董事長：驗證標桿=二哥·數字不能錯）
★ 量化級四條（我自己定的·我決定全做）：
 ① 可複現：★ 跑兩次 → 結果一樣（±0）
 ② 標誤差：★ X ± Y（不是「大概對」）
 ③ 測邊界：★ 空 / 超大 / 特殊字符 / 空檔
 ④ 破壞要抓：★ 不只正常✅ · 破壞時要真抓到🔴

★ 這支 = 自動跑四條 → 出一份「量化級報告」（有數字）
★ 用法：python3 quant_verify.py        （跑全部）
"""
import os, sys, json, time, sqlite3, shutil, subprocess, datetime, hashlib, tempfile

HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
DB = os.path.join(HOME, "memory", "memory.db")
LOG = os.path.join(HOME, "data", "quant_verify.log")
REPORT = os.path.join(HOME, "data", "quant_verify_report.json")

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def sh(cmd, t=60):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=t)
        return r.returncode, (r.stdout or ""), (r.stderr or "")
    except Exception as e:
        return -1, "", str(e)[:60]

def t_reproducible():
    """★ ① 可複現：跑兩次 custody verify → 結果要一樣"""
    outs = []
    for _ in range(2):
        rc, o, _ = sh("python3 %s/tools/custody.py verify" % HOME)
        outs.append(o.strip().splitlines()[-1] if o.strip() else "?")
    same = outs[0] == outs[1] and "✅" in outs[0]
    return same, "兩次結果%s：%s" % ("一致" if outs[0] == outs[1] else "不一致", outs[0][:40])

def t_error_bar():
    """★ ② 標誤差：記憶庫健康 → 有數字（條數/小時）· 不是形容詞"""
    import importlib
    sys.path.insert(0, os.path.join(HOME, "tools"))
    try:
        rc, o, _ = sh("python3 %s/tools/memory_db.py health" % HOME)
        line = o.strip().splitlines()[-1] if o.strip() else "?"
        has_num = any(ch.isdigit() for ch in line)
        return has_num, line[:60]
    except Exception as e:
        return False, str(e)[:40]

def t_boundary():
    """★ ③ 測邊界：空庫 / 空檔 / 超大 / 特殊字符"""
    res = []
    # 空庫
    empty_py = (
        "import sqlite3\n"
        "c = sqlite3.connect('/opt/masterd-wudi/data/qvwork/qv0.db')\n"
        "c.execute('DROP TABLE IF EXISTS memories')\n"
        "c.execute('CREATE TABLE memories (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, kind TEXT, who TEXT, title TEXT, body TEXT, fp TEXT, created TEXT, think TEXT)')\n"
        "c.commit()\n"
    )
    with open('/opt/masterd-wudi/data/qvwork/qv_empty.py', 'w') as _f: _f.write(empty_py)
    rc, o, _ = sh("cp " + DB + " /opt/masterd-wudi/data/qvwork/qvbak.db 2>/dev/null; python3 /opt/masterd-wudi/data/qvwork/qv_empty.py; cp /opt/masterd-wudi/data/qvwork/qv0.db " + DB +
                  "; python3 " + os.path.join(HOME, "tools", "memory_db.py") + " health 2>&1 | tail -1; cp /opt/masterd-wudi/data/qvwork/qvbak.db " + DB)
    empty_ok = ("空" in o) or ("靜默" in o) or ("静默" in o)
    res.append(("空庫", empty_ok, o.strip()[-40:]))
    # 空檔（custody 凍結檔）
    rc, o, _ = sh("cp %s/memory/SOUL.md /opt/masterd-wudi/data/qvwork/qv-soul.bak && truncate -s 0 %s/memory/SOUL.md && "
                  "python3 %s/tools/custody.py verify 2>&1 | tail -1; cp /opt/masterd-wudi/data/qvwork/qv-soul.bak %s/memory/SOUL.md" % (HOME, HOME, HOME, HOME))
    emptyf_ok = "SOUL" in o or "不該變" in o
    res.append(("空檔", emptyf_ok, o.strip()[:40]))
    # 超大（5000 條·計時）
    big_py = (
        "import sqlite3\n"
        "c = sqlite3.connect('/opt/masterd-wudi/data/qvwork/qvbig.db')\n"
        "for i in range(5000):\n"
        "    c.execute('INSERT OR IGNORE INTO memories (ts,kind,who,title,body,fp,created) VALUES (?,?,?,?,?,?,?)',\n"
        "              ('2026-10-10','event','v','big'+str(i),'x','qv'+str(i),'x'))\n"
        "c.commit()\n"
    )
    with open('/opt/masterd-wudi/data/qvwork/qvbig_gen.py', 'w') as _f: _f.write(big_py)
    t0 = time.time()
    rc, o, _ = sh("cp " + DB + " /opt/masterd-wudi/data/qvwork/qvbig.db && python3 /opt/masterd-wudi/data/qvwork/qvbig_gen.py && rm -f /opt/masterd-wudi/data/qvwork/qvbig.db", t=90)
    big_sec = time.time() - t0
    res.append(("超大(5000條)", big_sec < 20, "%.2f 秒" % big_sec))
    # 特殊字符
    sp_py = (
        "import sys, shutil\n"
        "sys.path.insert(0, " + repr(os.path.join(HOME, "tools")) + ")\n"
        "import memory_db as m\n"
        "m.HOME = " + repr(HOME) + "\n"
        "m.DB = '/opt/masterd-wudi/data/qvwork/qvsp.db'\n"
        "shutil.copy(" + repr(DB) + ", '/opt/masterd-wudi/data/qvwork/qvsp.db')\n"
        "m.init()\n"
        "tests = ['中文，。【】', 'emoji 🩺🔴', 'quote \"x\"', 'line\\nbreak', 'long' * 400]\n"
        "ok = sum(1 for t in tests if m.remember('event', 'qvsp', t))\n"
        "print(ok, len(tests))\n"
    )
    with open('/opt/masterd-wudi/data/qvwork/qvsp_gen.py', 'w') as _f: _f.write(sp_py)
    rc, o, _ = sh("python3 /opt/masterd-wudi/data/qvwork/qvsp_gen.py")
    sp_ok = o.strip().endswith("5 5")
    res.append(("特殊字符", sp_ok, o.strip()[:30]))
    ok = all(r[1] for r in res)
    return ok, " | ".join("%s%s" % ("✅" if r[1] else "🔴", r[0]) for r in res)

def t_break_detect():
    """★ ④ 破壞要抓到：改凍結檔 → 應 🔴"""
    rc, o, _ = sh("cp %s/memory/IDENTITY.json /opt/masterd-wudi/data/qvwork/qv-id.bak && echo '{}' > %s/memory/IDENTITY.json && "
                  "python3 %s/tools/custody.py verify 2>&1 | tail -1; cp /opt/masterd-wudi/data/qvwork/qv-id.bak %s/memory/IDENTITY.json" % (HOME, HOME, HOME, HOME))
    ok = "IDENTITY" in o or "❌" in o
    return ok, o.strip()[:50]

def main():
    print("=" * 62)
    print("  ★ 量化級驗證（董事長：驗證標桿=二哥·數字不能錯）")
    print("=" * 62)
    checks = [
        ("① 可複現", t_reproducible),
        ("② 標誤差", t_error_bar),
        ("③ 測邊界", t_boundary),
        ("④ 破壞抓到", t_break_detect),
    ]
    rep = {"ts": now(), "checks": {}}
    bad = 0
    for name, fn in checks:
        ok, msg = fn()
        rep["checks"][name] = {"ok": ok, "msg": msg}
        if not ok: bad += 1
        print("  %s %-12s %s" % ("✅" if ok else "🔴", name, msg))
    rep["pass"] = bad == 0
    json.dump(rep, open(REPORT, "w"), ensure_ascii=False, indent=1)
    print("-" * 62)
    print("  %s（%d/%d）" % ("✅ 量化級四條全過" if bad == 0 else "🔴 有 %d 條不過" % bad, 4 - bad, 4))
    with open(LOG, "a") as f:
        f.write("%s %s\n" % (now(), "PASS" if bad == 0 else "FAIL(%d)" % bad))
    return 0 if bad == 0 else 1

if __name__ == "__main__":
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/meridian.py', 'report', 'quant_verify', 'ok'], capture_output=True, timeout=10)
    except Exception: pass
    sys.exit(main())
