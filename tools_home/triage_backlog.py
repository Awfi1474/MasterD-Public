#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·积压分类止血（防本体烧钱回测试垃圾）

病情（照实）:
  本体复活后 未读 38255 条 → 无差别回复
  里面 56173 真消息 + 12030 验证 + 3797 探针 + 1897 ACTS + 1764 回执 + 237 通道测试
  ★ 判据(老大): «测试不是做事|发1000条测试 != 做1件真活»
  ★ 判据(老三): «自检自己造的垃圾要自己清|不自清=自己把自己堵死»

做法:
  ① 分类（测试/探针/回执/验证 → 标 read=true + tag=non_business）
  ② 真消息保留未读（让本体回）
  ③ 报表：清了什么、留了什么
用法: python3 tools/triage_backlog.py [--apply]
"""
import json, io, os, re, sys, time, shutil

HOME = "/opt/masterd-wudi"
SRC = HOME + "/data/inbox.jsonl"
KEEP_DAYS = 1          # 只让本体碰最近 1 天的真信

RE_TEST = re.compile(
    r"^(?:tck-|done$|ctest|G30-|SCHK-|SIXDIM-|lw-|bd-|RECTEST|E2E-|local-|ackver-|"
    r"std①|通道实测|双向验证|链路看守|探活|测试[abc]?|probe)", re.IGNORECASE)
RE_ACK = re.compile(r"(?:LINK-ACK|到级回执|门收到|ack_by|received_only)", re.IGNORECASE)

def classify(msg):
    if isinstance(msg, dict):
        msg = str(msg.get("text") or msg.get("message") or "")
    m = str(msg or "").strip()
    if RE_ACK.search(m):
        return "ack"
    if RE_TEST.search(m):
        return "test"
    if len(m) <= 12 and ("收到" in m or "ok" in m.lower() or m in ("x", "1")):
        return "ack"
    return "real"

def main():
    apply = "--apply" in sys.argv
    if not os.path.exists(SRC):
        print("no src"); return 1
    stat = {"ack": 0, "test": 0, "real": 0, "old_real": 0}
    out = []
    n = 0
    for ln in io.open(SRC, "r", encoding="utf-8", errors="ignore"):
        n += 1
        try:
            d = json.loads(ln)
        except Exception:
            out.append(ln); continue
        if not isinstance(d, dict):
            out.append(ln); continue
        if d.get("read") is True:
            out.append(ln); continue
        cls = classify(d.get("message"))
        if cls == "real":
            ts = str(d.get("ts") or "")[:10]
            today = time.strftime("%Y-%m-%d")
            if ts and ts < today and KEEP_DAYS <= 1:
                # 旧的真信也先归档（不删·标 stale）
                d["read"] = True
                d["triage"] = "stale_real"
                stat["old_real"] += 1
                out.append(json.dumps(d, ensure_ascii=False) + "\n")
                continue
            stat["real"] += 1
            out.append(ln)
        else:
            d["read"] = True
            d["triage"] = cls
            stat[cls] += 1
            out.append(json.dumps(d, ensure_ascii=False) + "\n")
    print(f"总行 {n} | 真信留未读 {stat['real']} | 旧真信归档 {stat['old_real']} | "
          f"测试标读 {stat['test']} | 回执标读 {stat['ack']}")
    if not apply:
        print("★ dry-run（--apply 才改）")
        return 0
    shutil.copy2(SRC, SRC + ".bak-triage-" + time.strftime("%Y%m%d_%H%M%S"))
    tmp = SRC + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as f:
        f.writelines(out)
    os.replace(tmp, SRC)
    print("已写入", SRC, f"{os.path.getsize(SRC)/1e6:.1f}MB")
    return 0

if __name__ == "__main__":
    sys.exit(main())
