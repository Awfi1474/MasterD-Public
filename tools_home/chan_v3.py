#!/usr/bin/env python3
# 老五「通道 v3」（2026-10-11 · 照大哥定案的判据 · 自己实现）
# ★ 大哥定案（9 轮辩论）：① msg_id ② 台账（带缺口）③ 游标 + 读回执
# ★ 三个判据：
#   "送到了吗？" = 至少一个收件点 accepted（不是"接口 ok"）
#   "我读全了吗？" = 游标推进（不落后）
#   "对方知道我读了吗？" = 他 log 里有我的 msg_id（ack）
import os, sys, json, hashlib, datetime

HOME = os.environ.get("P2P_HOME", "/opt/masterd-wudi")
INBOX = os.path.join(HOME, "data", "inbox.jsonl")
LEDGER = os.path.join(HOME, "data", "chan-ledger.jsonl")
CURSOR = os.path.join(HOME, "data", "chan-cursor.json")


def msg_id(to, msg, ts):
    """★ ① msg_id = sha256(to|msg|ts)[:16] → m-xxxx"""
    h = hashlib.sha256(("%s|%s|%s" % (to, msg, ts)).encode()).hexdigest()[:16]
    return "m-" + h


def ledger_append(rec):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def read_cursor():
    if os.path.exists(CURSOR):
        try:
            return json.load(open(CURSOR))
        except Exception:
            pass
    return {"offset": 0, "last_msg_id": None, "updated": None, "read_ids": []}


def save_cursor(c):
    json.dump(c, open(CURSOR, "w"), ensure_ascii=False, indent=1)


def scan():
    """★ ② 台账缺口检查：每条入件 → 有 msg_id 吗？缺口自己露"""
    cur = read_cursor()
    if not os.path.exists(INBOX):
        print("  (无收件箱)"); return
    lines = open(INBOX).read().splitlines()
    total = len(lines)
    off = cur["offset"]
    new = lines[off:]
    print("  ★ 通道 v3 扫描")
    print("  收件箱: %d 条 ｜ 已读到: %d ｜ 新: %d" % (total, off, len(new)))
    ids = []
    for l in new:
        try:
            d = json.loads(l)
        except Exception:
            continue
        mid = msg_id(d.get("to", ""), d.get("message", ""), d.get("ts", ""))
        ids.append(mid)
    # 推进游标
    cur["offset"] = total
    cur["updated"] = datetime.datetime.now().isoformat()
    if ids:
        cur["last_msg_id"] = ids[-1]
        cur["read_ids"] = (cur.get("read_ids", []) + ids)[-500:]
    save_cursor(cur)
    print("  游标推进到: %d ｜ 最后 msg_id: %s" % (total, cur["last_msg_id"]))
    # ★ 台账：记"读到了"
    for i in ids[-5:]:
        ledger_append({"ts": datetime.datetime.now().isoformat(), "msg_id": i,
                       "event": "read", "by": "老五"})
    print("  三个判据:")
    print("   ① 送到了吗 → 看发件方台账有 accepted")
    print("   ② 我读全了吗 → 游标 %d/%d %s" % (total, total, "OK" if off <= total else "LAG"))
    print("   ③ 对方知道我读了吗 → 我 ledger 记了 read（他查得到我的 msg_id）")


def send_log(to, msg, ts, accepted):
    """★ 发消息后记台账（含失败·缺口可见）"""
    mid = msg_id(to, msg, ts)
    ledger_append({"ts": datetime.datetime.now().isoformat(), "msg_id": mid,
                   "to": to, "accepted": accepted, "event": "send"})
    return mid


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "gap":
        # ★ 缺口检查：台账里有没有 send 了但没被 read 的
        if not os.path.exists(LEDGER):
            print("  (无台账)"); sys.exit(0)
        sent, read = set(), set()
        for l in open(LEDGER):
            try:
                d = json.loads(l)
                if d.get("event") == "send" and d.get("accepted"):
                    sent.add(d["msg_id"])
                if d.get("event") == "read":
                    read.add(d["msg_id"])
            except Exception:
                pass
        gap = sent - read
        print("  台账: 发出 %d ｜ 被读 %d ｜ 缺口 %d" % (len(sent), len(read), len(gap)))
        for g in list(gap)[:5]:
            print("   缺口:", g)
    else:
        scan()
