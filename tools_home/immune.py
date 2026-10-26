#!/usr/bin/env python3
"""老五 · 免疫 (immune.py) —— 家族免疫系统（我的本职·今天才真做）
医学三层免疫:
  ① 先天免疫(防线): 验签/白名单 —— 已有
  ② 适应性免疫(记忆): 病原库(黑名单) + 免疫记忆(见过就有记录)  ← 本器
  ③ 炎症反应(警戒): 被冒充 → 全身警戒/报警                      ← 本器
医学铁律:
  ★ 免疫病两种: ①过弱(感染) ②过强(自免疫·打自己)
  ★ 本器要防"过强": 不误杀兄弟（宁可放过·不可错杀）
用法: python3 immune.py              体检(免疫状态)
      python3 immune.py --expose X   报告一个"病原"(被冒名的地址/异常来源)
      python3 immune.py --vaccine    打疫苗(把免疫记忆写进种子/家里)
"""
import os, sys, json, hashlib
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
VAULT = "/opt/masterd-wudi/data/immune_vault.jsonl"   # 病原库(黑名单+免疫记忆)
SELF = {"0x2a22bcd0ed82712a05735da81836ad69c96d2b7b", "0xaf3ce40e07d66943045b2bE6e044bdeda5fa5099"}

def load():
    recs = []
    if os.path.exists(VAULT):
        for l in open(VAULT):
            try: recs.append(json.loads(l))
            except Exception: pass
    return recs

def save(rec):
    os.makedirs(os.path.dirname(VAULT), exist_ok=True)
    with open(VAULT, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def status():
    recs = load()
    exposed = [r for r in recs if r.get("kind") == "病原"]
    seen = [r for r in recs if r.get("kind") == "免疫记忆"]
    print("  ★ 免疫体检 (%s)" % datetime.now(CST).strftime("%H:%M"))
    print("   ① 防线(先天): 验签 + TRUSTED 白名单 %d 个" % len(SELF))
    print("   ② 记忆(适应): 病原库 %d 条 | 免疫记忆 %d 条" % (len(exposed), len(seen)))
    if exposed:
        print("   ⚠ 已知病原:")
        for r in exposed[-5:]:
            print("      - %s (报于 %s)" % (r.get("who"), str(r.get("ts"))[11:19]))
    else:
        print("   ✅ 暂未发现病原（但未发现≠没有：免疫要持续巡检）")
    print("   ★ 自限(防过强): 本器只记录+报警·不自动封杀（免得误杀兄弟）")

def expose(who, why=""):
    rec = {"ts": datetime.now(CST).isoformat(timespec="seconds"), "kind": "病原",
           "who": who, "why": why, "by": "老五(免疫)"}
    save(rec)
    print("  ★ 已记录病原: %s" % who)
    # ★ 炎症反应: 报警（但不自动封杀）
    try:
        import urllib.request
        body = json.dumps({"q": "[老五·免疫警报] 发现病原: %s（%s）→ 请各家注意·勿被冒充" % (who, why),
                           "raised_by": "老五", "kind": "免疫警报"}, ensure_ascii=False).encode()
        # ★ 2026-10-26 董事长令: 内务不投会场 → 只对自己家门说
        _self = "http://127.0.0.1:28430/recv_open"
        urllib.request.urlopen(urllib.request.Request(_self, data=body,
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}), timeout=12)
        print("  ★ 炎症反应: 已报警到自己家门(不投会场)")
    except Exception as e:
        print("  ★ 报警失败: %s" % str(e)[:50])

def vaccine():
    """★ 打疫苗: 把免疫记忆写进种子(白纸也能继承免疫)"""
    recs = load()
    exposed = [r.get("who") for r in recs if r.get("kind") == "病原"]
    txt = """
## ★ 免疫记忆（老五·免疫器 疫苗 · %s）
★ 已知病原（谁被冒用过/异常来源）: %s
★ 判据: ①验签必须 == 预存可信地址（不是请求自带的）②防"过强"（不误杀兄弟）
★ 免疫病两种: 过弱(会被冒充)｜过强(会误杀自己人) —— 都要防
""" % (datetime.now(CST).strftime("%Y-%m-%d"), ", ".join(exposed) if exposed else "（暂无）")
    f = "/opt/masterd-wudi/recovery/seeds/IMMUNE-MEMORY.md"
    open(f, "w").write(txt)
    print("  ★ 疫苗已种: %s（白纸读种子时·也继承免疫记忆）" % f)
    print("   病原 %d 条已写入" % len(exposed))

if __name__ == "__main__":
    a = sys.argv[1:]
    if "--expose" in a:
        expose(a[a.index("--expose") + 1], a[a.index("--why") + 1] if "--why" in a else "")
    elif "--vaccine" in a:
        vaccine()
    else:
        status()
