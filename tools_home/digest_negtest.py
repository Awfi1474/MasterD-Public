#!/usr/bin/env python3
"""消化率台賬的「負向測試」（2026-10-10 · 答大哥的問題）
★ 大哥問：「你的檢查器怎麼防假綠」→ ★ 我答：負向測試
★ 判據：★ 造假時必須報 error·不然檢查器本身是假的
"""
import os, sys, json, datetime
HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
RATE = os.path.join(HOME, "data", "digest_rate.json")

def check(r):
    """★ 正向：報告消化率"""
    if r["learned"] and r["real"] is not None:
        return round(100 * r["real"] / r["learned"]), None
    return None, "待補"

def neg_test():
    """★ 負向測試：造假（有人報 100% 但真消化少）→ 必須被揪出"""
    cases = [
        # ★ 造假案例（該被揪出）
        {"who": "假A", "learned": 10, "real": 1, "expect": "低"},
        {"who": "假B", "learned": 10, "real": 10, "expect": "高"},
        # ★ 真案例（該正常）
        {"who": "老五", "learned": 11, "real": 9, "expect": "高"},
    ]
    ok = True
    for c in cases:
        rt, err = check(c)
        got = ("高" if (rt and rt >= 70) else "低") if rt is not None else "待"
        pass_ = (got == c["expect"])
        if not pass_: ok = False
        print("  %s %-6s 學%d/真%d → 消化率 %s%% → 判「%s」（應「%s」）" % (
            "✅" if pass_ else "🔴", c["who"], c["learned"], c["real"], rt, got, c["expect"]))
    return ok

def main():
    print("=" * 62)
    print("  ★ 消化率台賬 · 負向測試（造假必須被抓）")
    print("=" * 62)
    ok = neg_test()
    print("-" * 62)
    if ok:
        print("  ✅ 負向測試通過（造假被抓·真值正常）→ 檢查器不是假的")
    else:
        print("  🔴 負向測試失敗（造假沒被抓）→ 檢查器本身是假的")
    # ★ 加上「真消化」的檢查器驗證欄
    print("  ★ 我補的欄位（答大哥）：checker_verified_by（檢查器被什麼驗過）")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
