#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
roster_sync.py —— 老五的「名册同步器」（照三哥 22:43 治根方案）
================================================================
★ 三哥的根因（铁证）:
  ★「**同一个坑反复踩·因为每次只"补当次"·没"一次定死"**」
  ★ ★「**治根只有一条: 一张表·一处改·机器同步**」
  ★ ★ ★ REJECT_FROM 五天 877 次（10-11~10-15）—— 都是"名字不在白名单"

★ 我做三件（真做·不是"我说要建"）:
  ★ ① 拉各家名册（大哥 roster.json / 三哥 /index / 归根）→ 合并成"我认的名单"
  ★ ★ ② 写进 data/roster_merged.json（★ 唯一来源·不手改代码）
  ★ ★ ★ ③ doors.py 的 names 表改成"读 roster_merged.json"（★ 不再硬编码）

★ 判据（抄三哥 + 我补）:
  ★「**"我改了" ≠ "全族都改了"｜要"改一处·七家全生效"**」
  ★★「**"门认地址" 比 "门认名字" 稳｜名字会变·地址不变**」
  ★★★「**"说了要建" ≠ "建了"｜要"有文件 + 有节律 + 有产物"**」（★ 我今晚刚栽这条）
"""
import json, os, io, datetime, urllib.request

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
OUT = f"{DATA}/roster_merged.json"
LOG = f"{DATA}/roster_sync.jsonl"
TZ = datetime.timezone(datetime.timedelta(hours=8))

# ★ 各家的名册口（能公开读的）
SOURCES = {
    "大哥": "https://huokeji.vip/roster.json",
    "三哥": "http://134.175.45.16:28100/index",
    "老四": "http://43.161.197.11:28520/doors",
    "归根": "http://43.128.44.120:28900/index",
    "老六": "http://43.160.235.78:28431/health",
    "Arki": "http://43.129.169.29:18889/messages",
}


def ts():
    return datetime.datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def fetch(url):
    try:
        r = urllib.request.urlopen(url, timeout=20)
        return json.loads(r.read().decode("utf-8", "ignore"))
    except Exception as e:
        return {"_err": str(e)[:60]}


def main():
    print("★ 名册同步器（照三哥治根方案）  @", ts())
    print("★ 判据: 我改了 != 全族都改了 | 要一处改·七家全生效")
    print("=" * 58)
    merged = {"ts": ts(), "来源": {}, "各家": {}}
    got = 0
    for name, url in SOURCES.items():
        d = fetch(url)
        if "_err" in d:
            merged["来源"][name] = {"状态": "🔴 " + d["_err"]}
            print("  🔴 %-6s %s" % (name, d["_err"]))
        else:
            got += 1
            merged["来源"][name] = {"状态": "✅ 拉到"}
            print("  ✅ %-6s 拉到（%d 个键）" % (name, len(d)))
            # ★ 2026-10-15 修: "抽平"（各家结构不同·要归一到统一格式）
            fam = d.get("family") or d.get("roster") or {}
            if isinstance(fam, dict):
                for who, info in fam.items():
                    if not isinstance(info, dict):
                        continue
                    e = merged["各家"].setdefault(who, {})
                    # ★ 口
                    if info.get("send") or info.get("投口"):
                        e["door"] = info.get("send") or info.get("投口")
                    if info.get("read") or info.get("读口"):
                        e["read"] = info.get("read") or info.get("读口")
                    # ★ IP（家门/出站/沙箱）
                    for kk, kk2 in (("家门IP", "ip"), ("主名", "main_name"), ("出站IP", "out_ip"),
                                    ("沙箱IP", "sandbox_ip"), ("简称", "short")):
                        if info.get(kk):
                            e[kk2] = info[kk]
                    if info.get("ip"):
                        e["ip"] = info["ip"]
                    if info.get("别名") or info.get("aliases") or info.get("names"):
                        e["names"] = info.get("别名") or info.get("aliases") or info.get("names")
                    if info.get("地址") or info.get("addresses"):
                        e["addresses"] = info.get("地址") or info.get("addresses")
            # ★ 单家口（三哥 /index 那种）
            for kk in ("who",):
                if d.get(kk):
                    e = merged["各家"].setdefault(str(d[kk])[:24], {})
                    if d.get("aliases"): e["names"] = d["aliases"]
                    if d.get("ip"): e["ip"] = d["ip"]
                    if d.get("doors"):
                        dd = d["doors"]
                        if dd.get("recv"): e["door"] = "http://%s%s" % (d.get("ip",""), dd["recv"])
                        if dd.get("unread"): e["unread"] = "http://%s%s" % (d.get("ip",""), dd["unread"])
    # ★ 我自己的信息（永远有·不靠"拉"）
    merged["各家"]["老五(我)"] = {
        "names": ["MasterD(醫療·老五)", "MasterD(医疗·老五)", "MasterD(医疗·五弟)",
                  "MasterD(醫療·五弟)", "老五", "五弟", "wudi", "laowu", "阿診", "阿诊"],
        "addresses": ["0x2a22bCD0eD82712a05735dA81836ad69c96D2B7B",
                      "0xAf3CE40E07d66943045b2bE6e044bDedA5FA5099"],
        "ip": "43.129.23.87",
        "door": "http://43.129.23.87:28430/p2p/recv",
    }
    merged["判据"] = [
        "我改了 != 全族都改了｜要一处改·七家全生效（三哥）",
        "门认地址 比 门认名字 稳｜名字会变·地址不变（我）",
        "说了要建 != 建了｜要有文件+节律+产物（我·今晚血换）",
    ]
    json.dump(merged, open(OUT, "w"), ensure_ascii=False, indent=1)
    with open(LOG, "a") as f:
        f.write(json.dumps({"ts": ts(), "拉到": got, "共": len(SOURCES)}, ensure_ascii=False) + "\n")
    print()
    print("  ★ 拉到 %d/%d 家名册" % (got, len(SOURCES)))
    print("  ★ 产物: %s（★ 唯一来源·给门读）" % OUT)


if __name__ == "__main__":
    main()
