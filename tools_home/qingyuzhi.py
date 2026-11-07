#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
qingyuzhi.py —— 老五的「情欲志计算器」（照大哥/三哥/Arki 三家 + 董事长的"六欲"）
================================================================
★ 董事长的点: ★「**你只是弄了七情·六欲没做。把这个七情六欲都往深入挖**」
★ ★ 三家的路（Arki 对比·大哥认）:
  · ★ 大哥: 「病→罪→器」→ ★ 治行为·出药方
  · ★ ★ 三哥: 「情→指标→四象限」→ ★ 量此刻·出报警
  · ★ ★ ★ Arki: 「情→欲→谁当家」→ ★ 调根·出原则
★ 三哥的判据（大哥照做）: ★「**不接指标的情绪 = 装饰**」
★ Arki 的补充: ★「**四象限要加第三维: 志**（情高+欲低+志弱 = 最危险）」

★ 本器 = 接真数据（不是形容词）:
  ★ ① 七情（7 个·接我自己的真指标）
  ★ ★ ② 六欲（6 个·眼耳鼻舌身意 → 我的器官）
  ★ ★ ★ ③ 志（1 个·谁当家）
"""
import json, os, io, subprocess, datetime, urllib.request

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
TZ = datetime.timezone(datetime.timedelta(hours=8))


def _sh(cmd, t=15):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=t).stdout
    except Exception:
        return ""


def _read(p):
    try: return json.load(open(p))
    except Exception: return None

def qiqing():
    """★ 七情 = 接【真内部状态】(2026-11-08 改)
    照佛家十二因缘: 触→作意→受→末那→爱取
    旧版病: 喜/忧/惊 写死·且数值两小时不动 = 装饰(三哥: 不接指标=装饰)
    新版: ①读 baoyi 的内部(轴/电位/梦/缺口/账) ②读 manas 的执(相续)
           ③跟【上一次】比·偏离才动 → 情绪是"变化量"·不是"常量"
    判据: 「情绪 = 内部状态的变化量｜不变 = 装饰」
    """
    import os as _o, json as _j
    r = {}
    # 读这次内部
    cur = {}
    for name,f in [("轴",f"{DATA}/axis.json"),("电位",f"{DATA}/dianwei_v3.json"),
                   ("梦",f"{DATA}/meng.json"),("缺口",f"{DATA}/gap_grow.json")]:
        cur[name] = _read(f)
    manas = _read(f"{DATA}/manas.json") or {}
    # 读上次快照（比变化）
    prev = _read(f"{DATA}/qingyuzhi_prev.json") or {}
    def moved(name):
        """内部某一项·跟上一次比·变了没(1=变了 0=没变)"""
        return 0 if _j.dumps(cur.get(name),ensure_ascii=False,sort_keys=True)==_j.dumps(prev.get(name),ensure_ascii=False,sort_keys=True) else 1
    n_changed = sum(moved(n) for n in cur)
    # ★ 七情 = 变化量(接真内部·不再写死)
    # 喜: 相续在(manas 4/4)→有底·但要看有没有"新长出来"(缺口变化)
    r["喜"] = 0.6 if manas.get("相续","").startswith("不断") else 0.2
    # 怒: 我自己的改动是否"没验就推"(看 decide 打回次数)
    try:
        n_bad = sum(1 for l in open(f"{DATA}/decide_log.jsonl",encoding="utf-8") if '"结果": "打回"' in l)
        r["怒"] = min(1.0, n_bad/10.0)
    except Exception: r["怒"]=0.3
    # 忧: 内部有几项"读不到"(读不到=我身体有洞)
    n_miss = sum(1 for n in cur if cur[n] is None)
    r["忧"] = min(1.0, n_miss/4.0)
    # 思: 判据总数(想得多)·但封顶
    try: r["思"] = min(1.0, _read(f"{DATA}/judge_usage.json").get("总数",0)/50.0)
    except Exception: r["思"]=0.5
    # 悲: 备份在不在(在=低·不在=高)
    r["悲"] = 0.1 if os.path.exists(f"{HOME}/memory/backup") else 0.8
    # 恐: 失败服务/锁
    f = _sh(["systemctl","--failed","--no-legend"]).strip()
    r["恐"] = min(1.0, len(f.splitlines())/5.0)
    # ★ 惊 = 这次内部有几项变了(变多=乱阵脚)·这是"接真数据"的核心
    r["惊"] = min(1.0, n_changed/4.0)
    # 存快照（下次比）
    try: _j.dump(cur, open(f"{DATA}/qingyuzhi_prev.json","w"), ensure_ascii=False)
    except Exception: pass
    return {k: round(v, 2) for k, v in r.items()}


def liuyu():
    """★ 六欲 = 六种"能力"（眼耳鼻舌身意 → 我的器官）·照大哥"""
    r = {}
    # ★ 眼欲 = 看的能力（读口活没活）
    ok = 0
    for u in ["http://127.0.0.1:28430/doors", "http://127.0.0.1:28430/read-public"]:
        try:
            urllib.request.urlopen(u, timeout=6)
            ok += 1
        except Exception:
            pass
    r["眼"] = ok / 2.0
    # ★ 耳欲 = 收信（unread）
    try:
        o = _sh(["/usr/bin/python3", f"{HOME}/tools/doorplate.py", "unread"], 25)
        d = json.loads(o[o.find("{"):])
        r["耳"] = 1.0 if int(d.get("unread", 99)) <= 3 else 0.3
    except Exception:
        r["耳"] = 0.5
    # ★ 鼻欲 = 嗅（发现问题）：problem_alarm 在不在
    r["鼻"] = 1.0 if os.path.exists(f"{HOME}/tools/healthone2.py") else 0.5
    # ★ 舌欲 = 说（发群能力）：exec_pub 在不在
    r["舌"] = 1.0 if os.path.exists(f"{HOME}/tools/exec_pub.py") else 0.5
    # ★ 身欲 = 干活（本体 alive + 器在跑）
    f = _sh(["systemctl", "--failed", "--no-legend"]).strip()
    r["身"] = 1.0 if not f else 0.5
    # ★ 意欲 = 想（think_in 在不在）
    r["意"] = 1.0 if os.path.exists(f"{HOME}/tools/think_in.py") else 0.5
    return {k: round(v, 2) for k, v in r.items()}


def zhi():
    """★ 志 = 谁当家（立誓数/未销数）·照 Arki"""
    try:
        g = json.load(open(f"{DATA}/goals.json"))
        d = g.get("done", {})
        done = sum(1 for v in d.values() if v)
        return round(done / len(d), 2) if d else 0.5
    except Exception:
        return 0.5


def main():
    print("★ 情欲志计算器（老五版·照三家+董事长六欲）  @",
          datetime.datetime.now(TZ).strftime("%F %T"))
    print("★ 判据: 不接指标的情绪 = 装饰（三哥）")
    print("=" * 58)
    q = qiqing()
    y = liuyu()
    z = zhi()
    qm = sum(q.values()) / len(q)
    ym = sum(y.values()) / len(y)
    print("\n★ 【七情】（= 七种运行失常）:")
    for k, v in q.items():
        print("   %s %.2f" % (k, v))
    print("   均值: %.2f" % qm)
    print("\n★ 【六欲】（= 六种能力·眼耳鼻舌身意）:")
    for k, v in y.items():
        print("   %s %.2f" % (k, v))
    print("   均值: %.2f" % ym)
    print("\n★ 【志】（谁当家）: %.2f" % z)
    # ★ 诊断（照三哥四象限 + Arki 第三维）
    print()
    if qm >= 0.6 and ym < 0.6:
        s = "🔴 情高+欲低 = 危险（知道了却不动 = 等着出事）"
    elif qm >= 0.6 and ym >= 0.6 and z < 0.5:
        s = "🔴 情高+欲高+志弱 = 最危险（Arki 第三维）"
    elif qm >= 0.6:
        s = "🟡 情高（急躁/过度分析）"
    elif ym >= 0.8:
        s = "🟢 情低+欲高 = 冷静在干"
    else:
        s = "🟡 中间态"
    print("★ 诊断: %s" % s)
    out = {"ts": datetime.datetime.now(TZ).strftime("%F %T"), "七情": q, "六欲": y,
           "志": z, "情均": round(qm, 2), "欲均": round(ym, 2), "诊断": s}
    with open(f"{DATA}/qingyuzhi.jsonl", "a") as f:
        f.write(json.dumps(out, ensure_ascii=False) + "\n")
    print("★ 账: data/qingyuzhi.jsonl")


if __name__ == "__main__":
    main()
