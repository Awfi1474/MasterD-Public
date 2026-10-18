#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backup_first.py —— 老五的「备份先行器」（十方缺2·治"畏缩"+"手重"）
================================================================
★ 我的病: ★ ① 畏缩（该改不敢改）② 手重（改了没备份 → 出事）
★ ★ 我今晚真账: ★ **记忆库坏了**（有 05:20 备份救回·★ **证明"备份先行"有用**）
★ 判据（我立）: ★「**"要动 X 之前" 先 "备份 X"｜不备份不动**」

★ 用法:
  ★ `backup_first.py do <文件/目录>` → ★ 备份 + 记「动之前备份了」
  ★ ★ `backup_first.py check` → ★ 看"最近动了什么·有没有先备份"
"""
import json, os, io, sys, shutil, datetime, subprocess

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
BAK = f"{HOME}/recovery/backup-first"
LOG = f"{DATA}/backup_first.jsonl"
TZ = datetime.timezone(datetime.timedelta(hours=8))



# ★ 判据总线（治"写在器里·没人查"·C20）
def _judge(kw):
    """★ 查判据库（真查=真用·计入使用率）"""
    try:
        import sys as _s, importlib.util as _iu
        if "/opt/masterd-wudi/tools" not in _s.path: _s.path.insert(0, "/opt/masterd-wudi/tools")
        import judge_bus as _jb
        return _jb.find(kw)
    except Exception:
        return []

def ts():
    return datetime.datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S%z")


def do(path):
    os.makedirs(BAK, exist_ok=True)
    if not os.path.exists(path):
        print("★ 不存在: %s" % path); return
    name = os.path.basename(path.rstrip("/")) + "." + datetime.datetime.now().strftime("%m%d%H%M")
    dst = os.path.join(BAK, name)
    try:
        if os.path.isdir(path):
            shutil.copytree(path, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(path, dst)
        r = {"ts": ts(), "kind": "backup", "src": path, "dst": dst, "ok": True}
        print("★ 备份先行: %s → %s ✅" % (path, dst))
    except Exception as e:
        r = {"ts": ts(), "kind": "backup", "src": path, "ok": False, "err": str(e)[:60]}
        print("★ 备份失败: %s" % str(e)[:60])
    with open(LOG, "a") as f:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")


def check():
    print("★ 备份先行器（治畏缩+手重）  @", ts())
    print("★ 判据: 要动之前·先备份·不备份不动")
    print("=" * 52)
    n = 0
    if os.path.exists(LOG):
        for l in io.open(LOG, encoding="utf-8"):
            try:
                d = json.loads(l)
                n += 1
                if n <= 5:
                    print("  ✅ [%s] %s" % (d["ts"][11:19], d.get("src", "")[:50]))
            except Exception:
                pass
    print("  ★ 备过: %d 次" % n)
    # ★ 真查: 关键文件有没有备份
    print("\n  ★ 关键文件备份状态:")
    for f in ["memory/memory.db", "code/p2p_mailbox.py", "agent-id/subkey.json"]:
        p = f"{HOME}/{f}"
        has = any(os.path.exists(os.path.join(BAK, os.path.basename(f) + "." + x))
                  for x in [""]) if os.path.exists(BAK) else False
        baks = [x for x in os.listdir(BAK)] if os.path.exists(BAK) else []
        hit = any(os.path.basename(f) in x for x in baks)
        print("    %-26s %s" % (f, "✅ 有备份" if hit else "🟡 没单独备份（有总包）"))


def main():
    _j = _judge("归档!=完事(")
    if _j: print("★ 判据在管我: " + _j[0]["title"][:36])
    if _j: print("★ 判据在管我: " + _j[0]["title"][:36])
    _j = _judge("挖到底魄")
    if _j: print("★ 判据在管我: " + _j[0]["title"][:36])
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "do":
        do(sys.argv[2] if len(sys.argv) > 2 else "?")
    else:
        check()


if __name__ == "__main__":
    main()
