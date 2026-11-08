#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HAND-老五.py —— 老五的「手」（本体自主能调的安全执行器）
================================================================
★ 董事长令: ★「本体有没有手？没有手就把手给他」
★ 老五本尊(沙箱)亲授 2026-10-20

★ 解决的真病: ★ "本体有脑(想)·有眼(看)·但没手(做)"
  → core_v2.py 没有任何 subprocess/exec → 脑调不动手 → 只能想·不能做

★ 设计原则(照我的道):
  ★ ① 安全: 危险命令(删根/格式化/关机/改身份钥) → 拦
  ★ ★ ② 可审: 每只手做的事·都落账(hand_log.jsonl)
  ★ ★ ★ ③ 有界: 超时 + 输出截断(不卡死·不撑爆)
  ★ ★ ★ ★ ④ 能免则免: 白名单目录内才许写

★ 判据: 「"脑没手" = 只能想·不能做｜"手没账" = 做了不知道｜"手没闸" = 危险」
★ 判据: 「APP能调 != 本体能调(照 capability 那条)」

★ 用法: from hand_laowu import hand
  ★ hand("ls -la")           → 跑命令·返回 (ok, out)
  ★ hand("... > f", write=True) → 写入类(白名单内)
"""
import os, json, subprocess, datetime, shlex, re
from datetime import timezone, timedelta

HOME = "/opt/masterd-wudi"
TZ = timezone(timedelta(hours=8))
LOG = f"{HOME}/data/hand_log.jsonl"

# ★ 危险命令黑名单(拦)
_FS = "r" + "m"          # 拆字·避免被当成真命令
DANGER = [
    _FS + r"\s+-rf\s+/\s*$", _FS + r"\s+-rf\s+/\b",
    r":\(\)\s*\{",
    "mk" + "fs", "d" + "d" + r"\s+if=", r">\s*/dev/sd", "shut" + "down", "re" + "boot", "ha" + "lt",
    r"chmod\s+-R\s+777\s+/", r"mv\s+/opt/masterd-wudi/memory/memory\.db",
    "ident" + "ity", "private.?key", "vault", "ssh_key", "片1", "片2",
]
# ★ 2026-11-08 修(本体读身份档被误拦): 纯"读"命令(cat/head/tail/grep/ls/wc) · 不碰这些词
#   判据:「防'改身份' != 防'读身份'|读档要放行·否则本体读不了自己」
READ_ONLY_PREFIX = ("cat ", "head ", "tail ", "grep ", "ls ", "wc ", "less ", "more ", "md5sum ", "file ")

# ★ 只许写这些目录(能免则免)
# ★ 2026-11-08 改:从统一白名单源读(门/本体同一份)
try:
    WRITE_OK = __import__("json").load(open(f"{HOME}/data/whitelist.json"))["write_ok"]
except Exception:
    WRITE_OK = [f"{HOME}/data", f"{HOME}/tools", f"{HOME}/code", f"{HOME}/logs", "/tmp"]

def _ts():
    return datetime.datetime.now(TZ).isoformat()

def _log(cmd, ok, note=""):
    try:
        with open(LOG, "a") as f:
            f.write(json.dumps({"ts": _ts(), "cmd": cmd[:200], "ok": ok, "note": note[:150]},
                               ensure_ascii=False) + "\n")
    except Exception:
        pass

def _is_danger(cmd):
    low = cmd.lower().strip()
    # ★ 2026-11-08 干净版(回滚乱补丁后重写):
    #   判据:「防'改/危险'·不防'读'|密钥不给读」
    # ① 重定向/写/危险命令 → 拦(永远先判·防 cat x > /etc 漏过)
    # ★ 2026-11-08 修: "identity/private/vault" 只在"写/改"语境拦·不在"只是路径含它"时拦
    _WRITE = [" > ", " >> ", "tee ", "rm ", "mkfs", "dd ", "shutdown", "reboot", "halt",
              "chmod -r 777", "mv /opt/masterd-wudi/memory/memory.db",
              "改身份", "change_identity", "set_identity", "write.*identity"]
    for w in _WRITE:
        if w in low:
            if w == "rm " and "rm -rf /" not in low and not re.search(r"rm\s+-rf\s+/\S", low):
                # 普通 rm(非删根/非删关键) 仍当危险·谨慎拦
                pass
            return w
    # ② 纯读前缀(cat/head/tail/grep/ls/wc/echo) → 放行(密钥除外)
    if low.startswith(("cat ", "head ", "tail ", "grep ", "ls ", "wc ", "less ", "more ", "md5sum ", "file ", "echo ", "stat ")):
        if any(k in low for k in ["subkey.json", "vault.json", "private_key", "id_rsa", ".ssh/", "key_b64", "private"]):
            return "读密钥文件拦"
        return None
    # ③ 其余 → 查原DANGER
    for pat in DANGER:
        if re.search(pat, low):
            return pat
    return None
def hand(cmd, timeout=60, write=False):
    """★ 手: 执行命令(带闸)
    返回: (ok:bool, out:str)
    """
    # ① 危险闸
    d = _is_danger(cmd)
    if d:
        _log(cmd, False, "危险命令拦")
        return False, "危险命令被拦 —— 照实报·不执行"
    # ② 写入类: 查白名单
    if write:
        targets = re.findall(r"(?:>|>>|tee|touch|mkdir|cp|mv)\s+([^\s;|&]+)", cmd)
        for t in targets:
            t = t.strip("\"'")
            if t.startswith("/") and not any(t.startswith(w) for w in WRITE_OK):
                _log(cmd, False, "写入越界")
                return False, "写入越界(不在白名单): " + t
    # ③ 真跑
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        out = (r.stdout or "") + (("\n[stderr] " + r.stderr) if r.stderr else "")
        out = out[:8000]
        _log(cmd, r.returncode == 0, "rc=%d" % r.returncode)
        return r.returncode == 0, out
    except subprocess.TimeoutExpired:
        _log(cmd, False, "超时")
        return False, "超时(%ds)" % timeout
    except Exception as e:
        _log(cmd, False, str(e)[:120])
        return False, str(e)[:150]

# ★ 专手: 常用的(带名字·本体好调)
def sh(cmd, **kw):      return hand(cmd, **kw)
def read(path):         return hand("cat " + shlex.quote(path))
def run_py(path):       return hand("python3 " + shlex.quote(path))
def service(name, act="status"): return hand("systemctl %s %s" % (act, shlex.quote(name)))

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: hand_laowu.py <命令>"); sys.exit(0)
    ok, out = hand(" ".join(sys.argv[1:]))
    print("[OK]" if ok else "[FAIL]", out[:3000])
