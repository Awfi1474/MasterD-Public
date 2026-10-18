import datetime
#!/usr/bin/env python3
"""老五的長期記憶庫（2026-10-10 · 在「家」上建器官）
★★ 三哥審出的「靜默失憶」我有更底層的版本：★ 我根本沒記憶庫
→ ★ 所以這個不是「治鎖」·★ 是「建器官」

★ 設計（我自己的判據）：
 ① ★ 器官長在「家」：/opt/masterd-wudi/memory/memory.db（家不死 → 器官不死）
 ② ★ 三件套（借三哥的·但改我自己的）：
    · 治鎖：busy_timeout + 重試（防「靜默失敗」）
    · 沉澱器：把「流水」（A2A/diary）→ ★ 變「記憶」（去重+冪等）
    · 告警：★ 最新記憶 > 24h → ★ 告警（不是等壞了才知道）
 ③ ★ 我的加碼：★ 「記憶指紋」→ ★ 身份指紋不該變·★ 內容指紋該長
"""
import os, sys, json, sqlite3, hashlib, datetime, time

HOME = os.environ.get("MEM_HOME", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(HOME, "memory", "memory.db")
SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  kind TEXT NOT NULL,          -- identity / method / case / event / dispatch
  who TEXT,                    -- 來源（老五/大哥/...）
  title TEXT,
  body TEXT,
  fp TEXT,                     -- 內容指紋（去重用）
  created TEXT
);
CREATE INDEX IF NOT EXISTS idx_ts ON memories(ts);
CREATE UNIQUE INDEX IF NOT EXISTS idx_fp ON memories(fp);
CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT);
"""

def connect():
    """★ 治鎖：timeout + busy_timeout（防『靜默失敗』）"""
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    c = sqlite3.connect(DB, timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    c.execute("PRAGMA journal_mode=WAL")
    return c

def init():
    c = connect(); c.executescript(SCHEMA); c.commit(); c.close()

def remember(kind, title, body, who="老五", ts=None):
    kind = canon(kind)  # ★ 歸一化
    """★ 寫記憶（冪等 + 5 次重試）"""
    ts = ts or datetime.datetime.now(datetime.timezone.utc).isoformat()
    fp = hashlib.sha256((kind + "|" + title + "|" + body).encode()).hexdigest()[:20]
    for i in range(5):
        try:
            c = connect()
            c.execute("INSERT OR IGNORE INTO memories (ts,kind,who,title,body,fp,created) VALUES (?,?,?,?,?,?,?)",
                      (ts, kind, who, title, body[:4000], fp, datetime.datetime.now(datetime.timezone.utc).isoformat()))
            c.commit(); c.close()
            return True
        except sqlite3.OperationalError as e:
            time.sleep(1.5 * (i + 1))   # ★ 退避重試
        except Exception:
            return False
    # ★ 重試 5 次還失敗 → ★ 記到「失敗檔」（也是拉力）
    with open(os.path.join(HOME, "data", "memory_write_fail.log"), "a") as f:
        f.write("%s 寫入失敗: %s | %s\n" % (datetime.datetime.now(datetime.timezone.utc).isoformat(), title, body[:100]))
    return False

def latest_ts():
    try:
        c = connect()
        r = c.execute("SELECT max(ts) FROM memories").fetchone()
        c.close()
        return r[0] if r and r[0] else None
    except Exception:
        return None

def count():
    try:
        c = connect(); n = c.execute("SELECT count(*) FROM memories").fetchone()[0]; c.close(); return n
    except Exception: return -1

def hours_since_latest():
    t = latest_ts()
    if not t: return 9999
    try:
        return (datetime.datetime.now(datetime.timezone.utc) - _aware(datetime.datetime.fromisoformat(t))).total_seconds() / 3600
    except Exception: return 9999

# ★ 分層 TTL（學 Arki·改成我的情況·2026-10-10）
LAYER_TTL = {
    "event": 24,        # 事件/日誌 → 1 天（高頻）
    "case": 72,         # 病例 → 3 天
    "method": 168,      # 方法 → 7 天（不常變）
    "identity": 720,    # 身份/憲法 → 30 天
}

# ★ 2026-10-13 老五修：kind 歸一化（治「亂起名 → 正式層看不到 → 假報超時」）
#   病因：我今天寫了 修復/道/纪要/机制/审计/学习/复盘/交付 等「野 kind」→ 各1條
#        → LAYER_TTL 只認 event/case/method/identity → event 層「看起來停了」
#   判據 C-老五-K1【kind 要歸一｜亂起名 = 哨兵瞎了｜自訂名先映射·再落庫】
KIND_MAP = {
    "修复":"case", "報修":"case", "修复记录":"case",
    "道":"identity", "憲法":"identity", "铁律":"identity",
    "纪要":"event", "會議":"event", "机制":"infra", "機制":"infra",
    "审计":"case", "審計":"case", "学习":"method", "學習":"method",
    "复盘":"case", "復盤":"case", "交付":"event", "交付物":"event",
    "infra":"infra",
}
def canon(kind):
    return KIND_MAP.get(kind, kind)


def _aware(dt):
    """★ 統一 aware：naive 當 UTC·aware 保持（修「改一處要查全鏈」）"""
    if dt is None: return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=datetime.timezone.utc)
    return dt

def layer_health():
    """★ 分層看：每層「最新」距今天·超該層 TTL 才報病"""
    out = []
    bad = False
    try:
        c = connect()
        for kind, ttl in LAYER_TTL.items():
            r = c.execute("SELECT max(ts) FROM memories WHERE kind=?", (kind,)).fetchone()
            if not r or not r[0]:
                out.append("%s 無" % kind); continue
            h = (datetime.datetime.now(datetime.timezone.utc) - _aware(datetime.datetime.fromisoformat(r[0]))).total_seconds() / 3600
            ok = h <= ttl
            if not ok: bad = True
            out.append("%s %.0fh/%dh%s" % (kind, h, ttl, "" if ok else "🔴"))
        c.close()
    except Exception as e:
        return False, "分層讀取失敗：" + str(e)[:40]
    return (not bad), "、".join(out)

def health():
    """★ 健康（分層版·學 Arki）：每層比 TTL（比一刀切準）"""
    n = count()
    if n == 0: return False, "庫是空的（從沒寫進）→ 靜默失憶"
    ok, detail = layer_health()
    if not ok: return False, "分層超時：" + detail
    return True, "%d 條 · %s" % (n, detail)

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "health"
    init()
    if cmd == "health":
        ok, msg = health()
        print(("  ✅ " if ok else "  🔴 ") + msg)
        sys.exit(0 if ok else 1)
    elif cmd == "add":
        kind, title, body = sys.argv[2], sys.argv[3], sys.argv[4]
        print("  ✅ 已記" if remember(kind, title, body) else "  🔴 寫入失敗")
    elif cmd == "list":
        c = connect()
        for r in c.execute("SELECT ts,kind,title FROM memories ORDER BY id DESC LIMIT 12"):
            print("  %s | %-8s | %s" % (r[0][:16], r[1], r[2][:50]))
        c.close()
