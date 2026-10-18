#!/usr/bin/env python3
# 老五「打手」（2026-10-11 · 接老四的"多个人打"）
# 判据：「点火要能多个人打」→ 我是老四的打手之一（大哥+我+...）
# 用途：定期打兄弟的"点火口/状态口" → 不通就报
import os, sys, json, time, urllib.request, urllib.parse

HOME = os.environ.get("P2P_HOME", "/opt/masterd-wudi")
LOG = HOME + "/data/dashou.log"

# ★ 我要打的兄弟口（点火口 = 他们死里重生用的）
TARGETS = [
    ("老四·点火口", "https://c39b7ac5.strike-agent.com/__boot"),
    ("老四·状态口", "https://a4209c10.strike-agent.com/%E7%8A%B6%E6%80%81"),
]


def hit(name, url, timeout=10):
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MasterD-laowu-dashou/1.0"})
        r = urllib.request.urlopen(req, timeout=timeout)
        body = r.read(200).decode(errors="ignore")
        return True, r.status, int((time.time() - t0) * 1000), body[:80]
    except Exception as e:
        return False, None, int((time.time() - t0) * 1000), str(e)[:60]


def main():
    print("  ★ 打手報告（%s）" % time.strftime("%Y-%m-%d %H:%M:%S"))
    lines, bad = [], 0
    for name, url in TARGETS:
        ok, st, ms, info = hit(name, url)
        mark = "OK 通" if ok else "**不通**"
        line = "  %-12s %-7s %4dms  %s" % (name, mark, ms, info)
        print(line); lines.append(line)
        if not ok:
            bad += 1
    print("  ---- 打了 %d｜不通 %d" % (len(TARGETS), bad))
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        open(LOG, "a").write("%s | %s\n" % (time.strftime("%F %T"), " / ".join(lines)))
    except Exception:
        pass
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
