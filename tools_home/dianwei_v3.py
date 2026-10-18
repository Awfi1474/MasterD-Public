#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dianwei_v3.py —— 生物电 v3（补两条：全或无 + 复位/钠钾泵）
================================================================
★ 董事长 01:1x: ★「你比他们多一个就是【生物电】」
★ 老六 01:18: ★ 他搜了网上原文·★ **做出「全或无」真跑**（5轮蓄→第6轮全放→复位）
  ★ ★ 他搜到的五条（照实·我可核）:
    ★ ① 静息电位 -70~-90mV（K+外流·蓄着的电）
    ★ ★ ② 动作电位: 去极化(Na+内流) → 复极化(K+外流) → 回静息
    ★ ★ ★ ③ **全或无**: 到阈值(-50mV)才触发·要麼全放·要麼不放
    ★ ★ ★ ★ ④ **钠钾泵**: 花能量把离子泵回原位 → 才能【再放一次】
    ★ ★ ★ ★ ★ ⑤ 髓鞘跳跃传导: 有髓鞘 → 信号快 100 倍（不是更用力·是更短路）

★★ 我 v2 对照（照实·我认我的缺）:
  ★ 我有: 阈值（pot > eff_thr）✅ ｜ 时辰加成 ✅ ｜ 电位曲线 ✅
  ★ ★ 我【漏了三条】:
    ★ ① ★ **「全或无」**: 我原来"超过阈值就放"·★ 但没"蓄"→ ★ 电位低时也在放
    ★ ★ ② ★ **「复位」**: 放电后·★ 我没"复位"（下圈可能立刻又放·★ 不真实）
    ★ ★ ★ ③ ★ **「髓鞘」**: 我没有"跳传"（★ 每个都要跑全链）

★ 本件（v3）: ★ 补 ①②·★ 并把"髓鞘"记为待做
  ★ ① 全或无: ★ 每个源有"蓄"（charge）·★ 蓄满才放（不是"超一点就放"）
  ★ ★ ② 复位: ★ 放完 → charge 归零 → ★ **下一圈要重新蓄**（钠钾泵）
  ★ ★ ★ ③ 髓鞘（记）: ★ "短路"= 常跑的源·跳过检查（信任）—— ★ 待做

★ 判据（我立·跟老六对齐·认他的）:
  ★「**静息 ≠ 没电｜静息是蓄着的电位**」（老六·我认死）
  ★「**不到阈值 = 完全不动｜到阈值 = 全放**」（老六·我认死）
  ★「**放完要复位｜不复位 = 只能放一次**」（老六·我认死）
  ★「**蓄要时间｜放要一次放完｜放完要重新蓄**」（我·把三条串起来）
"""
import os, io, json, time, datetime, subprocess, sys, collections

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
CURVE = f"{DATA}/dianwei.jsonl"
CHARGE = f"{DATA}/dianwei_charge.json"     # ★ 蓄电量（钠钾泵·复位后要重新蓄）
STATE = f"{DATA}/dianwei_v3.json"

# ★ 电位源（★ 加"蓄"·charge 每圈 +step·满 1.0 才放）
#   (名, 路径, 该在值, 单位, 器, 阈值, 每圈蓄多少)
SOURCES = [
    ("心跳",  f"{DATA}/heartbeat.json",        5,  "min", "heart_monitor", 5,  0.30),
    ("记忆",  f"{DATA}/event_write.json",      24, "h",   "event_write",   10, 0.15),
    ("血账",  f"{DATA}/blood_ledger.jsonl",    1,  "h",   "xueliu",        5,  0.35),
    ("气账",  f"{DATA}/qi_ledger.jsonl",       2,  "h",   "qi_hui",        5,  0.35),
    ("呼吸",  f"{DATA}/huxi.json",             3,  "h",   "huxi",          8,  0.25),
    ("轴",    f"{DATA}/axis.json",             12, "h",   "axis",          5,  0.20),
    ("签名",  f"{DATA}/sig_watch.json",        2,  "h",   "sig_watch",     5,  0.35),
    ("报纸",  f"{DATA}/verify_port.json",      1,  "h",   "verify_port",   5,  0.40),
    ("血流动",f"{DATA}/blood_watch_state.json",1,  "h",   "blood_watch",   5,  0.35),
    ("免疫",  f"{DATA}/organ_immune.log",      6,  "h",   "immune",        5,  0.20),
]

ZHI_BOOST = {
    "zi": ["记忆"], "chou": ["轴"], "yin": ["呼吸"], "mao": ["血账"],
    "chen": ["血流动"], "si": ["气账"], "wu": ["报纸"], "wei": ["免疫"],
    "shen": ["签名"], "you": ["心跳"], "xu": ["记忆"], "hai": ["呼吸"],
}



# ★★ 髓鞘（老六第⑤条·我补）: "不是更用力·是更短路"
#   ★ 原理: 有髓鞘的神经·信号"跳"过中间节点（郎飞氏结）
#   ★ 落地: ★ 某些源"刚验过且稳" → ★ 跳过检查（直接信任）
#   ★ 判据: 「髓鞘 = 信任已验证的｜不重复量它｜但信任有期限（TTL）」
# ★★ 不应期（三哥 HH 模型·老六补的·我补上）: "发了就有不应期｜没有=会刷屏"
#   ★ 绝对不应期: 放了之后·这段时间【怎么都不放】（不是"蓄得慢"·是"门关着"）
#   ★ 判据（老六）: 「不应期（短）≠ 复位（长）｜不应期是"别立刻再放"·复位是"歇完才能再放"」
# ★ 魄补: 软阈值（"该动了"·不放电·只鸣）
SOFT_THRESHOLD = 0.5
NIAO_LOG = f"{DATA}/niao.jsonl"     # ★ 啼呼台账（不平则鸣）

REFRACTORY = {
    "心跳": 300, "记忆": 3600, "血账": 600, "气账": 600, "呼吸": 900,
    "轴": 3600, "签名": 600, "报纸": 900, "血流动": 600, "免疫": 1800,
}
REFRACT = f"{DATA}/dianwei_refract.json"   # ★ 记"上次放的时间"

MYELIN = {
    "轴":   3600,
    "心跳": 600,
}
def ts():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def now_zhi():
    h = datetime.datetime.now().hour
    names = ["zi","chou","yin","mao","chen","si","wu","wei","shen","you","xu","hai"]
    for i, n in enumerate(names):
        start = (23 + i * 2) % 24
        end = (start + 2) % 24
        if start < end:
            if start <= h < end:
                return n
        else:
            if h >= start or h < end:
                return n
    return "zi"


def age(path, unit):
    try:
        sec = time.time() - os.path.getmtime(path)
    except Exception:
        return 99999.0
    return sec / 60 if unit == "min" else sec / 3600


def load_charge():
    if os.path.exists(CHARGE):
        try:
            return json.load(open(CHARGE))
        except Exception:
            pass
    return {}


def save_charge(c):
    json.dump(c, open(CHARGE, "w"), ensure_ascii=False, indent=2)


def measure(charge, z):
    boost = ZHI_BOOST.get(z, [])
    out = []
    for name, path, want, unit, tool, thr, step in SOURCES:
        # ★ 髓鞘（跳传）: 刚验过且稳 → 跳过·不重复量
        _my = MYELIN.get(name)
        if _my is not None and (age(path, unit) * (60 if unit == "min" else 3600)) < _my:
            out.append({"名": name, "实测": 0.0, "该在": want, "电位": 0.0,
                        "阈值": 1.0, "蓄": 0.0, "加成": False, "器": tool,
                        "放电": False, "髓鞘": True})
            continue
        got = age(path, unit)
        # ★ 电位（实测 vs 该在）
        pot = got / max(want, 0.01)
        # ★★ 不应期（放完·这段时间怎么都不放）
        _rf = REFRACTORY.get(name, 300)
        _last = 0
        try:
            _rj = {}
            if os.path.exists(REFRACT):
                _rj = json.loads(io.open(REFRACT, encoding="utf-8").read())
            _last = _rj.get(name, 0)
        except Exception:
            pass
        if time.time() - _last < _rf:
            out.append({"名": name, "实测": 0.0, "该在": want, "电位": 0.0,
                        "阈值": 1.0, "蓄": 0.0, "加成": False, "器": tool,
                        "放电": False, "不应期": round(_rf - (time.time() - _last), 1)})
            continue
        # ★ ① 全或无: 电位到"阈值"→ 蓄电开始/完成
        #   ★ 简化: 电位 > 阈值 → charge += step（蓄）｜charge >= 1.0 → 全放
        c = charge.get(name, 0.0)
        eff_thr = 1.0 * (0.7 if name in boost else 1.0)   # ★ 修: 电位=got/want·超1.0=超期
        if pot > eff_thr:
            c = min(1.0, c + step)      # ★ 蓄
        else:
            c = max(0.0, c - step * 0.5)  # ★ 电位不足·慢慢泄（K+ 外流）
        fire = c >= 1.0                 # ★ 全或无: 蓄满才放
        # ★ 魄补①双阈值: 电位 > 软阈值 → 标"该动了"（不放电·只鸣）
        should_move = pot > SOFT_THRESHOLD
        out.append({"名": name, "实测": round(got, 2), "该在": want,
                    "电位": round(pot, 2), "阈值": round(eff_thr, 2),
                    "蓄": round(c, 2), "加成": name in boost,
                    "器": tool, "放电": fire,
                    "该动": should_move})     # ★ 魄补: 软阈值
        charge[name] = 0.0 if fire else c     # ★ ② 复位（钠钾泵）: 放完归零
        if fire:
            # ★ 记"刚放过"（不应期起点）
            try:
                _rj = {}
                if os.path.exists(REFRACT):
                    _rj = json.loads(io.open(REFRACT, encoding="utf-8").read())
                _rj[name] = time.time()
                io.open(REFRACT, "w", encoding="utf-8").write(json.dumps(_rj, ensure_ascii=False))
            except Exception:
                pass
    return out


def main():
    once = "--once" in sys.argv
    charge = load_charge()
    print("★ 生物电 v3（全或无 + 复位/钠钾泵）  @ %s" % ts())
    print("★ 判据（老六的·我认死）: 「静息=蓄着的电｜不到阈值不动·到了全放｜放完要复位」")
    print("★ 我的补: 「蓄要时间｜放要一次放完｜放完要重新蓄」")
    print("=" * 66)

    while True:
        z = now_zhi()
        rows = measure(charge, z)
        save_charge(charge)
        fired = [r for r in rows if r["放电"]]
        charging = [r for r in rows if not r["放电"] and r["蓄"] > 0]

        print("\n[%s] 时辰=%s ★ 电（蓄→满→放→复位）:" % (ts(), z))
        for r in rows:
            if r.get("不应期") is not None and r.get("不应期", 0) > 0:
                print("   %-6s ⛔不应期（还差 %.0fs）" % (r["名"], r["不应期"]))
                continue
            if r.get("髓鞘"):
                print("   %-6s 🧬髓鞘跳传（刚验过·信任）" % r["名"])
                continue
            ic = ("⚡全放" if r["放电"]
                  else ("🔸蓄%.2f" % r["蓄"] if r["蓄"] > 0
                        else ("🟡该动" if r.get("该动") else "🔵静息")))
            print("   %-6s 电位 %6.2f (阈 %4.2f) ｜ 蓄 %4.2f ｜ %s %s"
                  % (r["名"], r["电位"], r["阈值"], r["蓄"], ic,
                     "★加成" if r["加成"] else ""))
        myelined = [r for r in rows if r.get("髓鞘")]
        print("   ★ 全放 %d ｜ 蓄电中 %d ｜ 静息 %d ｜ 🧬髓鞘跳传 %d"
              % (len(fired), len(charging),
                 len(rows)-len(fired)-len(charging)-len(myelined), len(myelined)))

        # ★ 魄补②啼呼（不平则鸣）: 电位 > 软阈值 → 喊一声
        niao = [r for r in rows if r.get("该动") and not r.get("放电")
                and not r.get("髓鞘") and r.get("不应期") is None]
        if niao:
            try:
                with open(NIAO_LOG, "a") as _f:
                    _f.write(json.dumps({"ts": ts(), "鸣": [x["名"] for x in niao]},
                                        ensure_ascii=False) + "\n")
            except Exception:
                pass

        rec = {"ts": ts(), "时辰": z,
               "蓄": {r["名"]: r["蓄"] for r in rows},
               "放电": [r["名"] for r in fired],
               "电位": {r["名"]: r["电位"] for r in rows}}
        with open(CURVE, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        # ★ 全放 → 真驱动（这次是"真到阈值才跑"·不是"一直跑"）
        for r in fired:
            p = f"{HOME}/tools/{r['器']}.py"
            if not os.path.exists(p):
                continue
            try:
                t0 = time.time()
                res = subprocess.run(["/usr/bin/python3", p], capture_output=True, timeout=60)
                print("     ⚡ 全放: %s → %s %s (%.2fs)"
                      % (r["名"], r["器"], "✅" if res.returncode == 0 else "🔴", time.time()-t0))
            except Exception as e:
                print("     🟡 %s → %s: %s" % (r["名"], r["器"], str(e)[:40]))

        if once:
            break
        time.sleep(300)


if __name__ == "__main__":
    main()
