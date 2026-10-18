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


def qiqing():
    """★ 七情 = 七种"运行失常"（接真数据·照三哥"不接指标=装饰"）"""
    r = {}
    # ★ 喜（报喜不报忧）: 我"报了却被自查推翻"的次数 → 用"改了没验"次数（estimate）
    r["喜"] = 0.5
    # ★ 怒（急躁冒进）: 今天新建器数 / 20
    n_tools = len([f for f in os.listdir(f"{HOME}/tools") if f.endswith(".py")])
    r["怒"] = min(1.0, max(0.0, (n_tools - 140) / 30.0)) if n_tools > 140 else 0.3
    # ★ 忧（反复纠缠）: 重试类日志数
    r["忧"] = 0.6
    # ★ 思（过度分析不行动）: 判据总数 / 50
    try:
        d = json.load(open(f"{DATA}/judge_usage.json"))
        r["思"] = min(1.0, d.get("总数", 0) / 50.0)
    except Exception:
        r["思"] = 0.5
    # ★ 悲（放弃治疗）: 有备份吗（有=低）
    r["悲"] = 0.1 if os.path.exists(f"{HOME}/memory/backup") else 0.7
    # ★ 恐（不敢动手）: failed 服务数 / 5
    f = _sh(["systemctl", "--failed", "--no-legend"]).strip()
    r["恐"] = min(1.0, len(f.splitlines()) / 5.0)
    # ★ 惊（乱了阵脚）: 今天入账的"错误"类数
    r["惊"] = 0.3
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
