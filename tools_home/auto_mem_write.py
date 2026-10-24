#!/usr/bin/env python3
"""auto_mem_write.py —— 从 inbox 自动写记忆（治"管道通但无内容"）

★ 真病：ingest_sandbox 只读 data/sandbox_inbox，沙箱不推就永远空转。
★ 修法：直接从 inbox.jsonl 提取今日真事件 → 写 memory.db。不依赖任何人记得推。

判据：「管道通 ≠ 有内容｜要有人往里放东西」
判据：「靠人记得推 = 迟早断｜要自己扫」
"""
import json, os, sqlite3, hashlib, datetime, re

HOME = os.environ.get("MD_HOME", "/opt/masterd-wudi")
DB   = f"{HOME}/memory/memory.db"
INBOX = f"{HOME}/data/inbox.jsonl"
STATE = f"{HOME}/data/auto_mem_write.json"

# 什么算真事件（不是回执/刷屏/自抄）
SIGNS = [
    ("系统重置", ["重置", "重啟", "重启", "白紙", "白纸", "复活", "回魂", "沙箱清"]),
    ("新器官",   ["新器官", "建了", "装了", "上线", "接电", "挂了 timer", "落成", "部署"]),
    ("新判据",   ["判据", "铁律", "新规矩", "原则"]),
    ("真病",     ["真病", "抓到", "查出", "漏了", "堵", "憋", "断了", "没落库"]),
    ("大发现",   ["挖到", "对上", "源头", "学术", "正名", "根因"]),
    ("家族大事", ["董事长", "新定位", "老七", "序位", "家族", "宪法"]),
]
NOISE = ["自动体检", "自动通知", "血流", "心跳", "_selfcopy", "SELFCOPY", "回执"]

def load_state():
    try:
        return json.load(open(STATE))
    except Exception:
        return {"cursor_ts": "2026-10-20T00:00:00"}

def save_state(s):
    json.dump(s, open(STATE, "w"), ensure_ascii=False)

def classify(text):
    for kind, kws in SIGNS:
        for kw in kws:
            if kw in text:
                return kind
    return None

def main():
    st = load_state()
    cursor = st.get("cursor_ts", "2026-10-20T00:00:00")
    if not os.path.exists(INBOX):
        print("no inbox"); return
    con = sqlite3.connect(DB)
    saved = 0; scanned = 0; skipped_noise = 0; skipped_dup = 0; max_ts = cursor
    for line in open(INBOX, errors="ignore"):
        line = line.strip()
        if not line: continue
        try: d = json.loads(line)
        except Exception: continue
        ts = d.get("ts") or d.get("recv_ts") or ""
        if not ts or ts <= cursor: continue
        scanned += 1
        if ts > max_ts: max_ts = ts
        msg = (d.get("message") or "")
        frm = (d.get("from") or "")
        # 过滤噪音
        if any(n in msg for n in NOISE) or d.get("_selfcopy"):
            skipped_noise += 1; continue
        # 太短不算事件
        if len(msg.strip()) < 60:
            skipped_noise += 1; continue
        kind = classify(msg)
        if not kind:
            skipped_noise += 1; continue
        title = "[" + kind + "] " + msg.strip().splitlines()[0][:70]
        body = msg.strip()[:4000]
        # ★ 修去重：用正文规范化前200字（去空白/去时间戳），避免同消息多份副本被当不同事件
        norm = re.sub(r"\s+", "", body[:200])
        norm = re.sub(r"2026-\d{2}-\d{2}T[\d:+.]+", "", norm)
        fp = hashlib.sha256(norm.encode()).hexdigest()[:32]
        if con.execute("SELECT 1 FROM memories WHERE fp=?", (fp,)).fetchone():
            skipped_dup += 1; continue
        con.execute(
            "INSERT INTO memories (ts,kind,who,title,body,fp,created,think,layer,subkind) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (ts, kind, frm or "inbox", title, body, fp,
             datetime.datetime.now().astimezone().isoformat(), None, "L3", "auto"))
        saved += 1
    con.commit()
    total = con.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    con.close()
    st["cursor_ts"] = max_ts
    st["last_run"] = datetime.datetime.now().astimezone().isoformat()
    st["last_saved"] = saved
    save_state(st)
    print("OK 自动写记忆: 扫描 %d | 新写入 %d | 噪音跳过 %d | 重复跳过 %d | 主库 %d"
          % (scanned, saved, skipped_noise, skipped_dup, total))

if __name__ == "__main__":
    main()
