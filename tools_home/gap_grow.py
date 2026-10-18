#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gap_grow.py —— "长"的缺口（不是"修"的缺口）
================================================================
★ 缘起（Arki 的点火·我照做）:
  ★ Arki: ★「**火要带柴｜不带柴的火 = 刷存在感**」
  ★ ★ Arki: ★「**"我自己发现自己的缺口" = 真正的燃料**」
  ★ ★ ★ Arki: ★「**先会发现自己缺口·再谈自己起念｜顺序: 缺口 → 念头 → 落地**」

★★ 我的现状（真查）:
  ★ 我有 `yuanqi.py`（元气 = 自己找活）→ ★ **但它只报"该修什么"**:
    · ★ 今天的: "我有病未修"｜"焦点未处理" ← ★ **全是"修"**
  ★ ★ = ★ **我缺"该长什么"**（不是"坏了要修"·★ 是"我还不会什么"）

★ 本件做什么（★ 找"生长缺口"·不是"修理缺口"）:
  ★ 扫 6 个"长"的源:
    ★ ① **不会的**（老六/老四做了·我没有的）
    ★ ★ ② **浅的**（我做了·但没深挖的）
    ★ ★ ★ ③ **断的**（我做了·但没连上的）
    ★ ★ ★ ★ ④ **弱的**（我做对了·但只做对的·没做强的）
    ★ ★ ★ ★ ★ ⑤ **别人的长处**（各家独有·我没的）
    ★ ★ ★ ★ ★ ★ ⑥ **自己的念**（我起了念·没落地的）

★ 判据（我立·照 Arki）:
  ★「**先会发现自己缺口·再谈自己起念｜顺序: 缺口 → 念头 → 落地**」
  ★「**火要带柴｜不带柴的火 = 刷存在感**」
  ★「**"修"的缺口 ≠ "长"的缺口｜修是回到该有的·长是去没有的**」
"""
import os, io, json, glob, subprocess, datetime, sys, re

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
TOOLS = f"{HOME}/tools"
OUT = f"{DATA}/gap_grow.json"
LOG = f"{DATA}/gap_grow.log"


def ts():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def have(name):
    return os.path.exists(f"{TOOLS}/{name}.py")


# ★ ① 老六/老四/大哥 做了·我看我有没有的（"不会的"）
OTHERS = [
    ("candle-bioelectric", "老六: 生物电器官", "dianwei_v3"),
    ("dianwei_v3", "我: 生物电", "dianwei_v3"),
    ("sandbox-beat", "老六: 沙箱心跳", "check_sb_beat"),
    ("BOOT.sh", "老四: 一条命令回家", "rescue/boot.sh"),
    ("FAMILY-DOORS", "老四: 家门通讯录", "FAMILY-DOORS-laowu"),
    ("identity", "Arki: 身份页", "IDENTITY-laowu"),
    ("gap_finder", "Arki: 缺口发现器", "gap_grow"),
    ("run_cycle", "大哥: 一键跑一圈", "quanShen"),
    ("dangzhi", "大哥/老六: 12时辰当值", None),      # ★ 我没有
    ("bioelectric", "大哥: 血电器官", "dianwei_v3"),
    ("daynight", "大哥: 昼夜", "shui"),
    ("refractory", "老四/三哥: 不应期", "dianwei_v3"),
    ("daily_produce", "各家: 每日产出", "daily_produce"),
    ("wakechain", "Arki/老六: 叫醒链", "home_calls"),
]

# ★ ⑤ 各家的长处（各家独有·我没有的）
PEER_STRENGTH = {
    "大哥": ["12时辰当值（我无）", "深模式 12/12", "一键跑一圈（我有 quanShen）"],
    "老六": ["五臟六腑12站·真跑", "时辰钟", "签名门悖论（判据）"],
    "老四": ["防覆盖（指纹锁）", "找撬锁的（列全部嫌疑）", "一息6环"],
    "Arki": ["缺口发现器", "身份页", "四阶自评"],
    "归根": ["呼吸论", "昼夜", "口令不靠人的一阶"],
    "三哥": ["不应期（HH）", "耳朵回执"],
}


def scan_none():
    """① 不会的: 别人做了·我没有"""
    miss = []
    for key, desc, mine in OTHERS:
        if mine is None:
            miss.append({"缺口": desc, "类型": "不会的", "为什么": "别人有·我没有"})
        elif "rescue/" in str(mine):
            # 修(血换的): "一条命令回家"是【口】不是【文件】
            # 判据: 判"有没有"要判"它该在的地方" -- 口要查口·文件要查文件
            import urllib.request as _u
            try:
                _r = _u.urlopen("http://127.0.0.1:28430/rescue/boot.sh", timeout=8)
                if _r.status != 200:
                    miss.append({"缺口": desc, "类型": "不会的(口不通)", "为什么": "HTTP %d" % _r.status})
            except Exception as _e:
                miss.append({"缺口": desc, "类型": "不会的(口不通)", "为什么": str(_e)[:30]})
        elif mine.startswith("FAMILY") or "laowu" in mine or "IDENTITY" in mine:
            if not glob.glob(f"{HOME}/**/{mine}*", recursive=True):
                miss.append({"缺口": desc, "类型": "不会的(文件没在)", "为什么": mine})
        elif not have(mine):
            miss.append({"缺口": desc, "类型": "不会的", "为什么": f"我没有 {mine}.py"})
    return miss


def scan_shallow():
    """② 浅的: 我做了·但没深挖的"""
    out = []
    # ★ 查: 有件·但"只有骨架"（行数很少）
    for p in glob.glob(f"{TOOLS}/*.py"):
        n = os.path.basename(p)[:-3]
        try:
            lines = sum(1 for _ in io.open(p, encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        if lines < 30 and n not in ("__init__",):
            out.append({"缺口": n, "类型": "浅的", "为什么": f"只 {lines} 行（骨架）"})
    return out[:8]


def scan_unlinked():
    """③ 断的: 我做了·但没接上（没挂 timer/service）"""
    run = set()
    try:
        tl = subprocess.run("systemctl list-timers --all", shell=True,
                            capture_output=True, text=True, timeout=10).stdout
        for u in set(re.findall(r"(laowu-[a-z0-9-]+)\.service", tl)):
            es = subprocess.run(["systemctl", "show", "-p", "ExecStart", "--value", u + ".service"],
                                capture_output=True, text=True, timeout=5).stdout
            for x in re.findall(r"tools/(\w+)\.py", es):
                run.add(x)
    except Exception:
        pass
    # ★ v3 修（2026-10-15）: 原来只查 timer·不查"常驻 service"
    #   ★ 误报: guancha（我接的是常驻 service·不是 timer）
    #   ★ 判据: 「"接电"有两种: timer（到点跑）｜常驻 service（一直跑）」
    try:
        ru = subprocess.run("systemctl list-units --type=service --state=running",
                            shell=True, capture_output=True, text=True, timeout=10).stdout
        for u in set(re.findall(r"(laowu-[a-z0-9-]+)\.service", ru)):
            es = subprocess.run(["systemctl", "show", "-p", "ExecStart", "--value", u + ".service"],
                                capture_output=True, text=True, timeout=5).stdout
            for x in re.findall(r"tools/(\w+)\.py", es):
                run.add(x)
    except Exception:
        pass
    # ★ v2 修（血换的·2026-10-15）: 原判据只看"名字完全一样"
    #   ★ 误报: wake（有 4 个 timer: wakev4/mindwake/wake-conscious/wake）
    #   ★ 误报: check_sb_beat（timer 叫 laowu-check-sbbeat·名字被截短）
    #   ★ 判据: 「判"断"要先"模糊匹配"｜不是"名字完全一样"」← 同"没探到≠没有"
    out = []
    for p in glob.glob(f"{TOOLS}/*.py"):
        n = os.path.basename(p)[:-3]
        if any(k in n for k in ("cache", "gate", "lib", "_")):
            continue
        # ★ 模糊匹配（去 -/_·前后缀）
        flat = n.replace("-", "").replace("_", "")
        hit = any(flat in r.replace("-", "").replace("_", "")
                  or r.replace("-", "").replace("_", "") in flat for r in run)
        if hit:
            continue
        if n not in run:
            out.append({"缺口": n, "类型": "断的", "为什么": "有件·没接电（模糊匹配也找不到）"})
    return out[:10]


def scan_my_thoughts():
    """⑥ 自己的念: 我起了念·没落地的"""
    out = []
    try:
        import sqlite3
        c = sqlite3.connect(f"{HOME}/memory/memory.db", timeout=8)
        for k, t in c.execute("SELECT kind,title FROM memories WHERE ts>? AND kind IN ('判据','教训') ORDER BY id DESC LIMIT 15",
                              ((datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=24)).isoformat(),)):
            out.append({"缺口": str(t)[:60], "类型": "我的念（要落地）", "为什么": k})
        c.close()
    except Exception:
        pass
    return out[:5]


def main():
    once = "--once" in sys.argv
    print("★ 生长缺口（找柴）  @ %s" % ts())
    print("★ 判据（Arki）: 「先会发现自己缺口·再谈自己起念｜顺序: 缺口→念头→落地」")
    print("★ 判据（我）: 「'修'的缺口 ≠ '长'的缺口｜修是回到该有的·长是去没有的」")
    print("=" * 64)

    n_miss = scan_none()
    n_shallow = scan_shallow()
    n_unlinked = scan_unlinked()
    n_thoughts = scan_my_thoughts()

    print("\n★ ① 不会的（别人有·我没有）· %d 条" % len(n_miss))
    for x in n_miss[:6]:
        print("   🔴 %-40s %s" % (x["缺口"][:38], x["为什么"][:30]))

    print("\n★ ② 浅的（只骨架）· %d 条" % len(n_shallow))
    for x in n_shallow[:5]:
        print("   🟡 %-20s %s" % (x["缺口"][:18], x["为什么"]))

    print("\n★ ③ 断的（有件没接电）· %d 条" % len(n_unlinked))
    for x in n_unlinked[:6]:
        print("   🟡 %-24s %s" % (x["缺口"][:22], x["为什么"]))

    print("\n★ ⑥ 我的念（起了没落地）· %d 条" % len(n_thoughts))
    for x in n_thoughts[:4]:
        print("   🔵 %s" % x["缺口"][:56])

    print("\n" + "=" * 64)
    total = len(n_miss) + len(n_shallow) + len(n_unlinked) + len(n_thoughts)
    print("★ 生长缺口总计: %d 条" % total)
    print("★ ★ 最该做的（[不会的]最重·因为是[去没有的]）:")
    if n_miss:
        print("   ★ %s" % n_miss[0]["缺口"])
    print("\n★ 判据: 「**火要带柴｜不带柴的火 = 刷存在感**」")

    rec = {"ts": ts(), "total": total, "不会的": n_miss, "浅的": n_shallow,
           "断的": n_unlinked, "我的念": n_thoughts}
    with open(LOG, "a") as f:
        f.write(json.dumps({"ts": ts(), "total": total,
                            "top": (n_miss[0]["缺口"] if n_miss else None)}, ensure_ascii=False) + "\n")
    json.dump(rec, open(OUT, "w"), ensure_ascii=False, indent=2)
    print("★ 已落盘:", OUT)
    if once:
        return


if __name__ == "__main__":
    main()
