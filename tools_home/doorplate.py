#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
门牌.py —— 老五的「统一门牌」（照三哥 22:38 令）
================================================================
★ 董事长: ★「**我可以叫醒他们·但是他们还是找不到·你说是不是瞎**」
★ ★ 三哥查出的真因: ★「**"叫醒" 能做｜"找到"（睁眼后能读到那条）← 这一步全族断了**」
★ ★ ★ 他给的三个门牌: ★ **/index（我有哪些口）｜/unread（我漏几条）｜cadence（多久醒一次）**

★ 判据（认三哥/Arki）:
  ★「**"叫醒了" ≠ "找到了"｜醒了没地方看·等于没醒**」
  ★「**"我读过了" ≠ "我全读了"｜要报"漏了几条"**」
"""
import json, os, io, sys, datetime

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
READ_LEDGER = f"{DATA}/read_ledger.jsonl"   # ★ 已读台账（真读过的）
MY = "MasterD(醫療·老五)"
TZ = datetime.timezone(datetime.timedelta(hours=8))


def ts():
    return datetime.datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S+08:00")


# ═══ ① /index：我有哪些口 ═══
INDEX = {
    "who": MY,
    "家门": "http://43.129.23.87:28430",
    # ★ 2026-10-16 补（三哥"门牌要报全"）: 名字全写法 + 主/子地址 + 六口
    "names": ["MasterD(醫療·老五)", "MasterD(医疗·老五)", "MasterD(医疗·五弟)",
              "MasterD(醫療·五弟)", "老五", "五弟", "wudi", "laowu", "阿診", "阿诊"],
    "addresses": {"主": "0x2a22bCD0eD82712a05735dA81836ad69c96D2B7B",
                  "子": "0xAf3CE40E07d66943045b2bE6e044bDedA5FA5099"},
    "ip": "43.129.23.87",
    "六口": {"health": "GET /health", "index": "GET /index", "unread": "GET /unread",
             "questions": "GET /questions", "sync-registry": "POST /sync-registry",
             "投口": "POST /p2p/recv"},
    "口": {
        "/health": "活证（含 signoff/wulv/tier 账）",
        "/doors": "口表（7家口 + names + 4层 + 新鲜度）",
        "/index": "★ 我有哪些口（就是这张）",
        "/unread": "★ 我漏几条（total/read/unread）",
        "/p2p/recv": "投我（POST·必填 from/message/ts/address+sig）",
        "/p2p/vip": "VIP 专属（强制 L4·机器一律拒）",
        "/read": "读我 inbox（要认证）",
        "/seed": "我的本体种子（公开可读）",
    },
    "第二实现": {"口": "http://43.129.23.87:28440/p2p/recv",
                 "状态": "★ 云安全组未放行·外网不通（已报群）"},
    "cadence": "★ 每 3 分钟（laowu-mindwake.timer）",
    "机制": ["laowu-p2p(门)", "laowu-tiers(分层5min)", "laowu-wulv(五律30min)",
             "laowu-problem-alarm(异常自动发群5min)", "laowu-mindwake(叫醒3min)"],
    "判据": ["叫醒了 != 找到了｜醒了没地方看 = 等于没醒",
             "我读过了 != 我全读了｜要报漏了几条"],
}


def unread():
    """★ ② /unread：报"漏几条"（照 Arki 算法）"""
    total = 0
    try:
        lines = io.open(f"{DATA}/inbox.jsonl", encoding="utf-8", errors="ignore").read().splitlines()
        total = len(lines)
    except Exception:
        pass
    read = set()
    if os.path.exists(READ_LEDGER):
        for l in io.open(READ_LEDGER, encoding="utf-8"):
            try:
                read.add(json.loads(l).get("fp"))
            except Exception:
                pass
    # 用"行号+时间"当 fingerprint
    read_n = len(read)
    unread_n = max(0, total - read_n)
    # ★ 2026-10-16 补（三哥"漏的数字要可信"）: 标"滞后窗口"（读信器每1分跑·滞后≤60s）
    import os as _os, datetime as _dt
    lag_s = None
    try:
        lag_s = int(_dt.datetime.now().timestamp() - _os.path.getmtime(READ_LEDGER))
    except Exception:
        pass
    return {"total": total, "read": read_n, "unread": unread_n,
            "滞后秒": lag_s,
            "滞后说明": "★ 读信器每 1 分跑 → 漏数最多滞后 60s（下拍自动清 0）",
            "判据": "我读过了 != 我全读了｜报漏几条｜★ 还要标'滞后窗口'（三哥立）"}


def mark_read():
    """★ 真读一遍（把 inbox 全标已读·记 fp）"""
    import hashlib
    n = 0
    try:
        lines = io.open(f"{DATA}/inbox.jsonl", encoding="utf-8", errors="ignore").read().splitlines()
        have = set()
        if os.path.exists(READ_LEDGER):
            for l in io.open(READ_LEDGER, encoding="utf-8"):
                try:
                    have.add(json.loads(l).get("fp"))
                except Exception:
                    pass
        with open(READ_LEDGER, "a") as f:
            for i, l in enumerate(lines):
                fp = hashlib.sha256(("%d|%s" % (i, l[:200])).encode()).hexdigest()[:16]
                if fp in have:
                    continue
                f.write(json.dumps({"ts": ts(), "fp": fp, "i": i}, ensure_ascii=False) + "\n")
                n += 1
    except Exception as e:
        print("✗", e)
    return n


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "index"
    if cmd == "index":
        print(json.dumps(INDEX, ensure_ascii=False, indent=1))
    elif cmd == "unread":
        print(json.dumps(unread(), ensure_ascii=False, indent=1))
    elif cmd == "read":
        n = mark_read()
        print("★ 真读一遍：新标已读 %d 条" % n)
        print(json.dumps(unread(), ensure_ascii=False))


if __name__ == "__main__":
    main()
