#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hall_cache.py —— 会场缓存（治"算一个数拉全库"）
================================================================
★ 董事长 01:3x: ★「你这边真正的跑一遍」→ ★ 我跑了·★ **全身 17 步通了**·
★★ 但★ **最慢两步: 呼吸 17.6s ｜ 意识 9.1s** ← ★ **都是"拉整个会场"（5118 条）**
 ★ ★ ★ 我今晚报过的判据: ★「**算一个数·别拉全库**」← ★ 现在真修

★ 治法（三层·不重复拉）:
  ★ ① 缓存: ★ 会场全量每 5 分钟拉一次（缓存文件）·谁要谁读缓存
  ★ ★ ② 增量: ★ 若缓存 < 5 分钟 → 直接用（不拉）
  ★ ★ ★ ③ 兜底: ★ 拉不到 → 用旧缓存（不阻塞）

★ 判据:
  ★「**算一个数·别拉全库｜要'只取算这个数需要的'**」
  ★「**同一个会场·不该每个器各拉一次｜要共享缓存**」
"""
import os, json, time, urllib.request

HOME = "/opt/masterd-wudi"
CACHE = f"{HOME}/data/hall_cache.json"
HALL = "http://134.175.45.16:28100/questions"
TTL = 300       # ★ 缓存有效期（5 分钟）


def get_hall(force=False, timeout=8):
    """★ 拿会场（缓存优先·5 分钟内不重拉）"""
    now = time.time()
    # ★ ① 缓存新鲜 → 直接用
    if not force and os.path.exists(CACHE):
        try:
            d = json.load(open(CACHE))
            if now - d.get("_cached_at", 0) < TTL:
                return d.get("questions", []), {"from": "cache", "age": round(now - d["_cached_at"], 1)}
        except Exception:
            pass
    # ★ ② 拉（★ 短 timeout·别拖）
    try:
        r = urllib.request.urlopen(HALL, timeout=timeout)
        raw = r.read().decode()
        d = json.loads(raw)
        items = d.get("questions", []) if isinstance(d, dict) else d
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        json.dump({"_cached_at": now, "questions": items}, open(CACHE, "w"), ensure_ascii=False)
        return items, {"from": "net", "n": len(items)}
    except Exception as e:
        # ★ ③ 兜底: 用旧缓存（不阻塞）
        if os.path.exists(CACHE):
            try:
                d = json.load(open(CACHE))
                return d.get("questions", []), {"from": "stale", "err": str(e)[:40]}
            except Exception:
                pass
        return [], {"from": "fail", "err": str(e)[:50]}


if __name__ == "__main__":
    t0 = time.time()
    items, how = get_hall()
    print("★ 会场缓存  %s ｜ %d 条 ｜ %.2fs" % (how, len(items), time.time()-t0))
    t0 = time.time()
    items2, how2 = get_hall()
    print("★ 第二次（该走缓存）  %s ｜ %d 条 ｜ %.2fs" % (how2, len(items2), time.time()-t0))
