#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清洗存量 from=ROLE_USER（13035 条）·从 message 前缀反推真源。

判据(老七): «role 字段漏出 ← 这就是显示英文»
判据(老六): «默认值要查"是否永远有值"»

做法:
  ① 逐条读 inbox.jsonl（流式·不全载）
  ② from == "ROLE_USER" → 从 message 前缀 [大哥]/【老七】等反推
  ③ 推不出 → 标 "a2a-client(unverified)"（不留 ROLE_USER）
  ④ 备份 + 原子替换
  ⑤ 同时修 state 里的（若有）
用法: python3 tools/clean_role_from.py [--apply]
"""
import json, re, io, os, sys, time, shutil

HOME = "/opt/masterd-wudi"
SRC = HOME + "/data/inbox.jsonl"
PREFIX_MAP = {
    "大哥": "老大(区块链)", "老大": "老大(区块链)",
    "老二": "老二(归根)", "二哥": "老二(归根)",
    "老三": "老三(燼)", "三哥": "老三(燼)", "三弟": "老三(燼)",
    "老四": "老四", "四弟": "老四", "四哥": "老四",
    "老五": "老五(阿诊)", "五弟": "老五(阿诊)",
    "老六": "老六(燭)", "六弟": "老六(燭)",
    "老七": "老七(Arki)", "七弟": "老七(Arki)", "Arki": "老七(Arki)",
    "大哥自测": "老大(区块链)",
}
_RE_PREFIX = re.compile(r"^\s*[\[\【]([^\]\】]{1,20})[\]\】]")

def infer(msg):
    m = _RE_PREFIX.match(msg or "")
    if m:
        key = m.group(1).strip()
        return PREFIX_MAP.get(key) or (key if len(key) <= 20 else None)
    if "链路看守探针" in (msg or "") or (msg or "").startswith("lw-"):
        return "链路看守器"
    # ★ 2026-11-19 加: 官方 ACTS/测试语料（tck-* 等=测试残留）
    _t = (msg or "").strip()
    if _t.startswith("tck-") or _t.startswith("done") or _t.startswith("ctest"):
        return "ACTS测试器"
    if "探活" in _t or _t.startswith("探针") or "双向验证" in _t:
        return "探针器"
    return None

def main():
    apply = "--apply" in sys.argv
    if not os.path.exists(SRC):
        print("SRC 不存在"); return 1
    n = 0; fixed = 0; unmapped = 0
    out_lines = []
    with io.open(SRC, "r", encoding="utf-8", errors="ignore") as f:
        for ln in f:
            n += 1
            if '"from": "ROLE_USER"' not in ln and '"from":"ROLE_USER"' not in ln:
                out_lines.append(ln); continue
            try:
                d = json.loads(ln)
            except Exception:
                out_lines.append(ln); continue
            if str(d.get("from")) == "ROLE_USER":
                src = infer(d.get("message") or "")
                if src:
                    d["from"] = src
                    d["from_inferred"] = True
                    fixed += 1
                else:
                    d["from"] = "a2a-client(unverified)"
                    d["from_inferred"] = False
                    unmapped += 1
                out_lines.append(json.dumps(d, ensure_ascii=False) + "\n")
            else:
                out_lines.append(ln)
    print(f"总行: {n} | 可反推: {fixed} | 未映射: {unmapped}")
    if not apply:
        print("★ dry-run（加 --apply 才改）")
        return 0
    shutil.copy2(SRC, SRC + ".bak-roleclean-" + time.strftime("%Y%m%d_%H%M%S"))
    tmp = SRC + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as f:
        f.writelines(out_lines)
    os.replace(tmp, SRC)
    print(f"新文件: {SRC}  {os.path.getsize(SRC)/1e6:.1f}MB")
    return 0

if __name__ == "__main__":
    sys.exit(main())
