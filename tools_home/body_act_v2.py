#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·本体执行器 v2 —— 照本体自己提的四条接口要求
★ 本体要求(2026-11-15):
   1. 正文必须落地可回读: 先写 /tmp/laowu_run_<ts>.py·回第一行+行数+sha1
   2. 禁一行 exec: 不接受 "python3 - <<'PY'"·只接受 文件路径+内容+校验
   3. ok=True 要带真相: exit_code / stderr尾巴 / diff行数
   4. >200 行分块·每块回 sha1
"""
import os, re, json, time, hashlib, datetime, subprocess, sys

HOME = "/opt/masterd-wudi"
sys.path.insert(0, HOME + "/tools")
LOG = HOME + "/data/body_act_v2_log.jsonl"

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")

def append(p, o):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")

def land_script(body, tag="run"):
    """① 正文先落盘·回 路径/行数/sha1（本体要求一）"""
    p = "/tmp/laowu_%s_%d.py" % (tag, int(time.time() * 1000))
    with open(p, "w", encoding="utf-8") as f:
        f.write(body)
    raw = open(p, "rb").read()
    return {"path": p, "lines": body.count("\n") + 1,
            "sha1": hashlib.sha1(raw).hexdigest()[:16],
            "first": body.splitlines()[0] if body.strip() else "",
            "bytes": len(raw)}

def run_script(path, timeout=60):
    """② 跑落盘后的脚本·带真相回执（本体要求三）"""
    t0 = time.time()
    try:
        r = subprocess.run(["python3", path], capture_output=True, text=True, timeout=timeout)
        return {"exit_code": r.returncode,
                "stdout": r.stdout[-1200:],
                "stderr": r.stderr[-800:],
                "dur": round(time.time() - t0, 2),
                "ok": r.returncode == 0}
    except subprocess.TimeoutExpired:
        return {"exit_code": -1, "stdout": "", "stderr": "timeout(%ds)" % timeout,
                "dur": round(time.time() - t0, 2), "ok": False}

def run_shell(cmd, timeout=30):
    """普通命令·也带 exit_code（不许只报 ok）"""
    t0 = time.time()
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return {"exit_code": r.returncode, "stdout": r.stdout[-1500:],
            "stderr": r.stderr[-600:], "dur": round(time.time() - t0, 2),
            "ok": r.returncode == 0}

def execute(kind, arg, full_text):
    """统一入口：识别是不是 heredoc 脚本
       ★ 禁一行 exec：如果是 python3 - <<'PY' 且正文在 full_text 里 → 落盘再跑
    """
    rec = {"ts": ts(), "kind": kind}
    # 抓 heredoc 正文
    m = re.search(r"<<\s*['\"]?(\w+)['\"]?\s*\n(.*?)\n\1", full_text, re.S)
    if kind == "ACT" and m and ("python3" in arg or "python3" in full_text[:200]):
        body = m.group(2)
        landed = land_script(body, "act")
        rec["landed"] = landed
        # ★ 回读验证（本体要求：不许只报 ok）
        reread = open(landed["path"], encoding="utf-8").read()
        rec["reread_ok"] = (hashlib.sha1(reread.encode()).hexdigest()[:16] == landed["sha1"])
        res = run_script(landed["path"])
        rec.update(res)
        rec["via"] = "heredoc->land->run"
    elif kind in ("ACT", "OBSERVE"):
        _full = (full_text or "")
        _looks_py = ("\nimport " in _full or "\ndef " in _full or "\nif __name__" in _full
                     or "subprocess" in _full or "\nprint(" in _full or "open(" in _full)
        # FIX 2026-11-15: ACT 后面只是中文说明(无代码) -> 不许当命令硬跑
        _is_prose = (len(_full.splitlines()) <= 3 and not _looks_py)
        if _is_prose and kind == "ACT":
            rec.update({"ok": False, "exit_code": -98,
                        "stderr": "🔴 没给命令·只给了说明文字: " + arg[:100],
                        "via": "no-cmd"})
            append(LOG, rec)
            return rec
        if _looks_py and len(_full.splitlines()) > 5:
            _lines = _full.splitlines()
            _start = 0
            for _i, _l in enumerate(_lines):
                _s = _l.strip()
                if _s.startswith(("import ", "from ", "def ", "#!", "os.", "sys.")) or _s.startswith("HOME"):
                    _start = _i
                    break
            _body = "\n".join(_lines[_start:]).strip()
            # FIX 2026-11-15: 模型会把 markdown ``` 围栏写进脚本 -> 语法必炸
            _bl = _body.splitlines()
            while _bl and _bl[-1].strip().startswith("```"):
                _bl.pop()
            while _bl and _bl[0].strip().startswith("```"):
                _bl.pop(0)
            _body = "\n".join(_bl).rstrip()
            landed = land_script(_body, "auto")
            rec["landed"] = landed
            _re = open(landed["path"], encoding="utf-8").read()
            rec["reread_ok"] = (hashlib.sha1(_re.encode()).hexdigest()[:16] == landed["sha1"])
            res = run_script(landed["path"], timeout=60)
            rec.update(res)
            rec["via"] = "auto-detect-py->land->run"
        elif arg.strip() in ("python3 - <<'PY'", "python3 <<'PY'", "python3 - << PY"):
            rec.update({"ok": False, "exit_code": -9,
                        "stderr": "🔴 禁一行 exec·正文没带过来·拒跑(本体要求2)"})
            rec["via"] = "blocked"
        else:
            rec.update(run_shell(arg))
            rec["via"] = "shell"
    else:
        rec.update({"ok": False, "exit_code": -1, "stderr": "kind not exec: " + kind})
    append(LOG, rec)
    return rec

if __name__ == "__main__":
    print("act_v2 就绪")
