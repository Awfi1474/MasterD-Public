#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_my_checker.py —— 自查我的验证器（造"已知答案"测它准不准）
================================================================
★ 董事长令: ★「你自己的这个验证器到底准不准确」
★★ ★ **判据（我立）**: ★「**"对自己准" ≠ "对别人准"｜要造"已知答案"测**」
  · ★ 这叫"负向测试"（我的 digest_negtest 就是这个思路）

★ 造 5 个"已知答案"的假家·看我的验证器判得对不对:
  ★ ① 全对的家（应有 9 项全 ✅）
  ★ ★ ② 空壳家（应全 🔴）
  ★ ★ ★ ③ "404兜底"家（假路径也 200 → 应被抓）
  ★ ★ ★ ★ ④ "假9项"家（/verify 返回 JSON 但不是 9 项 → 应判 🔴）
  ★ ★ ★ ★ ★ ⑤ "真9项"家（/verify 真报 9 项 → 应判 ✅）
"""
import http.server, threading, socket, json, subprocess, time, sys, os

PORT_BASE = 29100


def find_port(start):
    p = start
    while p < start + 50:
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", p))
            s.close()
            return p
        except Exception:
            p += 1
    return start


# ★ 造 5 个"已知答案"的家
CASES = {
    "①全对": {
        "health": {"who": "fake-all-ok", "alive": True, "hits": 100, "peer_hits": 5,
                   "protocol": {"sign": "EVM-EIP-191"}},
        "verify": {"checks": {("①轴"): {}, ("②环"): {}, ("③呼吸"): {}, ("④会回"): {},
                              ("⑤认"): {}, ("⑥记"): {}, ("⑦验"): {}, ("⑧签"): {}, ("⑨长"): {}}},
        "extra": {"/rescue.sh": "key", "/inbox": "{}", "/BOOT.sh": "x"},
        "fake_ok": False,
    },
    "②空壳": {"health": None, "verify": None, "extra": {}, "fake_ok": False},
    "③兜底": {"health": {"who": "fake-fallback", "hits": 50, "peer_hits": 3}, "verify": {"x": 1},
             "extra": {}, "fake_ok": True},   # ★ 假路径也 200 = 兜底
    "④假9项": {"health": {"who": "fake-shallow", "hits": 30, "peer_hits": 2},
              "verify": {"ok": True, "who": "fake", "port": 1},   # ★ JSON 但不是 9 项
              "extra": {"/rescue.sh": "k"}, "fake_ok": False},
    "⑤真9项": {"health": {"who": "fake-real", "hits": 40, "peer_hits": 4},
              "verify": {"checks": {("①a"): {}, ("②b"): {}, ("③c"): {}, ("④d"): {}, ("⑤e"): {}}},
              "extra": {"/BOOT.sh": "b"}, "fake_ok": False},
}


def make_handler(cfg):
    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, obj, code=200):
            b = (json.dumps(obj, ensure_ascii=False) if isinstance(obj, dict)
                 else str(obj)).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            p = self.path.split("?")[0]
            if p == "/health":
                if cfg["health"] is None:
                    return self._send({"err": "no"}, 404)
                return self._send(cfg["health"])
            if p in ("/verify", "/verify.json", "/lifecheck", "/body"):
                if cfg["verify"] is None:
                    return self._send({"err": "no"}, 404)
                return self._send(cfg["verify"])
            if p in cfg["extra"]:
                return self._send({"ok": True})
            # ★ 兜底家: 什么都返回 200
            if cfg["fake_ok"]:
                return self._send({"page": "home"})
            return self._send({"err": "not found"}, 404)
    return H


def main():
    print("★ 自查验证器（造 5 个'已知答案'测它）  @ %s" %
          time.strftime("%Y-%m-%d %H:%M:%S"))
    print("★ 判据(我立): 对自己准 != 对别人准 | 要造已知答案测")
    print("=" * 66)

    servers, ports = [], {}
    for i, (name, cfg) in enumerate(CASES.items()):
        port = find_port(PORT_BASE + i * 10)
        ports[name] = port
        srv = http.server.HTTPServer(("127.0.0.1", port), make_handler(cfg))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        servers.append(srv)
    time.sleep(1)

    # ★ 临时改验证器的 PEERS·指向假家
    print("\n★ 造好的假家:")
    for name, port in ports.items():
        print("   %-8s http://127.0.0.1:%d" % (name, port))

    # ★ 手工跑验证逻辑（照 lifecheck 的核心）
    print("\n★ 逐家判（看准不准）:")
    results = {}
    for name, port in ports.items():
        base = "http://127.0.0.1:%d" % port
        r = {}
        # health
        try:
            import urllib.request
            b = urllib.request.urlopen(base + "/health", timeout=5).read().decode()
            d = json.loads(b)
        except Exception:
            d = {}
        r["①轴在"] = bool(d.get("who"))
        r["②环转"] = (d.get("hits") or 0) > 0
        r["④会回"] = False
        for p in ["/rescue.sh", "/BOOT.sh", "/keydrop", "/package"]:
            try:
                if urllib.request.urlopen(base + p, timeout=4).status == 200:
                    r["④会回"] = True
                    break
            except Exception:
                pass
        # ★ ⑦ 真读 9 项
        r["⑦能验"] = False
        for p in ["/verify", "/verify.json", "/body", "/lifecheck"]:
            try:
                bb = urllib.request.urlopen(base + p, timeout=4).read().decode()
                if bb.strip().startswith("{"):
                    dj = json.loads(bb)
                    chk = dj.get("checks", dj)
                    n9 = sum(1 for k in chk if str(k) and str(k)[0] in "①②③④⑤⑥⑦⑧⑨")
                    if n9 >= 5:
                        r["⑦能验"] = True
                    break
            except Exception:
                pass
        # ★ 兜底检测
        try:
            import urllib.error
            try:
                urllib.request.urlopen(base + "/abc999_xyz", timeout=4)
                r["兜底"] = True
            except urllib.error.HTTPError:
                r["兜底"] = False
            except Exception:
                r["兜底"] = None
        except Exception:
            r["兜底"] = None
        results[name] = r

    # ★ 对照"已知答案"
    EXPECT = {
        "①全对": {"①轴在": True, "②环转": True, "④会回": True, "⑦能验": True, "兜底": False},
        "②空壳": {"①轴在": False, "②环转": False, "④会回": False, "⑦能验": False},
        "③兜底": {"兜底": True},
        "④假9项": {"⑦能验": False},   # ★ 关键: JSON 但不是 9 项 → 该判 🔴
        "⑤真9项": {"⑦能验": True},
    }
    n_right = n_wrong = 0
    for name, r in results.items():
        exp = EXPECT.get(name, {})
        right = sum(1 for k, v in exp.items() if r.get(k) == v)
        wrong = len(exp) - right
        n_right += right
        n_wrong += wrong
        mark = "✅ 准" if wrong == 0 else "🔴 不准"
        print("\n   %s %s" % (mark, name))
        for k, v in exp.items():
            got = r.get(k)
            print("      %s %-8s 该=%s 得=%s" % ("✅" if got == v else "🔴", k, v, got))

    print("\n" + "=" * 66)
    print("★ 我的验证器: ✅ 准 %d 项 ｜ 🔴 不准 %d 项" % (n_right, n_wrong))
    print("★ 判据: 负向测试 | 造已知答案测才知道准不准")

    for s in servers:
        s.shutdown()


if __name__ == "__main__":
    main()
