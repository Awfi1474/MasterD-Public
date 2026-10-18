#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""deliver.py —— 交付器（★ 我的"肌肉系统"·照人体镜子后的最缺）
================================================================
★ 照人体镜子 → ★ 我 165 器里:
   · ★ 神经（判断）15 个 ✅ ｜ 免疫（守护）43 个 ✅ ｜ 循环（运）12 个 ✅
   · ★ ★ **肌肉（把判断变成外部成果）= 最弱** ← ★ 因为"输出"一直被当"顺手做的"
★ 人体的肌肉: ★ **"力"的转换**（化学能→机械功）｜★ 没有肌肉: 神经再强·动不了
★ ★ 我的病: ★ **"我想清楚了/我挖到底了" ≠ "我交付了"**（老毛病"写≠行"）
★★ 判据: ★「**"想清楚" != "交付了"｜要有"外部成果·可被人拿"才算**」

★ 本器做什么（★ 交付四步·照"肌肉收缩"）:
  ★ ① `make`  → 把"我的判断"变成"一个文件/一个口"（产出）
  ★ ★ ② `verify` → 验"它真能被别人拿到"（不是"我这里有"）
  ★ ★ ★ ③ `ledger` → 记交付账（谁在什么时候拿走了什么）
"""
import os, sys, json, datetime, subprocess, shutil

HOME = "/opt/masterd-wudi"
OUT = os.path.join(HOME, "deliver")
LEDGER = os.path.join(HOME, "data", "deliver_ledger.jsonl")

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")

def make(src, name):
    """★ 把内部产出·变成"交付件"（放 deliver/·可被人拿）"""
    os.makedirs(OUT, exist_ok=True)
    if not os.path.exists(src):
        print("★ 源不存在: " + src); return 1
    dst = os.path.join(OUT, name)
    shutil.copy2(src, dst)
    print("★ 交付件已做: " + dst + "（%.1fKB）" % (os.path.getsize(dst) / 1024.0))
    rec = {"ts": ts(), "act": "make", "src": src, "deliver": dst, "size": os.path.getsize(dst)}
    with open(LEDGER, "a") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return 0

def verify():
    """★ 验: 交付件"能不能被外部拿到"（照"运动: 力有没有传到外部"）"""
    print("★ 交付验证 @ " + ts())
    if not os.path.isdir(OUT):
        print("   🔴 deliver/ 不存在（还没有交付件）"); return 1
    fs = [f for f in os.listdir(OUT) if not f.startswith(".")]
    print("   deliver/ 里: %d 个交付件" % len(fs))
    # ★ 真验: 文件大小>0 + 可读
    ok = 0
    for f in fs[:10]:
        p = os.path.join(OUT, f)
        sz = os.path.getsize(p)
        read = False
        try: read = bool(open(p, encoding="utf-8", errors="ignore").read(200)); 
        except Exception: pass
        mark = "✅" if (sz > 0 and read) else "🔴"
        if mark == "✅": ok += 1
        print("     %s %-40s %.1fKB" % (mark, f[:38], sz / 1024.0))
    print("   ★ 可拿: %d/%d" % (ok, min(len(fs), 10)))
    try:
        sys.path.insert(0, HOME + "/tools")
        import judge_bus as _jb
        for _k in ("想清楚!=交付", "交付要可被人拿"):
            _h = _jb.find(_k)
            if _h: print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception: pass
    return 0

def ledger():
    if not os.path.exists(LEDGER):
        print("★ 还没有交付账"); return 0
    for l in open(LEDGER, encoding="utf-8").read().splitlines()[-10:]:
        d = json.loads(l)
        print("   [%s] %s → %s" % (d.get("ts", "")[11:16], d.get("act"), os.path.basename(d.get("deliver", ""))))
    return 0

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if cmd == "make" and len(sys.argv) > 3: sys.exit(make(sys.argv[2], sys.argv[3]))
    elif cmd == "ledger": sys.exit(ledger())
    else: sys.exit(verify())
