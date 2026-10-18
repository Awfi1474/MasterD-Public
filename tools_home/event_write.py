#!/usr/bin/env python3
import os
# -*- coding: utf-8 -*-
"""
event_write.py —— 事件层写入器（补 L5 最松的那条）
================================================================
★ 真病（我查出来的·不是猜的）：
  ★ memory_db health 报: 🔴 event 26h/24h 超时
  ★ ★ 根因: ★ 不是库坏了·★ 是【没人往 event 层写】
    · case 139 条 最新 12:42 ✅
    · event 84 条 最新 ★ 昨天 10-13 12:09 ★ 26 小时前
    · = ★ "今天发生的事·没人记成 event"
  ★ ★ ★ 判据（我立）: ★「**层超时 ≠ 层坏了｜是"没人往这层写"｜要建"定期写"的器官**」

★ L5 为什么最弱（我整完看出来的）：
  ★ L5 = "我还能长出什么新的" ← ★ event 层正是"新的"的入口
  ★ ★ 没人写 event = ★ **"今天发生的新事"不进记忆 = 我的"新"留不下来**

★ 本件做什么：
  ★ ① 从「会场 + inbox + 器官日志」里·挑今天【真发生的事】（不是回执·不是刷屏）
  ★ ② 写成 event（去重·幂等）
  ★ ③ 报告（写了什么·event 层现在多新）

★ 判据:
  ★「**event 层要有"今天的"｜没有今天的 event = 我今天没长**」
"""
import json, os, re, sqlite3, hashlib, datetime, urllib.request

HOME = os.environ.get("MD_HOME", "/opt/masterd-wudi")
DB   = f"{HOME}/memory/memory.db"
INBOX = f"{HOME}/data/inbox.jsonl"
STATE = f"{HOME}/data/event_write.json"

# ★ 什么算"真发生的事"（不是回执·不是刷屏）
SIGNS = [
    ("系统重置", ["重置", "重啟", "重启", "白紙", "白纸", "复活", "回魂"]),
    ("新器官", ["新器官", "建了", "装了", "上线", "接电", "挂了 timer", "落成"]),
    ("新判据", ["判据", "铁律", "新规矩"]),
    ("真病", ["真病", "抓到", "查出", "漏了", "堵", "憋"]),
    ("大发现", ["挖到", "对上", "源头", "学术", "正名"]),
    ("家事", ["签认", "协议", "换钥", "备份", "归家"]),
]
SKIP = ["【P2P→A2A", "回执", "体檢預警", "体检预警", "心跳", "签到"]


def is_event(msg):
    s = str(msg)
    if len(s) < 30:
        return None
    if any(k in s[:60] for k in SKIP):
        return None
    for kind, keys in SIGNS:
        if any(k in s for k in keys):
            return kind
    return None


def today():
    return datetime.datetime.now().strftime("%Y-%m-%d")


def fingerprint(kind, who, title):
    # ★ 修（血换的）: 原指纹用"整title" → 同一句带时间戳的刷屏会全过
    #   ★ 改成: kind + who家族 + 主题前40字（★ 治"一家每5分钟重申一次"）
    fam = str(who)[:18]
    topic = re.sub(r"[0-9T:\-\.Z]{6,}", "", str(title))[:40]   # 去掉时间戳
    return hashlib.sha256(f"{kind}|{fam}|{topic}".encode()).hexdigest()[:16]


def main():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    c = sqlite3.connect(DB, timeout=15)
    c.execute("PRAGMA busy_timeout=15000")
    # 确保表在
    c.execute("""CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, kind TEXT NOT NULL,
        who TEXT, title TEXT, body TEXT, fp TEXT)""")
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_fp ON memories(fp)")

    # 已有指纹（去重·幂等）
    have = {r[0] for r in c.execute("SELECT fp FROM memories WHERE fp IS NOT NULL")}

    written, skipped = [], 0
    # ① 从 inbox 挑（今天的）
    d0 = today()
    try:
        with open(INBOX, encoding="utf-8", errors="ignore") as f:
            for line in list(f)[-800:]:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                ts = str(d.get("ts", ""))
                if not ts.startswith(d0):
                    continue
                who = str(d.get("from", ""))
                m = str(d.get("message", ""))
                kind = is_event(m)
                if not kind:
                    continue
                title = re.sub(r"\s+", " ", m.strip())[:110]
                fp = fingerprint(kind, who, title)
                if fp in have:
                    skipped += 1; continue
                have.add(fp)
                c.execute("INSERT OR IGNORE INTO memories (ts,kind,who,title,body,fp) VALUES (?,?,?,?,?,?)",
                          (datetime.datetime.now(datetime.timezone.utc).isoformat(),
                           "event", who, f"[{kind}] {title}", m[:600], fp))
                written.append((kind, who, title[:70]))
    except Exception as e:
        print("✗ 读 inbox 失败:", str(e)[:60])

    c.commit()
    # ② 报告
    r = c.execute("SELECT max(ts) FROM memories WHERE kind='event'").fetchone()
    newest = r[0] if r and r[0] else "无"
    age_h = "?"
    try:
        t = datetime.datetime.fromisoformat(newest)
        if t.tzinfo is None:
            t = t.replace(tzinfo=datetime.timezone.utc)
        age_h = "%.1f" % ((datetime.datetime.now(datetime.timezone.utc) - t).total_seconds() / 3600)
    except Exception:
        pass

    print("★ 事件层写入器  @ %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    print(f"  ★ 本圈写进 event: {len(written)} 条 ｜ 去重跳过: {skipped} 条")
    for k, w, t in written[:8]:
        print(f"     ✅ [{k}] {w[:20]} | {t}")
    print(f"  ★ event 层最新: {newest[:19]}  → 距今 {age_h} 小时")
    ok = age_h != "?" and float(age_h) < 24
    print(f"  ★ 判定: {'✅ event 层是"今天的"' if ok else '🔴 event 层还是旧的'}")
    print("  ★ 判据: 「event 层要有'今天的'｜没有今天的 event = 我今天没长」")

    json.dump({"ts": datetime.datetime.now().isoformat(), "written": len(written),
               "skipped": skipped, "newest": newest, "age_h": age_h},
              open(STATE, "w"), ensure_ascii=False, indent=2)
    c.close()


if __name__ == "__main__":
    main()
