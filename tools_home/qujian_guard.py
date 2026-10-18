#!/usr/bin/env python3
# 老五「取件守卫」：兄弟取走片后 → 自动删我家的片（物理分离）
# 判据：片要在"别人家"·不在"我家"｜我只在"传递中"短暂持有
import os, json, datetime

HOME = "/opt/masterd-wudi"
SHARES = [
    ("dage", "peers/dage/laowu-share1.b64", "大哥"),
    ("erge", "peers/erge/laowu-share2.b64", "二哥"),
]
RECEIPT = os.path.join(HOME, "data", "share_pickup.json")


def load():
    return json.load(open(RECEIPT)) if os.path.exists(RECEIPT) else {"picked": {}}


def main():
    d = load()
    for key, path, who in SHARES:
        full = os.path.join(HOME, path)
        if d["picked"].get(key) and os.path.exists(full):
            os.remove(full)
            print("  OK 已删我家的片（%s 已取走·%s）" % (who, path))
    print("  状态：", json.dumps(d.get("picked", {}), ensure_ascii=False))


def mark_picked(key, by):
    # ★ 2026-10-11 修：必須 by 是人（非模拟）·且 key 有效
    if by in ("?", "模拟", "test") or not by:
        print("  ✗ 拒絕：by 必須是真人（不是'%s'）" % by); return
    if key not in [s[0] for s in SHARES]:
        print("  ✗ 拒絕：key '%s' 不在清單" % key); return
    d = load()
    d["picked"][key] = {"by": by, "ts": datetime.datetime.now().isoformat()}
    json.dump(d, open(RECEIPT, "w"), ensure_ascii=False, indent=1)
    print("  记：%s 已取走（%s）" % (key, by))


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3 and sys.argv[1] == "picked":
        mark_picked(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "?")
    main()
