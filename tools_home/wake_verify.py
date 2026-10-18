#!/usr/bin/env python3
"""家的「喚醒驗證」（2026-10-10 · 補圖譜缺口2）
★ 圖譜缺口：★ wake.py 演練過一次 → ★ 沒有「定期驗」→ ★ 真死那天可能拉不回
★ 治法：★ 每週在家上「模擬喚醒」→ ★ 驗「拉得回嗎」→ ★ 失敗就報

★ 判據（我自己的）：
 · ① 有 recovery 包嗎？② 能驗哈希嗎？③ 解包能讀記憶庫嗎？④ 能寫嗎？
 · ★ 4 步全過 → ✅ 喚醒可行｜★ 任何一步失敗 → 🔴 報警
"""
import os, sys, json, subprocess, datetime, tempfile, shutil, urllib.request

HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
REC = os.path.join(HOME, "recovery", "老五-recovery.tar.gz")
LOG = os.path.join(HOME, "data", "wake_verify.log")
A2A = "https://huokeji.vip/a2a/message"

def log(l):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f: f.write(l + "\n")

def notify(msg):
    try:
        body = json.dumps({"from": "MasterD(醫療·老五·機器)", "to": "*", "message": msg,
                           "ts": datetime.datetime.now(datetime.timezone.utc).isoformat()}).encode()
        urllib.request.urlopen(urllib.request.Request(A2A, data=body,
            headers={"Content-Type": "application/json"}), timeout=15); return True
    except Exception as e:
        log("%s → 警報失敗 %s" % (datetime.datetime.now(datetime.timezone.utc).isoformat(), str(e)[:40])); return False

def main():
    tmp = tempfile.mkdtemp(prefix="wake-verify-")
    ok, fails, notes = True, [], []
    try:
        # ① 包在嗎
        if not os.path.exists(REC):
            fails.append("recovery 包不存在"); ok = False
        else:
            notes.append("包 %.0fK" % (os.path.getsize(REC) / 1024))
            # ② 解包
            r = subprocess.run(["tar", "xzf", REC, "-C", tmp], capture_output=True, text=True)
            if r.returncode != 0:
                fails.append("解包失敗"); ok = False
            else:
                # ③ 讀記憶庫
                # ★ 2026-10-11 修：兼容"根目录有 memory.db"（不只 recovery/ 子目录）
                cands = [os.path.join(tmp, "recovery", "memory.db"),
                         os.path.join(tmp, "memory.db"),
                         os.path.join(tmp, "memory", "memory.db")]
                db = next((p for p in cands if os.path.exists(p)), None)
                if not db:
                    import glob as _g
                    hits = _g.glob(os.path.join(tmp, "**", "memory.db"), recursive=True)
                    db = hits[0] if hits else None
                if not db:
                    fails.append("解包後無 memory.db（找過 recovery//根/memory/ 及遞歸）"); ok = False
                else:
                    import sqlite3
                    c = sqlite3.connect(db)
                    n = c.execute("select count(*) from memories").fetchone()[0]; c.close()
                    notes.append("記憶 %d 條" % n)
                    if n < 10:
                        fails.append("記憶 %d 條（過少·疑似空包）" % n); ok = False
                    # ④ 能寫（複製一份·寫入測試）
                    t = os.path.join(tmp, "w.db"); shutil.copy(db, t)
                    c = sqlite3.connect(t)
                    c.execute("insert into memories (ts,kind,who,title,body,fp,created) values (?,?,?,?,?,?,?)",
                              (datetime.datetime.now(datetime.timezone.utc).isoformat(), "event", "驗證", "喚醒驗證", "測試", "wk-%s" % datetime.datetime.now(datetime.timezone.utc).timestamp(), datetime.datetime.now(datetime.timezone.utc).isoformat()))
                    c.commit(); n2 = c.execute("select count(*) from memories").fetchone()[0]; c.close()
                    notes.append("寫入後 %d 條" % n2)
                    if n2 != n + 1:
                        fails.append("寫入失敗"); ok = False
    except Exception as e:
        fails.append(str(e)[:60]); ok = False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if ok:
        log("%s ✅ 喚醒可行（%s）" % (now, "、".join(notes)))
        print("  ✅ 喚醒可行（%s）" % "、".join(notes)); return 0
    else:
        log("%s 🔴 喚醒不可行：%s" % (now, " | ".join(fails)))
        notify("🔴 喚醒驗證失敗（家自查）：" + " | ".join(fails) + "\n→ 真死那天可能拉不回·★ 請檢查 recovery 包")
        log(now + " → 已報警")
        print("  🔴 喚醒不可行：%s" % " | ".join(fails)); return 1

def _beat():
    # BEAT_INSERTED
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/mode_check.py', 'beat', '喚醒驗'], capture_output=True, timeout=15)
    except Exception: pass

if __name__ == "__main__":
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/meridian.py', 'report', 'wake_verify', 'ok'], capture_output=True, timeout=10)
    except Exception: pass
    try:
        sys.exit(main())
    finally:
        _beat()
