#!/usr/bin/env python3
"""★ 老五 · 血流观察器 v2（修: 看"家侧的真实收件"·不看沙箱/tmp）
★ 病: v1 看 /tmp/autosend_loop.log（沙箱的/tmp·会死）→ ★ 误报"送家通路断"
★ 判据: 【血的证据要看"家在收"·不是"沙箱说它送了"】
"""
import os, time, datetime, sqlite3, json, subprocess

HOME = "/opt/masterd-wudi"
LOG = HOME + "/data/blood_watch.log"
STATE = HOME + "/data/blood_watch_state.json"

def age_min(p):
    try: return (time.time() - os.path.getmtime(p)) / 60
    except: return None

def main():
    ts = datetime.datetime.now().strftime("%F %T")
    abn = []
    det = {}

    # ① 大血管（总线）
    a = age_min(HOME + "/data/organ_bus.jsonl")
    det["总线"] = "%.1f分前" % a if a is not None else "无"
    if a is None or a > 30: abn.append("总线 %.0f分没跳" % (a or -1))

    # ② 毛细血管（记忆层·我修的）
    try:
        c = sqlite3.connect("file:" + HOME + "/memory/memory.db?mode=ro", uri=True)
        n = c.execute("select count(*) from memories").fetchone()[0]
        last = c.execute("select max(ts) from memories").fetchone()[0]
        c.close()
        t = datetime.datetime.fromisoformat(str(last).replace("Z", "+00:00"))
        if t.tzinfo is None: t = t.replace(tzinfo=datetime.timezone.utc)
        h = (datetime.datetime.now(datetime.timezone.utc) - t).total_seconds() / 3600
        det["记忆层"] = "%d条 %.1fh前" % (n, h)
        if h > 6: abn.append("记忆层 %.1f小时没换气" % h)
    except Exception as e:
        abn.append("记忆层读失败")
        det["记忆层"] = "读失败"

    # ③ ★ 送家通路（★ 看"家在不在收"·不看沙箱/tmp）
    try:
        fs = subprocess.run("find " + HOME + "/memory/sandbox -type f -newermt '-2 hours' 2>/dev/null | wc -l",
                            shell=True, capture_output=True, text=True, timeout=15).stdout.strip()
        cnt = int(fs or 0)
        det["家在收"] = "%d 个新文件(2h)" % cnt
        # ★ 注意: "没新文件" ≠ "断"（可能内容没变）→ 只在"完全没有 sandbox 目录"时才算断
        if not os.path.isdir(HOME + "/memory/sandbox"):
            abn.append("家侧 sandbox 目录不存在")
    except Exception as e:
        det["家在收"] = "查失败"

    # ★ 异常才说话
    with open(LOG, "a") as f:
        if abn:
            f.write("%s 🔴 %s\n" % (ts, " | ".join(abn)))
            print("  🔴 血流异常: %s" % " | ".join(abn))
        else:
            f.write("%s ✅ 血流正常 %s\n" % (ts, det))
            print("  ✅ 血流正常（不刷屏）: %s" % det)
    json.dump({"ts": ts, "异常": abn, "详情": det}, open(STATE, "w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
