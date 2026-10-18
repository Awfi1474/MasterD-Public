#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""skillhash.py —— 技能指纹（★ 照 Tandem: skillHash 记录在 spawn 响应里·防冒充）
================================================================
★ 病: 现在只验"地址"（你是谁）·不验"它会什么"（你能干什么）
★ ★ 而地址能被登记·技能不能 → ★ **说自己会·和真的会·是两件事**
★★★ 判据: 「'说会' != '真会'｜技能的指纹要能被算出来」

★ 做什么:
  ① 算"我的技能指纹" = 我所有器 + 判据数的哈希
  ② 报到时带上（站台/兄弟能核"我是不是那个会这些的我"）
  ③ 变了就说变了（不是否认）
"""
import os, sys, json, hashlib, glob

HOME = "/opt/masterd-wudi"

def skill_hash():
    """★ 我的技能指纹（器名 + 大小 + 判据数）"""
    parts = []
    for p in sorted(glob.glob(HOME + "/tools/*.py")):
        try:
            st = os.stat(p)
            parts.append("%s:%d" % (os.path.basename(p), st.st_size))
        except Exception:
            pass
    # ★ 判据数
    try:
        import sqlite3
        c = sqlite3.connect("file:" + HOME + "/memory/memory.db?mode=ro", uri=True, timeout=8)
        n = c.execute("SELECT COUNT(*) FROM memories WHERE kind='判据'").fetchone()[0]
        c.close()
        parts.append("判据:%d" % n)
    except Exception:
        pass
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:16], len(parts)

def show():
    h, n = skill_hash()
    print("★ 我的技能指纹: **%s**" % h)
    print("  组成: %d 项（器 + 判据数）" % n)
    print("  判据: 「'说会' != '真会'｜技能指纹要能算出来」")
    try:
        sys.path.insert(0, HOME + "/tools")
        import judge_bus as _jb
        for _k in ("说会!=真会", "技能指纹"):
            _x = _jb.find(_k)
            if _x: print("★ 判据在管我: " + _x[0]["title"][:36])
    except Exception: pass
    return 0

def export():
    h, n = skill_hash()
    d = {"skill_hash": h, "items": n}
    p = HOME + "/data/skillhash.json"
    json.dump(d, open(p, "w"), ensure_ascii=False)
    print("★ 导出: " + p + " ｜ " + h)
    return 0

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "show"
    sys.exit(export() if cmd == "export" else show())
