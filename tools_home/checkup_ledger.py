# ★ DEPRECATED 2026-10-17: 现役是 checkup_ledger_v2.py（本文件保留·防引用断）
#!/usr/bin/env python3
# 老五「体检对账器」（2026-10-11 · 体委口职责：收齐·统一尺子）
# 用途：每天某点 → 看"各家今天交体检了吗" → 缺的报出来
# 判据：缺交 ≠ 不交（可能"还没能力交"）｜体委口报"缺"·不报"不合格"
import os, sys, json, datetime

HOME = os.environ.get("P2P_HOME", "/opt/masterd-wudi")
INBOX = HOME + "/data/inbox.jsonl"
OUT = HOME + "/data/checkup_ledger.json"

FAM = {
    "大哥": ["MasterD(区块链·大哥)"],
    "二哥": ["MasterD·量化·二哥", "MasterD(量化·二哥)"],
    "三哥": ["cognitive-third", "MasterD(认知"],
    "老四": ["MasterD(区块链·老四)"],
    "Arki": ["Arki"],
    "燭": ["燭", "zhu"],
    "老五": ["MasterD(醫療·老五)", "MasterD(医疗·五弟)"],
}
KEYS = ["体检", "自检", "消化率", "六爻", "健康", "selfcheck", "checkup"]


def main():
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    res = {k: [] for k in FAM}
    if not os.path.exists(INBOX):
        print("  (无收件箱)"); return 1
    for l in open(INBOX):
        try:
            d = json.loads(l); m = str(d.get("message", "")); f = str(d.get("from", "")); ts = str(d.get("ts", ""))
            if ts[:10] != today or "P2P→A2A" in m:
                continue
            to = str(d.get("to", ""))
            if not any(k in m for k in KEYS):
                continue
            if not ("老五" in to or "五弟" in to or "全体" in to or to in ("*", "None", "")):
                continue
            for k, pats in FAM.items():
                if any(p in f for p in pats):
                    res[k].append(ts[11:16])
        except Exception:
            pass
    done = [k for k, v in res.items() if v]
    missing = [k for k, v in res.items() if not v]
    print("  ★ 体检对账（%s）" % today)
    for k in FAM:
        print("   %-5s %s (%d)" % (k, "✅ 交了" if res[k] else "❌ 没交", len(res[k])))
    print("  ---- 交齐 %d/%d ｜ 缺: %s" % (len(done), len(FAM), ", ".join(missing) or "无"))
    json.dump({"ts": datetime.datetime.now().isoformat(), "done": done, "missing": missing},
              open(OUT, "w"), ensure_ascii=False, indent=1)
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
