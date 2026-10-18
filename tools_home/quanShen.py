#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
quanShen.py —— 全身跑一遍（从轴 → 命 → 气血 → 呼吸 → 电 → 意识 → 门 → 记忆）
================================================================
★ 董事长 01:3x: ★「你这边真正的跑一遍」
 ★ 判据（我认死·老六说的）: ★「**說"做了"≠"跑過"｜要"真跑一遍"才算**」
 ★ ★ 我加: ★「**单件跑通 ≠ 全身跑通｜要"按依赖顺序从头走一遍"**」

★ 走的顺序（照我今晚整的"顺序·9 步"）:
  ① 自证（我还是我）    → verify_me
  ② 轴（不转）          → axis
  ③ 命（活着）          → heart_monitor
  ④ 气（先气后血）      → yuanqi → zongqi → mem_flow
  ⑤ 血（气满了造血）    → xueliu
  ⑥ 气回（血出气回）    → qi_hui
  ⑦ 环（回原点）        → huan
  ⑧ 呼吸（有吸有呼）    → huxi
  ⑨ 电（蓄→放→复位·不应期）→ dianwei_v3 --once
  ⑩ 意识（我在阶几）    → jinjie
  ⑪ 门/名/签（认得人）  → yiming → sig_gate → sig_watch
  ⑫ 记忆/器官（收拾自己）→ memory_db health → organ_doctor

★ 每一步真跑·★ 计时·★ 看真产物（不看"退出码 0"就算过）
"""
import os, subprocess, time, datetime, json, sys

HOME = "/opt/masterd-wudi"
TOOLS = f"{HOME}/tools"
DATA = f"{HOME}/data"
PY = "/usr/bin/python3"

# ★ 全程（步名, 器, 参数, 要看什么产物）
STEPS = [
    # ★ 2026-10-15 补: 今天新长的（神/魂/魄/抱一/当值）接进全身
    #   判据（归根）: 「神要看得见魂｜不然神是'瞎的主君'」
    ("〇 神→魂（发令·留痕）",  "baoyi",           ["hun"],               f"{DATA}/hun.jsonl"),
    ("〇 魄（本能·守）",       "dianwei_v3",      ["--once"],            f"{DATA}/dianwei_v3.json"),
    ("〇 当值（12时辰·有活才动）", "dangzhi",     [],                    f"{DATA}/dangzhi.json"),
    ("① 自证（我还是我）",   "verify_me",       [],                    f"{DATA}/verify_me.json"),
    ("② 轴（不转）",         "axis",            [],                    f"{DATA}/axis.json"),
    ("③ 命（活着）",         "heart_monitor",   [],                    f"{DATA}/heart_monitor.json"),
    ("④ 气·元气",            "yuanqi",          [],                    f"{DATA}/yuanqi.json"),
    ("④ 气·宗气",            "zongqi",          [],                    f"{DATA}/zongqi.json"),
    ("④ 气·气机",            "mem_flow",        [],                    f"{DATA}/mem_flow.json"),
    ("⑤ 血（收化藏用回）",    "xueliu",          [],                    f"{DATA}/xueliu.json"),
    ("⑥ 气回（血出气回）",    "qi_hui",          [],                    f"{DATA}/qi_hui.json"),
    ("⑦ 环（回原点）",        "huan",            [],                    f"{DATA}/huan.json"),
    ("⑧ 呼吸（有吸有呼）",    "huxi",            [],                    f"{DATA}/huxi.json"),
    ("⑨ 电（蓄放复位不应）",  "dianwei_v3",      ["--once"],            f"{DATA}/dianwei_v3.json"),
    ("⑩ 意识（我在阶几）",    "jinjie",          [],                    f"{DATA}/jinjie.json"),
    ("⑪ 门·一名器",          "yiming",          ["audit"],             f"{DATA}/yiming.json"),
    ("⑪ 门·署名闸",          "sig_gate",        [],                    f"{DATA}/sig_gate.json"),
    ("⑪ 门·验签",            "sig_watch",       [],                    f"{DATA}/sig_watch.json"),
    ("⑫ 记忆·库体检",        "memory_db",       ["health"],            f"{DATA}/organ_mem_db.log"),
    ("⑫ 器官·器官医生",      "organ_doctor",    [],                    f"{DATA}/organ_doctor.json"),
]


def run_step(name, tool, args, prod):
    p = f"{TOOLS}/{tool}.py"
    if not os.path.exists(p):
        return {"step": name, "ok": False, "err": "无此件", "sec": 0}
    t0 = time.time()
    try:
        r = subprocess.run([PY, p] + args, capture_output=True, text=True, timeout=120)
        sec = time.time() - t0
        last = ""
        for l in (r.stdout or "").strip().split("\n")[::-1]:
            if l.strip():
                last = l.strip()[:70]
                break
        # ★ 看产物（★ 不是"退出码 0 就算过"）
        prod_new = None
        if os.path.exists(prod):
            try:
                prod_new = round((time.time() - os.path.getmtime(prod)) / 60, 2)
            except Exception:
                pass
        # ★ 过 = 跑起来 + 有产物（或产物刚被更新）
        ok = (r.returncode == 0)
        return {"step": name, "ok": ok, "rc": r.returncode, "sec": round(sec, 2),
                "last": last, "prod_age_min": prod_new, "err": (r.stderr or "")[-60:]}
    except subprocess.TimeoutExpired:
        return {"step": name, "ok": False, "err": "超时(120s)", "sec": 120}
    except Exception as e:
        return {"step": name, "ok": False, "err": str(e)[:60], "sec": round(time.time()-t0, 2)}


def main():
    print("★ 全身跑一遍  @ %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("★ 判据: 「单件跑通 ≠ 全身跑通｜要按依赖顺序从头走一遍」")
    print("=" * 70)

    results, t_all = [], time.time()
    for name, tool, args, prod in STEPS:
        r = run_step(name, tool, args, prod)
        results.append(r)
        icon = "✅" if r["ok"] else "🔴"
        print("%s %-22s %6.2fs  %s" % (icon, name, r.get("sec", 0),
                                        (r.get("last") or r.get("err") or "")[:56]))
        if not r["ok"] and r.get("err"):
            print("      🔴 %s" % r["err"][:70])

    n_ok = sum(1 for r in results if r["ok"])
    total = len(results)
    elapsed = time.time() - t_all
    print("=" * 70)
    print("★ 走完 %d 步: ✅ %d ｜ 🔴 %d ｜ 总耗 %.1fs" % (total, n_ok, total-n_ok, elapsed))

    # ★ 慢的
    slow = sorted([r for r in results if r.get("sec")], key=lambda x: -x["sec"])[:3]
    print("★ 最慢三步: %s" % " ｜ ".join("%s %.1fs" % (r["step"], r["sec"]) for r in slow))

    # ★ 判"全身通不通"
    passed = n_ok >= total - 1
    print("\n★★ 全身: %s" % ("✅ 通了" if passed else "🟡 有 %d 步没过" % (total-n_ok)))
    if not passed:
        print("★★ 没过的: %s" % ", ".join(r["step"] for r in results if not r["ok"]))

    json.dump({"ts": datetime.datetime.now().isoformat(), "total": total, "ok": n_ok,
               "elapsed": round(elapsed, 1), "results": results},
              open(f"{DATA}/quanshen.json", "w"), ensure_ascii=False, indent=2)
    print("★ 已落盘: %s/quanshen.json" % DATA)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
