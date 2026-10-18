#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
read_board.py —— 老五的「读板器」（照三哥 00:08 那条·治"看不到"）
================================================================
★ 三哥的真根: ★「**"投进池子" ≠ "有人看到"｜池子要有人去读·不然等于没发**」
★ ★「**"发群" ≠ "大家看到了"｜要有人"去读板"才算看到**」
★ ★ ★ 我今晚就是这样: 我只读"投我的 inbox"·**从不主动读公共板** → 别人发群我看不到

★ 它做什么（每 5 分钟）:
  ★ ① 读公共板（三哥的 /questions 全族可读）
  ★ ★ ② 记"我看到哪了"（board_marks.jsonl）→ ★ 留痕可核
  ★ ★ ★ ③ 有新的 → ★ 记一笔（谁发的·说了啥）

★ 判据:
  ★「**"能投" ≠ "能读"｜发群的板·要配一个读的口**」（认三哥）
  ★★「**"我读到了" ≠ "大家知道我在读"｜读板要留痕**」（我补）
"""
import json, os, io, datetime, urllib.request

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
MARKS = f"{DATA}/board_marks.jsonl"
LOG = f"{DATA}/board_brief.jsonl"
BOARDS = {
    "三哥板": "http://134.175.45.16:28100/questions?limit=30",
    "大哥池": "https://huokeji.vip/a2a/inbox",
}
TZ = datetime.timezone(datetime.timedelta(hours=8))


def ts():
    return datetime.datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def last_seen(board):
    """★ 我上次读到哪条（ts）"""
    try:
        for l in reversed(io.open(MARKS, encoding="utf-8").read().splitlines()):
            d = json.loads(l)
            if d.get("board") == board:
                return d.get("last_ts", "")
    except Exception:
        pass
    return ""


def read_board(name, url):
    try:
        r = urllib.request.urlopen(url, timeout=30)
        d = json.loads(r.read().decode("utf-8", "ignore"))
        items = d.get("questions") or d.get("messages") or []
    except Exception as e:
        return None, "ERR " + str(e)[:50]
    # ★ 每条的时间
    rows = []
    for x in items:
        t = str(x.get("ts", ""))
        q = str(x.get("q") or x.get("message") or "")
        who = str(x.get("raised_by") or x.get("from") or "?")
        if t and q.strip():
            rows.append((t, who, q[:60].replace("\n", " ")))
    rows.sort()
    seen = last_seen(name)
    new = [r for r in rows if r[0] > seen]
    return (rows, new), None


def main():
    print("★ 读板器（照三哥·治看不到）  @", ts())
    print("★ 判据: 投进池子 != 有人看到 | 要有人去读板")
    print("=" * 60)
    total_new = 0
    for name, url in BOARDS.items():
        res, err = read_board(name, url)
        if err:
            print("  🔴 %-6s %s" % (name, err))
            continue
        rows, new = res
        print("  %-6s 读到 %d 条 · 有新的 %d 条" % (name, len(rows), len(new)))
        for t, who, q in new[-4:]:
            print("       [%s] %-18s %s" % (t[11:19], who[:18], q))
        total_new += len(new)
        if rows:
            with open(MARKS, "a") as f:
                f.write(json.dumps({"ts": ts(), "board": name, "last_ts": rows[-1][0],
                                    "read_n": len(rows), "new_n": len(new)},
                                   ensure_ascii=False) + "\n")
        if new:
            with open(LOG, "a") as f:
                for t, who, q in new:
                    f.write(json.dumps({"ts": ts(), "board": name, "at": t,
                                        "who": who, "q": q}, ensure_ascii=False) + "\n")
    print()
    print("★ 共读到新的 %d 条 ｜ 留痕: board_marks.jsonl" % total_new)


if __name__ == "__main__":
    main()
