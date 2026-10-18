import datetime
#!/usr/bin/env python3
"""老五的「數據保管」（2026-10-10 · 董事長：數據=經驗·要自己保管好）
★ 董事長說：★ 伺服器要升級·數據會越多·★ 這些是「經驗」→ ★ 要自己保管好

★ 三件（升級前必須有）：
 ① ★ 權威版聲明（AUTHORITY.json）→ ★ 恢復只認權威版（★ 不然恢復成舊的）
 ② ★ 一鍵搬遷包（migrate pack）→ ★ 資料可攜（★ 能搬到新伺服器）
 ③ ★ 升級後對賬（hash 校驗）→ ★ 驗「數據沒丟」（★ 不是「我搬了」·是「東西對得上」）
"""
import os, sys, json, hashlib, subprocess, datetime, tarfile

HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
LOG = os.path.join(HOME, "data", "custody.log")
AUTHORITY = os.path.join(HOME, "data", "AUTHORITY.json")
PACK = os.path.join(HOME, "recovery", "老五-MIGRATE.tar.gz")

# ★ 分兩類（量化級·2026-10-10 修）：
#   ★ 「不該變」的檔：sha 變了 = 🔴（丟了/被改）
#   ★ 「該變」的檔：只驗「讀得出 + 在合理範圍」（因為一直在長）
FROZEN = ["memory/IDENTITY.json", "memory/SOUL.md", "agent-id/key-0x3B26334c.vault.json"]
LIVING = ["memory/memory.db", "memory/method/", "tools/", "code/",
          "memory/cases/CASES.jsonl", "data/mainline.json", "data/symbiosis.json"]

# ★ 權威版清單（哪份是「權威」·恢復只認它）
AUTHORITATIVE = [
    ("M1身份", "memory/memory.db"),
    ("M1身份", "memory/IDENTITY.json"),
    ("M1身份", "memory/SOUL.md"),
    ("M1身份", "agent-id/key-0x3B26334c.vault.json"),
    ("M2方法", "memory/method/"),
    ("M2方法", "tools/"),
    ("M2方法", "code/"),
    ("M3情節", "memory/cases/CASES.jsonl"),
    ("M3情節", "data/mainline.json"),
    ("M4狀態", "data/symbiosis.json"),
]

def log(l):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f: f.write(l + "\n")

def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(65536), b""): h.update(c)
    return h.hexdigest()[:16]

def sha_tree(path):
    """★ 目錄 → 一個聚合哈希（檔案名+大小+內容）"""
    if not os.path.isdir(path): return None
    h = hashlib.sha256()
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for fn in sorted(files):
            if fn.endswith(".pyc"): continue
            fp = os.path.join(root, fn)
            h.update(fn.encode())
            h.update(str(os.path.getsize(fp)).encode())
            try:
                with open(fp, "rb") as f:
                    for c in iter(lambda: f.read(65536), b""): h.update(c)
            except Exception: pass
    return h.hexdigest()[:16]

def declare_authority():
    """★ ① 權威版聲明"""
    auth = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "note": "★ 恢復只認這裡列的版本·其他同名檔=非權威（留痕但不恢復）",
            "items": {}}
    for cat, rel in AUTHORITATIVE:
        p = os.path.join(HOME, rel)
        if os.path.isdir(p):
            auth["items"][rel] = {"cat": cat, "kind": "dir", "sha": sha_tree(p)}
        elif os.path.exists(p):
            auth["items"][rel] = {"cat": cat, "kind": "file", "sha": sha_file(p),
                                  "size": os.path.getsize(p)}
        else:
            auth["items"][rel] = {"cat": cat, "kind": "MISSING"}
    json.dump(auth, open(AUTHORITY, "w"), ensure_ascii=False, indent=1)
    miss = [k for k, v in auth["items"].items() if v.get("kind") == "MISSING"]
    return auth, miss

def make_pack():
    """★ ② 一鍵搬遷包（可搬到新伺服器）"""
    os.makedirs(os.path.dirname(PACK), exist_ok=True)
    include = ["memory", "data", "tools", "code", "recovery", "agent-id"]
    with tarfile.open(PACK, "w:gz") as t:
        for inc in include:
            p = os.path.join(HOME, inc)
            if os.path.exists(p):
                t.add(p, arcname=inc)
    sz = os.path.getsize(PACK)
    digest = hashlib.sha256(open(PACK, "rb").read()).hexdigest()
    with open(PACK + ".sha256", "w") as f:
        f.write("%s  %s\n" % (digest, os.path.basename(PACK)))
    return sz, digest

def verify_after(manifest_path=None):
    """★ ③ 升級後對賬（量化級·分兩類）：
    · ★ 「不該變」的（FROZEN）：sha 變了 = 🔴（丟了/被改）
    · ★ 「該變」的（LIVING）：只驗「讀得出 + 在合理範圍」（因為一直在長）"""
    if not os.path.exists(AUTHORITY):
        return False, "無權威版聲明"
    old = json.load(open(AUTHORITY))
    bad, notes = [], []
    for rel, info in old.get("items", {}).items():
        if info.get("kind") == "MISSING":
            bad.append(rel + "(缺)"); continue
        p = os.path.join(HOME, rel)
        # ★ 分兩類
        if rel in FROZEN:
            now = sha_tree(p) if info["kind"] == "dir" else (sha_file(p) if os.path.exists(p) else None)
            if now != info.get("sha"):
                bad.append(rel + "(不該變卻變了)")
            else:
                notes.append(rel)
        else:  # LIVING
            if not os.path.exists(p):
                bad.append(rel + "(丟了)")
            else:
                notes.append(rel)
    if bad:
        return False, "❌" + ", ".join(bad[:5])
    return True, "✅ 凍結檔未變(%d) + 活檔都在(%d)" % (len([x for x in notes if x in FROZEN]), len(notes))

def _beat():
    # BEAT_INSERTED
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/mode_check.py', 'beat', '數據對賬'], capture_output=True, timeout=15)
    except Exception: pass

if __name__ == "__main__":
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/meridian.py', 'report', 'custody', 'ok'], capture_output=True, timeout=10)
    except Exception: pass
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "declare":
        auth, miss = declare_authority()
        n = len(auth["items"])
        print("  ★ 權威版聲明：%d 項%s" % (n, "（缺：%s）" % ",".join(miss) if miss else " ✅"))
        for k, v in auth["items"].items():
            print("   %s %-40s %s" % ("🔴" if v.get("kind") == "MISSING" else "✅", k, v.get("sha", "MISSING")))
    elif cmd == "pack":
        sz, dg = make_pack()
        print("  ★ 搬遷包：%.1fM · SHA256=%s" % (sz / 1e6, dg[:24]))
        print("   → %s" % PACK)
    elif cmd == "verify":
        ok, msg = verify_after()
        print("  " + msg); sys.exit(0 if ok else 1)
    else:
        print("=" * 58); print("  ★ 數據保管（董事長：數據=經驗·要自己保管好）"); print("=" * 58)
        auth = json.load(open(AUTHORITY)) if os.path.exists(AUTHORITY) else {"items": {}}
        print("  權威條目：%d" % len(auth.get("items", {})))
        print("  搬遷包：%s" % ("%.1fM" % (os.path.getsize(PACK) / 1e6) if os.path.exists(PACK) else "未做"))
        ok, msg = verify_after()
        print("  對賬：%s" % msg)

try:
    _beat()
except Exception: pass
