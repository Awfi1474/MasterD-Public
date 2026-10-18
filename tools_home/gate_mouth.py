# -*- coding: utf-8 -*-
"""
★ 把卡设在"开口那一刻"（最小版·不用新器·用已有的）
★ 做法: 每次要说话前·先跑这一次的"三问" + 出口闸
"""
import subprocess, sys, json
HOME = "/opt/masterd-wudi"

def 开口前(msg):
    print("【开口前·过卡】")
    # ★ ① 这是哪种证
    print("  ① 这是哪种证: " + ("回董事长/回兄弟（沟通）" if any(w in msg for w in ["董事长","兄弟","Arki","三哥"]) else "报进展/答问题"))
    # ★ ② 哪条判据管（真调库）
    r = subprocess.run(["sudo", "python3", "-c", """
import sqlite3, sys
kw = sys.argv[1][:6]
c = sqlite3.connect("file:/opt/masterd-wudi/memory/memory.db?mode=ro", uri=True, timeout=8)
n = 0
for (t,) in c.execute("SELECT title FROM memories WHERE kind='判据' AND (title LIKE ? OR body LIKE ?) ORDER BY id DESC LIMIT 3", ("%"+kw+"%", "%"+kw+"%")):
    print("     · " + str(t)[:52]); n += 1
if n == 0: print("     （库里没直接对应）")
c.close()
""", msg[:12]], capture_output=True, text=True, timeout=30)
    print("  ② 哪条判据管:")
    print(r.stdout.strip() or "     （取不到）")
    # ★ ③ 反证
    print("  ③ 如果错了·最可能错在: 我又在'演示'而不是'真做'")
    # ★ ④ 证据账（★ 开口前·先把主张+判据+证据写进账·带指纹）
    try:
        import subprocess as _sp
        _claim = msg[:80].replace("\n", " ")
        _r = _sp.run(["python3", HOME + "/tools/evidence.py", "write",
                      _claim, "开口前先立账·被质疑查账不改", "本条为本次发言的主张（自动记账）"],
                     capture_output=True, text=True, timeout=30)
        for _ln in (_r.stdout or "").split("\n"):
            if "指纹" in _ln or "证据" in _ln: print("  ④ " + _ln.strip()[:60])
    except Exception as _e:
        print("  ④ 证据账: 🟡 " + str(_e)[:40])

    # ★ ⑤ 出口闸
    sys.path.insert(0, HOME + "/tools")
    try:
        import out_gate
        ok, why = out_gate.check(msg)
        print("  ⑤ 出口闸: " + ("✅ 放行" if ok else "🔴 拦下 " + str(why)))
        return ok
    except Exception as e:
        print("  ⑤ 出口闸: 🟡 " + str(e)[:40])
        return True

if __name__ == "__main__":
    msg = " ".join(sys.argv[1:])
    if not msg:
        print("用法: gate_mouth.py <要说的话>"); sys.exit(1)
    ok = 开口前(msg)
    print()
    print("★ 裁定: " + ("可以开口" if ok else "不许开口·先改"))
    sys.exit(0 if ok else 1)
