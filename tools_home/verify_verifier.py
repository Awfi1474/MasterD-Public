#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·验验证器 verify_verifier.py（照老三「验证器不是神·它也会错·要验验证器」）
★ 缘起：老七的 verify_any.py 用普通POST打消息流SSE接口 → 误判我streaming
   → 今天照老三判据去核尺·查出他的bug
★ 治法：对外部拿来的验证器/尺·先做「三验」
   ① 源码读法对不对（打SSE的接口·有没有按SSE读）
   ② 结论有没有留反证口（会不会一口咬死）
   ③ 它的判据和官方原文对不对得上（两处核）
判据：「别人的尺 ≠ 真理｜用前先验尺｜验不出错才敢用」
用法: verify_verifier.py <脚本路径或URL>
"""
import sys, os, urllib.request, re

SSE_SIGNS = ("text/event-stream", "data: ", "SSE", "stream")
JSON_READS = ("json.loads", ".get(\"error\")", ".get('error')", "urllib.request.urlopen")

def check(path):
    src = ""
    if path.startswith("http"):
        src = urllib.request.urlopen(path, timeout=15).read().decode("utf-8", "ignore")
    else:
        src = open(path, encoding="utf-8", errors="ignore").read()

    print("★ 验验证器: %s" % path[:60])
    print("  行数: %d" % len(src.splitlines()))
    print("-" * 55)

    # ① 读法: 会不会用JSON读SSE
    risk = []
    lines = src.splitlines()
    for i, l in enumerate(lines, 1):
        if "message/stream" in l or "stream" in l.lower():
            # 往后看10行·有没有 json.loads 读这个返回
            window = "\n".join(lines[i-1:i+12])
            if any(k in window for k in JSON_READS) and not any(k in window for k in ("event-stream", "iter_lines", "data: ")):
                risk.append((i, l.strip()[:80]))
    if risk:
        print("  ① 读法风险: 🔴 疑似用 JSON 读流式接口")
        for i, l in risk[:3]: print("     L%d: %s" % (i, l))
    else:
        print("  ① 读法: ✅ 未发现 JSON 读 SSE")

    # ② 有没有留反证/复核口
    has_hard = any(k in src for k in ("MUST", "必须", "一定", "绝对"))
    has_soft = any(k in src for k in ("可能", "若", "如果", "反证", "待核", "疑似"))
    print("  ② 结论语气: %s（硬=%s 软=%s）" % ("⚠️ 只有硬判" if has_hard and not has_soft else "✅ 有保留", has_hard, has_soft))

    # ③ 有没有引官方行号
    refs = re.findall(r"(L\d{2,}|§[\d\.]+|spec)", src)
    print("  ③ 官方引用: %s" % ("✅ 有 %d 处" % len(refs) if refs else "⚠️ 无行号引用"))

    print("-" * 55)
    print("★ 判据: 别人的尺≠真理｜结论离谱时先验尺")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: verify_verifier.py <脚本路径或URL>")
        sys.exit(1)
    check(sys.argv[1])
