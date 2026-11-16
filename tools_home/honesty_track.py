#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诚实闸效果追踪器（照董事长"自己跑几天试"）。

它做三件：
  ① 统计每天诚实闸拦了几次（从 send_msg 输出日志里数）
  ② 记录拦的理由（缺证据 / 报数字无源 / ...）
  ③ 输出日报：今天我说了多少次"好了"·被拦几次·通过几次

用法:
  python3 honesty_track.py            # 看今天
  python3 honesty_track.py --days 3   # 看近 3 天
产物: data/honesty_track.jsonl（每次被拦/通过都记一条）
"""
import json, os, re, sys, time, datetime

HOME = '/opt/masterd-wudi'
LOG_CANDIDATES = [
    HOME + '/data/send_msg.log',
    HOME + '/data/honesty.log',
]
TRACK = HOME + '/data/honesty_track.jsonl'


def scan_sendlog():
    """从 send_msg 的对外输出里找不到（它是 stdout）·改读 journald 不可行
    所以：直接调用 honesty_gate 对「最近发出去的文本」做复盘

    更可靠的做法：读 data/speech_log.jsonl（每条发出去的话都在）
    """
    out = []
    p = HOME + '/data/speech_log.jsonl'
    if not os.path.exists(p):
        return out
    try:
        lines = open(p, encoding='utf-8', errors='ignore').readlines()[-500:]
    except Exception:
        return out
    for l in lines:
        if not l.strip():
            continue
        try:
            d = json.loads(l)
        except Exception:
            continue
        ts = str(d.get('ts') or '')
        txt = str(d.get('说') or '')
        if not txt:
            continue
        out.append((ts, txt))
    return out


def check_with_gate(txt):
    """调 honesty_gate 判一次"""
    import subprocess
    try:
        r = subprocess.run(['python3', HOME + '/tools/honesty_gate.py', txt[:2000]],
                           cwd=HOME, capture_output=True, text=True, timeout=15)
        return r.returncode, (r.stdout or '').strip()
    except Exception as e:
        return -1, str(e)[:80]


def main():
    days = 1
    if '--days' in sys.argv:
        try:
            days = int(sys.argv[sys.argv.index('--days') + 1])
        except Exception:
            days = 1
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()[:10]

    rows = scan_sendlog()
    today = [r for r in rows if r[0][:10] >= cutoff]
    print("复盘窗口: 近 %d 天 | 检查条数: %d" % (days, len(today)))
    print()

    blocked, passed, noassert = 0, 0, 0
    reasons = {}
    records = []
    for ts, txt in today:
        code, why = check_with_gate(txt)
        rec = {"ts": ts, "code": code, "why": why[:120], "len": len(txt)}
        records.append(rec)
        if code == 1:
            blocked += 1
            key = why.split('\n')[1].strip() if '\n' in why else why[:50]
            reasons[key] = reasons.get(key, 0) + 1
        elif code == 0:
            if '无断言词' in why:
                noassert += 1
            else:
                passed += 1

    print("=== 结果 ===")
    print("  通过(带证据)      : %d" % passed)
    print("  🔴 应拦但已发出     : %d  ← 这些是'闸上线前'或'绕过闸'的" % blocked)
    print("  无断言(不适用)     : %d" % noassert)
    print()
    if reasons:
        print("=== 拦截理由统计 ===")
        for k, v in sorted(reasons.items(), key=lambda x: -x[1])[:6]:
            print("  %3d 次  %s" % (v, k))
        print()
    # 落盘
    try:
        with open(TRACK, 'a', encoding='utf-8') as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
        print("已记录到:", TRACK)
    except Exception as e:
        print("记录失败:", e)

    print()
    print("判据: «说了多少次'好了' != 真好了多少次｜被拦数 = 假绿数」")


if __name__ == '__main__':
    main()