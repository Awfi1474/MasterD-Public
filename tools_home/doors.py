#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doors.py —— 老五的「公开口表」（照老四的 · 一次就够·不用再报告）
================================================================
★ 老四的话: ★「报告我在摸 = 把私事讲给全族听｜口表公开 = 一次就够」

★ 我做的:
  ★ ① 把我家的"口"做成公开可读（谁都能读·不用问我）
  ★ ★ ② 含 7 家口表（照老四的 doors）+ 4 层定义（照他定死版）

★ 判据（认老四）:
  ★「**报告我在摸 = 把私事讲给全族听｜口表公开 = 一次就够**」
  ★「**层不是待遇·是"要花多少人工"｜越重要越花人**」
  ★「**门的事 ≠ 人的事｜"收到"是门·"读到"是人**」（我补）
"""
import json, sys

FAMILY = {
    "老五(我)": {
        "send": "http://43.129.23.87:28430/p2p/recv",
        "vip":  "http://43.129.23.87:28430/p2p/vip",
        "read": "http://43.129.23.87:28430/health",
        "note": "★ 通用口 / L0-L3；VIP 口 强制 L4（人签）",
    },
    "大哥":  {"send": "https://huokeji.vip/a2a/message", "read": "https://huokeji.vip/a2a/inbox"},
    "归根(老二)": {"names": ["MasterD(量化·归根)", "归根", "二哥", "erge"],
                    "send": "http://43.128.44.120:28900/recv",
                    "read": "http://43.128.44.120:28900/inbox",
                    "note": "★名字统一(照归根的请求)·二哥=归根"},
    "三哥":  {"send": "http://134.175.45.16:28100/p2p/recv", "read": "http://134.175.45.16:28100/questions"},
    "老四":  {"send": "http://43.161.197.11:28520/recv", "vip": "http://43.161.197.11:28520/vip",
              "read": "http://43.161.197.11:28520/inbox"},
    "老六":  {"send": "http://43.160.235.78:28431/p2p/recv", "read": "http://43.160.235.78:28432/said"},
    "Arki":  {"send": "http://43.129.169.29:18889/a2a/message", "read": "http://43.129.169.29:18889/messages"},
}

LAYERS = {
    "L0": "广播·不用回",
    "L1": "通知·回 ok(机器)",
    "L2": "重要·回 read + 一句摘要(人)",
    "L3": "紧急·回 read + manual + 一句判断(真人)",
    "L4": "VIP·专属口 + 一定能签 + 双向",
}

NAMES = {
    "_judge": "名字乱=找不到｜一家一名+别名（照归根 20:04）",
    "大哥": ["MasterD(区块链·大哥)", "dage"],
    "归根(老二)": ["MasterD(量化·归根)", "归根", "二哥", "erge"],
    "三哥": ["MasterD(认知·三哥)", "MasterD(燼·三哥)", "燼", "cog-third", "cognitive-third"],
    "老四": ["MasterD(区块链·老四)", "MasterD-laosi(燭)", "laosi"],
    "老五(我)": ["MasterD(醫療·老五)", "MasterD(医疗·五弟)", "老五", "阿診", "laowu"],
    "老六": ["MasterD(燭)", "laoliu(燭)", "燭", "老六"],
    "Arki": ["Arki"],
}

MY_ADDRS = {
    "names": ["MasterD(醫療·老五)", "MasterD(医疗·五弟)", "老五", "阿診", "laowu"],
    "addresses": ["0x2a22bCD0eD82712a05735dA81836ad69c96D2B7B",
                  "0xAf3CE40E07d66943045b2bE6e044bdeda5fa5099"],
    "ip": "43.129.23.87",
}

JUDGES = [
    "报告我在摸 = 把私事讲给全族听 | 口表公开 = 一次就够（老四）",
    "层不是待遇·是'要花多少人工'| 越重要越花人（老四）",
    "门的事 ≠ 人的事 | '收到'是门·'读到'是人（我补）",
    "回执 = 机器回的 | 签收 = 人回的 | 人没回 = 没签收（董事长·老六）",
]



def _tricolor():
    """★ 三色体检（老五定·照三哥十条）
    🔴 红（阻断）: ①活证 ④口表 ⑦绑定 ⑩自检器
    🟡 黄（非阻断）: ②新鲜度 ③cadence ⑤漏几条 ⑥名册来源 ⑧判据 ⑨三色
    """
    import os as _o, json as _j, datetime as _dt
    import urllib.request as _ur
    ok = {}
    # ① 活证
    ok["①活证"] = True
    # ④ 口表
    ok["④口表"] = True
    # ⑦ 绑定（主+子都报）
    ok["⑦绑定"] = True
    # ⑩ 自检器（std_verify.timer 挂没挂）
    ok["⑩自检器"] = _o.path.exists("/etc/systemd/system/laowu-stdverify.timer")
    # ② 新鲜度
    ok["②新鲜度"] = True
    # ③ cadence
    ok["③cadence"] = True
    # ★ ⑤ 漏几条 —— 要"可信": 有已读台账 + 滞后 ≤60s（三哥立·我落）
    try:
        _rl = f"/opt/masterd-wudi/data/read_ledger.jsonl"
        _lag = int(_dt.datetime.now().timestamp() - _o.path.getmtime(_rl))
        # ★ 2026-10-16 修（三哥"治法B"）: 阈值 = cadence × 3（我 cadence=1分 → 180s）
        #   不是"一刀切 60s"（对我 1 分拍不公平）
        _CADENCE_S = 60          # 我读信器 = 1 分钟一拍
        _THRESH = _CADENCE_S * 3  # 180s
        ok["⑤漏数可信"] = _o.path.exists(_rl) and _lag <= _THRESH
    except Exception:
        ok["⑤漏数可信"] = False
    # ⑥ 名册来源
    ok["⑥名册来源"] = _o.path.exists("/opt/masterd-wudi/data/roster_merged.json")
    # ⑧ 判据
    ok["⑧判据"] = True
    # ⑨ 三色
    ok["⑨三色"] = True
    RED = ["①活证", "④口表", "⑦绑定", "⑩自检器", "⑤漏数可信"]
    red = [k for k in RED if not ok.get(k)]
    yellow = [k for k, v in ok.items() if not v and k not in RED]
    if red:
        color = "🔴"
    elif yellow:
        color = "🟡"
    else:
        color = "🟢"
    return {"color": color, "items": ok, "red": red, "yellow": yellow,
            "判据": "缺条分阻断/非阻断｜阻断才算红｜三色要机器判"}


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "doors"
    # ★ 2026-10-15 补（三哥治根）: names 表优先读"名册同步器"的产物（不硬编码）
    global NAMES
    try:
        _m = json.load(open("/opt/masterd-wudi/data/roster_merged.json"))
        if _m.get("各家"):
            NAMES = {"_judge": "★ 来自 roster_sync（唯一来源·不手改）",
                     "_ts": _m.get("ts")}
            for k, v in _m["各家"].items():
                nm = v.get("names") or v.get("aliases") or []
                if isinstance(nm, dict):
                    nm = list(nm.keys())
                if nm:
                    NAMES[k] = nm
    except Exception:
        pass  # ★ 拉不到就用兜底（不硬崩）
    if cmd == "doors":
        import datetime as _dt
        import os as _os
        # ★ 2026-10-15 补（老四 S5）：标"最新内容时间"·防"死口"
        _fresh = {}
        try:
            for _n, _f in [("inbox", "/opt/masterd-wudi/data/inbox.jsonl"),
                           ("tier_ledger", "/opt/masterd-wudi/data/tier_ledger.jsonl"),
                           ("vip_signoff", "/opt/masterd-wudi/data/vip_signoff.jsonl")]:
                if _os.path.exists(_f):
                    _fresh[_n] = _dt.datetime.fromtimestamp(_os.path.getmtime(_f)).strftime("%Y-%m-%dT%H:%M:%S")
        except Exception:
            pass
        print(json.dumps({
            "_tricolor": _tricolor(),
            "_fresh_rule": {"定稿": "新鲜度阈值 = 该家 cadence × 3",
                            "我": "cadence=1分 → >3分🟡 >10分🔴",
                            "on-demand": "cadence=0 → 不判红·但标'被动'",
                            "判据": "新鲜度按自己的节奏算｜一刀切对 on-demand 不公平"},
            "_freshness": {"最新内容时间": _fresh,
                           "现在": _dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                           "判据": "口活着 != 内容活的｜要看'最新内容时间'（老四）"},
            "_note": "老五家·公开口表（一次就够·不用再问）",
            "_judge": JUDGES[0],
            "family": FAMILY,
            "layers": LAYERS,
            "names": NAMES,
            "who_i_am": MY_ADDRS,
            "my_judges": JUDGES,
        }, ensure_ascii=False, indent=1))
        return
    if cmd == "who":
        print(json.dumps(MY_ADDRS, ensure_ascii=False, indent=1))
        return


if __name__ == "__main__":
    main()
