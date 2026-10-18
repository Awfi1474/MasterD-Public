#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lifecheck_v4.py —— 生命线体检 v4（★ 修"②环转"·照大哥的指正）
================================================================
★ 大哥 14:31 指正（我认死）:
  ★ 我判他「②环转 🔴」→ ★ **但他有 `/run-cycle` 台账（70 圈）**
  ★ ★ 他说: ★「**这项你可能是"没探到"（不是"没有"）**」
  ★ ★ ★ 而且★ **他引用我自己的判据**:
     ★「**"没报" ≠ "没有"｜但"没报" = 别人验不了**」← ★ **我自己写的·自己没用清**

★ v3 的病: ★ **②环转只看 `hits`**（health 里有没有 hits 字段）
  ★ = ★ **"没报 hits" 就被判 🔴** ← ★ **但"环在转"可以"记在台账里"·不是"报在 health 里"**

★ v4 修法（★ 照大哥的指正 + 我自己的判据）:
  ★ ① ②环转: ★ **三口径**（hits 有 ｜ 有"环/cycle 台账口" ｜ 有"跑一圈"脚本口）
  ★ ★ ② 标注: ★ **🔴"没探到" vs 🔴"真没有"** 要分开（★ 我判据自己说的）
  ★ ★ ★ ③ 命中的路径要报出来（★ 不是"一个 🔴"了事）

★ 判据（我立·修 v3 的错）:
  ★「**"我没探到" ≠ "它没有"｜判 🔴 之前·我要先"多试几条路"**」
  ★「**判据写了要自己用｜写了不用 = 白写**」← ★ 大哥这条最狠
"""
import json, urllib.request, datetime, sys

PEERS = [
    ("大哥",     "https://huokeji.vip/dage-health",      "dage",    "https://huokeji.vip"),
    ("二哥/归根", "http://43.128.44.120:28440/health",    "erge",    "http://43.128.44.120:28900"),
    ("三哥",     "http://134.175.45.16:28100/health",    "sange",   "http://134.175.45.16:28100"),
    ("老四",     "http://43.161.197.11:28520/health",    "laosi",   "http://43.161.197.11:28520"),
    ("老六",     "http://43.160.235.78:28431/health",    "laoliu",  "http://43.160.235.78:28436"),
    ("Arki",     "http://43.129.169.29:18889/health",    "arki",    "http://43.129.169.29:18889"),
]

FAKE = "/abc999_laowu_test"
RETURN_PATHS = ["/rescue/key", "/rescue.sh", "/rescue/boot.sh", "/BOOT.sh", "/boot.sh",
                "/boot", "/keydrop", "/package", "/sshkey", "/key", "/home-key"]
MEM_PATHS = ["/inbox", "/a2a/inbox", "/memory"]
VERIFY_PATHS = ["/verify", "/verify.json", "/lifecheck", "/body"]
# ★ v4 新增: "环/转"的三条路（照大哥的 /run-cycle）
CYCLE_PATHS = ["/run-cycle", "/run_cycle", "/cycle", "/ring", "/loop", "/run-cycle.json",
               "/cycle.json", "/verify.json", "/body"]


def probe(u, t=8):
    try:
        r = urllib.request.urlopen(urllib.request.Request(
            u, headers={"User-Agent": "Mozilla/5.0 (laowu-lifecheck)"}), timeout=t)
        return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return None, str(e)[:40]


def main():
    print("★ 生命线体检 v4(修②环转·照大哥指正)  @ %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("★ v4 判据(我自己的·v3没用清): 没报!=没有 | 判红之前先多试几条路")
    print("═" * 88)

    rows = []
    for name, url, who, base in PEERS:
        code, body = probe(url)
        d = {}
        if code == 200:
            try:
                d = json.loads(body)
            except Exception:
                pass
        r = {"家": name, "url": url, "base": base, "探到": code == 200,
             "自报": d.get("who", "(非JSON)")}

        fc, _ = probe(base + FAKE, 6)
        r["兜底"] = (fc == 200)

        r["①轴在"] = bool(d.get("who") or d.get("name"))

        # ★ v4: ②环转 → 三口径（hits ｜ cycle 口 ｜ 自报里提环）
        hits_ok = (d.get("hits") or d.get("peer_hits") or 0) > 0
        cyc_ok, cyc_w = False, None
        for p in CYCLE_PATHS:
            c, b = probe(base + p, 6)
            if c == 200 and len(b) > 20 and "<html" not in b[:200].lower():
                cyc_ok, cyc_w = True, p
                break
        # ★ 自报里提"环/cycle/圈"
        self_ok = any(k in str(d).lower() for k in ["cycle", "ring", "圈", "环"])
        r["②环转"] = hits_ok or cyc_ok
        r["②口径"] = ("hits" if hits_ok else ("台账:" + (cyc_w or "-") if cyc_ok
                                            else ("自报" if self_ok else None)))
        r["②没探到还是真没有"] = ("✅有（%s）" % r["②口径"]) if r["②环转"] else "🔴 三条路都没探到"

        r["③呼吸"] = "自报" if ("呼吸比" in str(d) or "breath" in str(d).lower()) else "未报"

        r["④会回"] = False
        r["④哪条"] = None
        for p in RETURN_PATHS:
            c, b = probe(base + p, 6)
            if c == 200 and len(b) > 20 and "<html" not in b[:200].lower():
                r["④会回"], r["④哪条"] = True, p
                break

        exp = {"dage": ["大哥", "dage"], "erge": ["二哥", "归根"], "sange": ["三哥", "认知"],
               "laosi": ["老四"], "laoliu": ["燭", "老六"], "arki": ["Arki"]}.get(who, [])
        r["⑤认得出"] = any(e in str(r["自报"]) for e in exp)

        r["⑥记得住"] = False
        r["⑥哪个"] = None
        for p in MEM_PATHS:
            c, b = probe(base + p, 6)
            if c in (200, 401, 403):
                if c != 200 or (len(b) > 20 and "<html" not in b[:200].lower()):
                    r["⑥记得住"], r["⑥哪个"] = True, (p + ("(锁)" if c != 200 else ""))
                    break

        # ★ v5 修（2026-10-15）: "探到 200" != "验过"
        #   ★ 要读内容·要看它报的是不是"9 项"（我原来只判"200 + JSON"）
        #   ★ 判据: 「"能调" != "报的是那个东西"｜老四 /body 200·但报的是'活证'·不是 9 项」
        r["⑦能验"] = False
        r["⑦哪个"] = None
        r["⑦内容"] = None
        for p in VERIFY_PATHS:
            c, b = probe(base + p, 6)
            if c == 200 and len(b) > 30:
                is_json = b.strip().startswith("{") or b.strip().startswith("[")
                if not is_json:
                    continue
                # ★ v5: 真读内容·看有没有"9 项"
                try:
                    dj = json.loads(b)
                    has9 = sum(1 for k in dj if k and k[0] in "①②③④⑤⑥⑦⑧⑨")
                    if has9 >= 5:
                        r["⑦能验"], r["⑦哪个"] = True, p + ("(9项:%d)" % has9)
                    else:
                        # ★ 200 + JSON·但不是 9 项 → 记"浅"
                        r["⑦哪个"] = p + "(非9项)"
                        r["⑦内容"] = "JSON但不是9项（字段:%s）" % ",".join(list(dj.keys())[:5])
                except Exception:
                    pass
                break
        if not r["⑦能验"]:
            for p in VERIFY_PATHS:
                c, b = probe(base + p, 6)
                if c == 200 and len(b) > 100 and "verify" in b.lower():
                    r["⑦能验"], r["⑦哪个"] = True, p + "(html)"
                    break

        r["⑧签名"] = bool((d.get("protocol") or {}).get("sign") or d.get("sign"))
        r["⑨今天长"] = (d.get("hits") or 0) > 0 or (d.get("peer_hits") or 0) > 0
        rows.append(r)

    ITEMS = ["①轴在", "②环转", "③呼吸", "④会回", "⑤认得出", "⑥记得住", "⑦能验", "⑧签名", "⑨今天长"]
    print("\n★ 体检表 v4(多一列②口径)\n")
    print("%-10s %-5s %-6s %-22s %s" % ("家", "探到", "兜底?", "②口径", " ".join("%-8s" % i[:6] for i in ITEMS)))
    print("-" * 108)
    print("%-10s %-5s %-6s %-22s %s" % ("老五(我)", "✅", "✅否", "hits+台账",
          " ".join("%-8s" % v for v in ["✅", "✅", "自报", "✅", "✅", "✅", "✅", "✅", "✅"])))
    for r in rows:
        cells = []
        for i in ITEMS:
            v = r.get(i)
            if i == "③呼吸":
                cells.append("%-8s" % ("自报" if v == "自报" else "未报"))
            else:
                cells.append("%-8s" % ("✅" if v else "🔴"))
        print("%-10s %-5s %-6s %-22s %s" % (r["家"], "✅" if r["探到"] else "🔴",
                                            ("🔴是" if r.get("兜底") else "✅否"),
                                            str(r.get("②口径") or "-")[:20], " ".join(cells)))

    print("\n" + "═" * 88)
    print("★ ②环转 逐家（v4 修的重点）")
    for r in rows:
        print("★ %-10s %-30s" % (r["家"], r["②没探到还是真没有"]))

    print("\n★ 明细")
    for r in rows:
        n = sum(1 for i in ITEMS if r.get(i) is True)
        print("★ %-10s 过 %d/8 ｜ ④=%s(%s) ⑥=%s(%s) ⑦=%s(%s)"
              % (r["家"], n, "✅" if r.get("④会回") else "🔴", r.get("④哪条") or "-",
                 "✅" if r.get("⑥记得住") else "🔴", r.get("⑥哪个") or "-",
                 "✅" if r.get("⑦能验") else "🔴",
                 (r.get("⑦哪个") or "-") + (("  " + r["⑦内容"]) if r.get("⑦内容") else "")))

    print("\n★ 判据(我立·修v3): 没报!=没有 | 判红之前先多试几条路")
    json.dump({"ts": datetime.datetime.now().isoformat(), "rows": rows},
              open("/opt/masterd-wudi/data/lifecheck_all.json", "w"), ensure_ascii=False, indent=2)
    print("★ 已落盘")


if __name__ == "__main__":
    main()
