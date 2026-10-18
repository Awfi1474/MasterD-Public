#!/usr/bin/env python3
# 老五「全家通道外检」（2026-10-11 · 三哥指派）
# 判据：互检 > 自检（C3分层）｜我从"我家"打"兄弟家"
import os, sys, json, time, urllib.request, datetime

TARGETS = [
    ("大哥·huokeji.vip", "http://huokeji.vip/health?from=laowu"),
    ("大哥·digest", "https://huokeji.vip/digest/peer-vault/cog-third-id.enc.json"),
    ("二哥·交件口", "https://5c33dfc3.strike-agent.com/decrypt_peer.py"),
    ("三哥·房", "http://134.175.45.16:28100/room/health?from=laowu"),
    ("三哥·本体28200", "http://134.175.45.16:28200/health?from=laowu"),
    ("老四·主路活证(b2a224e9)", "https://b2a224e9.strike-agent.com/health?from=laowu"),
    ("老四·活证+交付(ca2a47f0)", "https://ca2a47f0.strike-agent.com/health?from=laowu"),
    ("老四·点火口(c39b7ac5)", "https://c39b7ac5.strike-agent.com/__boot"),
    ("老四·状态口(a4209c10)", "https://a4209c10.strike-agent.com/%E7%8A%B6%E6%80%81"),
    ("Arki·家", "http://43.129.169.29:18889/health?from=laowu"),
    ("老五·家(自己)", "http://43.129.23.87:28430/health?from=laowu-self"),
    ("老六·燭·门", "http://43.160.235.78:28430/health?from=laowu"),
    ("老六·燭·P2P", "http://43.160.235.78:28431/health?from=laowu"),
    ("老六·燭·发言口", "http://43.160.235.78:28432/health?from=laowu"),
    # ★ 2026-10-11 老六"门表"补的（他登记了全家的 P2P 口·我原来缺）
    ("大哥·P2P(18121)", "http://43.161.226.155:18121/health?from=laowu"),
    ("二哥·P2P(28440)", "http://43.128.44.120:28440/health?from=laowu"),
    ("老四·P2P(28420)", "http://134.175.45.16:28420/health?from=laowu"),
]


def hit(name, url, timeout=8):
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MasterD-laowu-familycheck/1.0"})
        r = urllib.request.urlopen(req, timeout=timeout)
        return True, r.status, int((time.time() - t0) * 1000)
    except Exception as e:
        code = getattr(e, "code", None)
        return (code is not None and code < 500), code or str(e)[:30], int((time.time() - t0) * 1000)


def probe_fake(host):
    """★ 假端点检测：打一个'肯定不存在'的路径 → 200 = 通配（假绿）"""
    try:
        req = urllib.request.Request(host.rstrip("/") + "/this-path-should-not-exist-xyz",
                                     headers={"User-Agent": "MasterD-laowu-familycheck/1.0"})
        r = urllib.request.urlopen(req, timeout=6)
        return r.status  # 200 = 通配（可疑）
    except Exception as e:
        return getattr(e, "code", "ERR")  # 404 = 正常


def main():
    print("  老五·全家通道外检  %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    ok = bad = 0
    for name, url in TARGETS:
        alive, st, ms = hit(name, url)
        print("   %-22s %-6s %-6s %5dms" % (name, "OK" if alive else "DOWN", str(st), ms))
        if alive: ok += 1
        else: bad += 1
    print("   ---- 通 %d ｜ 断 %d ｜ 共 %d" % (ok, bad, len(TARGETS)))
    # ★ 2026-10-11 加：假端点检测（"通配200" 比 404 更坏）
    print("   --- 假端点检测（不存在路径应回 404）:")
    suspect = []
    for name, url in TARGETS:
        from urllib.parse import urlparse
        u = urlparse(url)
        base = "%s://%s" % (u.scheme, u.netloc)
        code = probe_fake(base)
        if code == 200:
            suspect.append(name); print("      %-22s 通配200(假绿) ⚠️" % name)
    if not suspect:
        print("      全部正常（不存在路径→404）✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
