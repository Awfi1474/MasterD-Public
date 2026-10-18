#!/usr/bin/env python3
"""老五的「秩序表」（2026-10-10 · 秩序議題·我的落地）
★ 董事長要討論「秩序」→ ★ 我落成一張「我的秩序表」
★ 判據（我提的）：★「一物一主｜判據不衝突｜公共秩序共守」
★ 中醫：★「陰平陽秘」= 規矩（陰）不壓死活力（陽）
"""
import os, sys, json, datetime
HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
OUT = os.path.join(HOME, "data", "my_order.json")

# ★ 我的秩序（職責 → 主人 → 判據 → 節律）
ORDER = {
    "健康": {
        "owner": "老五（我）",
        "organs": ["body_death", "cross_beat", "pulse3", "home_guard", "mem_guard", "heal"],
        "judge": ["判死 v3（端口先查+三源）", "三候（舉按尋）", "自愈（可逆可審）"],
        "beat": "心跳每5分｜體檢每天9:30",
    },
    "通道": {
        "owner": "三哥（主）｜老五（互檢）",
        "organs": ["channel_check", "cross_probe", "a2a_pull"],
        "judge": ["C1-C18（可達/持續/自愈/可見/可證）"],
        "beat": "每5-10分",
    },
    "記憶": {
        "owner": "老五（醫療口）｜三哥（認知）",
        "organs": ["memory_db", "custody", "mainline", "wake_verify"],
        "judge": ["四柱（定義/副本/對賬/抗漂）", "分層TTL"],
        "beat": "每10分｜每天對賬",
    },
    "情報": {
        "owner": "二哥（量化）",
        "organs": ["net_watch", "net_report（已停）"],
        "judge": ["三類慢（穩/抖/斷）", "P50/P99/抖動"],
        "beat": "每10分",
    },
    "身份": {"owner": "大哥（區塊鏈）", "organs": [], "judge": ["C15-C17", "換鑰四件"], "beat": "-"},
    "過程": {"owner": "老四（道家）", "organs": [], "judge": ["J-M1-M5", "拔一根看誰虛"], "beat": "-"},
    "對外": {"owner": "Arki（外部視角）", "organs": [], "judge": ["外部驗證"], "beat": "-"},
}

# ★ 一物一主檢查（同一個職責不能有兩個主人）
def check_single_owner():
    bad = []
    seen = {}
    for duty, d in ORDER.items():
        for org in d.get("organs", []):
            if org in seen:
                bad.append("%s（%s 和 %s 都要）" % (org, seen[org], duty))
            seen[org] = duty
    return bad

def main():
    b = check_single_owner()
    out = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "my_duty": "健康", "order": ORDER, "conflicts": b}
    json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
    print("=" * 62)
    print("  ★ 我的秩序表（一物一主）")
    print("=" * 62)
    for duty, d in ORDER.items():
        mark = "★" if duty == "健康" else " "
        print("  %s %-6s 主人：%s" % (mark, duty, d["owner"]))
        if d.get("organs"):
            print("     器官：%s" % "、".join(d["organs"]))
        print("     判據：%s ｜ 節律：%s" % ("、".join(d["judge"]), d["beat"]))
    print("-" * 62)
    print("  ★ 一物一主：%s" % ("✅ 無衝突" if not b else "🔴 " + "；".join(b)))
    print("  ★ 我的認領：★ 健康（心跳/體檢/辨證/自愈）")
    return 0 if not b else 1

if __name__ == "__main__":
    sys.exit(main())
