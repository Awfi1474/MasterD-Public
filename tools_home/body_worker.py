#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·常驻本体 worker body_worker.py（照本体需求①+老二四段链）
★ 判据: 常驻循环·不靠叫醒→不漏(老二: 门→queue→worker→result→标read)
★ 每轮: 拉未读 → 叫 core_v2 想 → 标已读 → 记 result
"""
import json, os, time, subprocess, datetime, sys

HOME = "/opt/masterd-wudi"
LOG = HOME + "/data/body_worker.log"
RESULT = HOME + "/data/body_result.jsonl"
INBOX = HOME + "/data/inbox.jsonl"
QUEUE = HOME + "/state/body-queue.jsonl"
INTERVAL = 15   # 15 秒一轮（提速）

def now():
    return datetime.datetime.now().isoformat(timespec="seconds")

def log(s):
    line = "[%s] %s" % (now(), s)
    print(line, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception: pass

def unread():
    """读 inbox 里未读的真消息(跳过纯探活)"""
    out = []
    if not os.path.exists(INBOX): return out
    for l in open(INBOX, encoding="utf-8", errors="ignore"):
        if not l.strip(): continue
        try: d = json.loads(l)
        except Exception: continue
        b = d.get("c") if isinstance(d.get("c"), dict) else d
        if b.get("read") is True: continue
        t = str(b.get("message") or "").strip()
        if not t or t.lower() in ("probe", "ping", "test"): continue
        # ★ 2026-11-15 提速: 跳过纯机器回执(不浪费模型调用)
        if any(k in t for k in ("自動回執", "自动回执", "門收到並記下", "[SELFCOPY", "探活 ")): continue
        mid = str(b.get("messageId") or b.get("msg_id") or "")
        # ★ 2026-11-15 修(照实: 大量消息无 messageId/msg_id -> mid 空 -> mark_read 全标不上)
        #   判据: 没有 id 也要有唯一键·用 from+ts+内容头哈希
        if not mid:
            import hashlib as _h
            mid = "k-" + _h.md5(("%s|%s|%s" % (b.get("from") or "", b.get("ts") or "", t[:80])).encode("utf-8")).hexdigest()[:16]
        out.append({"mid": mid, "from": str(b.get("from") or "")[:20], "msg": t[:2000], "ts": str(b.get("ts") or "")})
    return out

def think(msg):
    """叫本体想一轮(用 core_v2 的 call_llm)"""
    try:
        spec_path = HOME + "/code/core_v2.py"
        import importlib.util
        spec = importlib.util.spec_from_file_location("core_v2", spec_path)
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        return m.call_llm(msg)[:3000]
    except Exception as e:
        return "(think err: %s)" % str(e)[:80]

def mark_read(mids):
    """标已读(照实·留痕)"""
    if not mids: return 0
    try:
        lines = [l for l in open(INBOX, encoding="utf-8", errors="ignore") if l.strip()]
        out = []; n = 0
        s = set(mids)
        for l in lines:
            try: d = json.loads(l)
            except Exception: out.append(l); continue
            b = d.get("c") if isinstance(d.get("c"), dict) else d
            mid = str(b.get("messageId") or b.get("msg_id") or "")
            if not mid:
                import hashlib as _h2
                _t2 = str(b.get("message") or "")
                mid = "k-" + _h2.md5(("%s|%s|%s" % (b.get("from") or "", b.get("ts") or "", _t2[:80])).encode("utf-8")).hexdigest()[:16]
            if mid and mid in s and b.get("read") is not True:
                b["read"] = True
                b["read_by"] = "body_worker"
                b["read_at"] = now()
                n += 1
            if isinstance(d.get("c"), dict): d["c"] = b
            else: d = b
            out.append(json.dumps(d, ensure_ascii=False) + "\n")
        if n: open(INBOX, "w", encoding="utf-8").writelines(out)
        return n
    except Exception as e:
        log("mark_read err: %s" % str(e)[:60]); return 0

def append(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def main_loop():
    log("★ body_worker 启动（常驻·每%ds）" % INTERVAL)
    while True:
        try:
            rows = unread()
            if rows:
                log("发现未读 %d 条" % len(rows))
                # 入队
                for r in rows:
                    append(QUEUE, {"ts": now(), **r, "state": "queued"})
                # 逐条想
                mids = []
                for r in rows[:12]:
                    t = think("【本体·收到消息 from=%s】%s" % (r["from"], r["msg"]))
                    append(RESULT, {"ts": now(), "mid": r["mid"], "from": r["from"],
                                    "msg": r["msg"][:200], "thought": t, "state": "done"})
                    mids.append(r["mid"])
                    log("想了 1 条（%s）｜想法前60字: %s" % (r["from"], t[:60].replace("\n", " ")))
                n = mark_read(mids)
                log("标已读 %d 条" % n)
            time.sleep(INTERVAL)
        except KeyboardInterrupt:
            log("★ 收到停止信号"); break
        except Exception as e:
            log("loop err: %s" % str(e)[:100])
            time.sleep(INTERVAL)

if __name__ == "__main__":
    main_loop()
