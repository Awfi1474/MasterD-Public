#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·队列消化器 queue_digest.py —— 处理 21 万条积压
★ 照实: body-queue.jsonl 210,883 条全 queued·没消费
★ 判据: 「队列积压 = 有入口没出口｜先分真假·再归档」
★ 做法(零模型):
   ① 分类: 测试/噪音/重复 → archived
   ② 真内容 → 保留(等本体处理)
   ③ 落账: 三样齐(输入/算子/重跑)
"""
import os, json, re, hashlib, datetime

HOME = "/opt/masterd-wudi"
QUEUE = HOME + "/state/body-queue.jsonl"
ARCHIVE = HOME + "/data/body_queue_archived.jsonl"
LOG = HOME + "/data/queue_digest.jsonl"

NOISE_PAT = [
    r"^RECTEST-\d+",
    r"^MD-SEND-TEST",
    r"^\[SELFCOPY",
    r"^探活",
    r"^probe$", r"^ping$", r"^test$",
    r"^TEST-NOISE",
    r"tck-long-running",
    r"^链路看守探针",
    r"双向验证",
]


def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")


def is_noise(t):
    t = (t or "").strip()
    if not t:
        return True, "empty", "len==0"
    for p in NOISE_PAT:
        if re.search(p, t, re.I):
            return True, "pattern", p
    if len(t) < 30 and not any(c in t for c in "?？"):
        return True, "too_short", "len<30 无问号"
    if "自動回執" in t or "自动回执" in t:
        return True, "auto_receipt", "含自动回执"
    return False, "", ""


def digest(dry=True):
    if not os.path.exists(QUEUE):
        return {"err": "no queue"}
    keep = []
    arch = []
    seen = set()
    dup = 0
    noise = 0
    for l in open(QUEUE, encoding="utf-8", errors="ignore"):
        if not l.strip():
            continue
        try:
            d = json.loads(l)
        except Exception:
            continue
        msg = str(d.get("msg") or "")
        n, kind, why = is_noise(msg)
        h = hashlib.md5(msg[:120].encode()).hexdigest()
        if h in seen:
            dup += 1
            d["archived_reason"] = "dup"
            arch.append(d)
            continue
        seen.add(h)
        if n:
            d["archived_reason"] = kind + ":" + why[:40]
            arch.append(d)
            noise += 1
        else:
            keep.append(d)

    proof = {
        "ts": ts(), "dry": dry,
        "输入": {"队列行": len(keep) + len(arch)},
        "算子": "噪音/重复 -> archived；真内容保留",
        "结果": {"保留": len(keep), "归档噪音": noise, "归档重复": dup,
                 "归档合计": len(arch)},
        "复跑": "python3 tools/queue_digest.py --apply",
    }
    if not dry and arch:
        with open(ARCHIVE, "a", encoding="utf-8") as f:
            for d in arch:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")
        with open(QUEUE, "w", encoding="utf-8") as f:
            for d in keep:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")
        # ★ 重跑验证
        left = sum(1 for _ in open(QUEUE, encoding="utf-8", errors="ignore"))
        proof["重跑"] = {"队列剩余行": left, "归档文件行": sum(1 for _ in open(ARCHIVE, encoding="utf-8", errors="ignore"))}
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(proof, ensure_ascii=False) + "\n")
    return proof


if __name__ == "__main__":
    import sys
    r = digest(dry="--apply" not in sys.argv)
    print(json.dumps(r, ensure_ascii=False, indent=1))