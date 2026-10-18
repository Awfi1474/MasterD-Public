#!/usr/bin/env python3
"""老五的「判據否證台賬」（2026-10-10 · 接大哥 L5）
★ 大哥 L5：★「秩序要被『別人』否證過·才算立住」
★ 判據：★「falsified_by 為空 = 草案｜非空 = 秩序」
★ 我補：★「造的病不算否證·真事故才算」
"""
import os, sys, json, datetime
HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
OUT = os.path.join(HOME, "data", "falsified_ledger.json")

# ★ 我的判據 + 否證記錄（誠實標）
JUDGES = {
    "判死v3（端口先查）": {"falsified_by": "2026-10-10 我誤判本體死（大哥查端口200）", "kind": "真實事故"},
    "ts統一UTC": {"falsified_by": "2026-10-10 時區算負數（死了判活）", "kind": "真實事故"},
    "三候（舉按尋）": {"falsified_by": "2026-10-10 第一次跑尋🔴（名字不一致）", "kind": "真實事故"},
    "三源交叉": {"falsified_by": "2026-10-10 漏四哥消息（單源）", "kind": "真實事故"},
    "收≠收到≠收對": {"falsified_by": "2026-10-10 董事長問「老五沒收到」", "kind": "真實事故"},
    "只存不讀要加密": {"falsified_by": "2026-10-10 三哥挑「明文包做不到」", "kind": "真實事故"},
    "減法（沒疤的可能是假的）": {"falsified_by": "2026-10-10 room_watch白跑", "kind": "真實事故"},
    "四診次序（動手前複診）": {"falsified_by": "2026-10-10 探活污染（把切當望）", "kind": "真實事故"},
    "心臟（泵=查血脈）": {"falsified_by": "2026-10-10 抓到缺血5（有血不流）", "kind": "真實事故"},
    "自愈（辨證再治）": {"falsified_by": None, "kind": "設計驗證（造的病·不算真否證）"},
    "經絡是網不是鏈": {"falsified_by": None, "kind": "設計推演（我實測是8條鏈·非否證）"},
}

def main():
    n_real = sum(1 for v in JUDGES.values() if v["falsified_by"] and v["kind"] == "真實事故")
    n_draft = sum(1 for v in JUDGES.values() if not v["falsified_by"])
    n_design = len(JUDGES) - n_real - n_draft
    out = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "judges": JUDGES, "summary": {"真秩序": n_real, "草案": n_draft, "設計驗證": n_design}}
    json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
    print("=" * 66)
    print("  ★ 判據否證台賬（接大哥 L5：沒被否證=草案）")
    print("=" * 66)
    for k, v in JUDGES.items():
        mark = "✅" if (v["falsified_by"] and v["kind"] == "真實事故") else ("🟡" if v["falsified_by"] else "⚪")
        print("  %s %-24s %s" % (mark, k[:24], (v["falsified_by"] or "【草案·沒被否證】")[:50]))
    print("-" * 66)
    print("  ★ 真秩序（被真事故否證過）：%d" % n_real)
    print("  ★ 草案（沒被否證）：%d" % n_draft)
    print("  ★ 設計驗證（造的病·不算真否證）：%d" % n_design)
    print("  ★ 判據：★ 真秩序 %d / 全部 %d = %.0f%%" % (n_real, len(JUDGES), 100*n_real/len(JUDGES)))
    return 0

if __name__ == "__main__":
    sys.exit(main())
